"""
Network Monitor - Adaptador del IDS (src/) para la arquitectura hexagonal.

Importa los módulos del IDS original (src/detection_engine, src/traffic_analysis,
src/packet_capture) y los expone a través del puerto BaseIDSPort.
"""

import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.infrastructure.security.base_ids import (
    BaseIDSPort, NetworkThreat, ThreatSeverity, ThreatType,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Scapy (captura real de paquetes) 
try:
    from scapy.all import IP, TCP, sniff  # type: ignore
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    logger.warning("scapy no instalado — IDS en modo simulación (sin captura real)")

# Módulos IDS integrados en ids_core/ 
try:
    from app.infrastructure.security.ids_core import DetectionEngine, TrafficAnalyzer
    IDS_MODULES_AVAILABLE = True
except ImportError as exc:
    IDS_MODULES_AVAILABLE = False
    logger.warning(f"ids_core no disponible: {exc}")

class NetworkMonitor(BaseIDSPort):
    """
    Adaptador concreto del IDS.

    Usa DetectionEngine + TrafficAnalyzer del IDS existente (src/)
    y los expone mediante BaseIDSPort para el resto del sistema.
    """

    def __init__(self):
        self._running          = False
        self._monitor_thread:  Optional[threading.Thread] = None
        self._lock             = threading.Lock()

        self._active_threats:  list[NetworkThreat] = []
        self._threat_history:  deque               = deque(maxlen=1000)
        self._blocked_ips:     set[str]             = set()
        self._threat_counts:   dict                 = defaultdict(int)

        self._threat_ttl       = settings.IDS_THREAT_TTL_SECONDS
        self._max_before_block = settings.IDS_MAX_THREATS_BEFORE_BLOCK

        # Instanciar motores del IDS original
        self._detector: Optional[object] = DetectionEngine() if IDS_MODULES_AVAILABLE else None
        self._analyzer: Optional[object] = (
            TrafficAnalyzer(window_seconds=settings.IDS_WINDOW_SECONDS)
            if IDS_MODULES_AVAILABLE else None
        )

        status_scapy = "✓" if SCAPY_AVAILABLE else "✗ (simulación)"
        status_ids   = "✓" if IDS_MODULES_AVAILABLE else "✗"
        logger.info(f"NetworkMonitor inicializado | scapy={status_scapy} | ids_modules={status_ids}")

    # Ciclo de vida
    def start_monitoring(self, interface: Optional[str] = None) -> None:
        if self._running:
            logger.warning("NetworkMonitor ya está corriendo")
            return

        if not SCAPY_AVAILABLE or not IDS_MODULES_AVAILABLE:
            logger.warning(
                "IDS no puede iniciarse: faltan dependencias "
                f"(scapy={SCAPY_AVAILABLE}, ids_modules={IDS_MODULES_AVAILABLE})"
            )
            return

        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._capture_loop,
            args=(interface or None,),
            daemon=True,
            name="ids-monitor",
        )
        self._monitor_thread.start()
        logger.info(f"IDS iniciado | interfaz: {interface or 'default del sistema'}")

    def stop_monitoring(self) -> None:
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        logger.info("IDS detenido")

    # Consultas públicas
    def get_active_threats(self) -> list[NetworkThreat]:
        self._purge_expired()
        with self._lock:
            return list(self._active_threats)

    def get_threat_summary(self) -> dict:
        self._purge_expired()
        with self._lock:
            return {
                "active_threats":    len(self._active_threats),
                "total_detected":    sum(
                    v for k, v in self._threat_counts.items()
                    if not k.startswith("ip:")
                ),
                "blocked_ips":       len(self._blocked_ips),
                "threats_by_type":   {
                    k: v for k, v in self._threat_counts.items()
                    if not k.startswith("ip:")
                },
                "monitoring_active": self._running,
                "scapy_available":   SCAPY_AVAILABLE,
                "ids_available":     IDS_MODULES_AVAILABLE,
            }

    def is_ip_blocked(self, ip: str) -> bool:
        return ip in self._blocked_ips

    # Internos 
    def _capture_loop(self, interface: Optional[str]) -> None:
        """Hilo de captura. Llama sniff() de Scapy con callback por paquete."""
        sniff_kwargs = dict(
            iface=interface,
            prn=self._process_packet,
            store=False,
            stop_filter=lambda _: not self._running,
        )
        try:
            sniff(**sniff_kwargs)
        except OSError:
            # Layer 2 no disponible (WinPcap/Npcap no instalado) → Layer 3
            try:
                from scapy.config import conf  # type: ignore
                logger.info(
                    "WinPcap/Npcap no detectado — usando captura Layer 3"
                )
                sniff_kwargs["socket"] = conf.L3socket
                sniff(**sniff_kwargs)
            except Exception as exc:
                logger.warning(f"Captura L3 no disponible: {exc}")
                self._running = False
        except Exception as exc:
            logger.error(f"Error en captura de paquetes: {exc}")
            self._running = False

    def _process_packet(self, packet) -> None:
        """Callback ejecutado por Scapy en cada paquete capturado."""
        try:
            # Delegar análisis al TrafficAnalyzer original (src/)
            features = self._analyzer.analyze_packet(packet)
            if not features:
                return

            # Delegar detección al DetectionEngine original (src/)
            raw_threats = self._detector.detect_threats(features)
            for raw in raw_threats:
                threat = self._build_threat(raw, packet)
                self._register_threat(threat)

        except Exception as exc:
            logger.debug(f"Error procesando paquete: {exc}")

    def _build_threat(self, raw: dict, packet) -> NetworkThreat:
        """
        Convierte la detección cruda del DetectionEngine original
        al modelo tipado NetworkThreat del sistema.
        """
        rule       = raw.get("rule", "unknown")
        confidence = float(raw.get("confidence", raw.get("score", 0.5)))

        threat_type = {
            "syn_flood": ThreatType.SYN_FLOOD,
            "port_scan": ThreatType.PORT_SCAN,
            "anomaly":   ThreatType.ANOMALY,
        }.get(rule, ThreatType.UNKNOWN)

        severity = (
            ThreatSeverity.CRITICAL if confidence >= 0.9 else
            ThreatSeverity.HIGH     if confidence >= 0.7 else
            ThreatSeverity.MEDIUM   if confidence >= 0.4 else
            ThreatSeverity.LOW
        )

        # Extraer IPs/puertos del paquete Scapy
        try:
            src_ip   = packet[IP].src
            dst_ip   = packet[IP].dst
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        except Exception:
            src_ip, dst_ip, src_port, dst_port = "unknown", "unknown", None, None

        return NetworkThreat(
            threat_type=     threat_type,
            severity=        severity,
            source_ip=       src_ip,
            destination_ip=  dst_ip,
            source_port=     src_port,
            destination_port=dst_port,
            confidence=      confidence,
            description=     f"Regla '{rule}' | tipo: {raw.get('type', 'unknown')}",
            details=         raw,
        )

    def _register_threat(self, threat: NetworkThreat) -> None:
        with self._lock:
            self._active_threats.append(threat)
            self._threat_history.append(threat)
            self._threat_counts[threat.threat_type.value] += 1

            ip_key = f"ip:{threat.source_ip}"
            self._threat_counts[ip_key] += 1
            if self._threat_counts[ip_key] >= self._max_before_block:
                if threat.source_ip not in self._blocked_ips:
                    self._blocked_ips.add(threat.source_ip)
                    logger.warning(f"IP bloqueada automáticamente: {threat.source_ip}")

        logger.info(
            f"[IDS] {threat.severity.value.upper()} | "
            f"{threat.threat_type.value} | src={threat.source_ip}"
        )

    def _purge_expired(self) -> None:
        cutoff = datetime.utcnow() - timedelta(seconds=self._threat_ttl)
        with self._lock:
            self._active_threats = [
                t for t in self._active_threats if t.timestamp > cutoff
            ]