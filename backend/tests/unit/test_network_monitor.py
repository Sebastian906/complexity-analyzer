"""
Tests unitarios — NetworkMonitor (adaptador hexagonal del IDS).

Verifica que:
  • Se instancian correctamente los atributos internos
  • get_active_threats / get_threat_summary / is_ip_blocked funcionan
  • El registro de amenazas actualiza contadores y bloquea IPs
  • La purga de amenazas expiradas funciona
  • start_monitoring / stop_monitoring no lanzan errores
"""

import sys
from unittest.mock import MagicMock

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

# Mock scapy antes de importar módulos IDS
if "scapy" not in sys.modules:
    _scapy_mock = MagicMock()
    sys.modules["scapy"] = _scapy_mock
    sys.modules["scapy.all"] = _scapy_mock

from app.infrastructure.security.base_ids import (
    NetworkThreat,
    ThreatSeverity,
    ThreatType,
)
from app.infrastructure.security.network_monitor import NetworkMonitor


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def monitor():
    """NetworkMonitor fresco."""
    return NetworkMonitor()


def _make_threat(
    threat_type=ThreatType.SYN_FLOOD,
    severity=ThreatSeverity.HIGH,
    source_ip="10.0.0.99",
    timestamp=None,
):
    return NetworkThreat(
        threat_type=threat_type,
        severity=severity,
        source_ip=source_ip,
        destination_ip="10.0.0.1",
        confidence=0.9,
        description="test threat",
        timestamp=timestamp or datetime.utcnow(),
    )


# ── Inicialización ────────────────────────────────────────────────────────────

class TestNetworkMonitorInit:
    def test_initial_state(self, monitor):
        assert monitor._running is False
        assert monitor.get_active_threats() == []
        assert monitor.is_ip_blocked("1.2.3.4") is False

    def test_threat_summary_initial(self, monitor):
        summary = monitor.get_threat_summary()
        assert summary["active_threats"] == 0
        assert summary["total_detected"] == 0
        assert summary["blocked_ips"] == 0
        assert summary["monitoring_active"] is False


# ── Registro de amenazas ──────────────────────────────────────────────────────

class TestThreatRegistration:
    def test_register_threat(self, monitor):
        threat = _make_threat()
        monitor._register_threat(threat)

        active = monitor.get_active_threats()
        assert len(active) == 1
        assert active[0].source_ip == "10.0.0.99"

    def test_register_multiple_threats(self, monitor):
        for i in range(5):
            monitor._register_threat(_make_threat(source_ip=f"10.0.0.{i}"))

        assert len(monitor.get_active_threats()) == 5

    def test_threat_counts(self, monitor):
        monitor._register_threat(_make_threat(threat_type=ThreatType.SYN_FLOOD))
        monitor._register_threat(_make_threat(threat_type=ThreatType.PORT_SCAN))
        monitor._register_threat(_make_threat(threat_type=ThreatType.SYN_FLOOD))

        summary = monitor.get_threat_summary()
        assert summary["threats_by_type"]["syn_flood"] == 2
        assert summary["threats_by_type"]["port_scan"] == 1
        assert summary["total_detected"] == 3


# ── Bloqueo automático de IPs ────────────────────────────────────────────────

class TestIPBlocking:
    def test_ip_blocked_after_threshold(self, monitor):
        """La IP se bloquea tras alcanzar IDS_MAX_THREATS_BEFORE_BLOCK."""
        threshold = monitor._max_before_block
        for _ in range(threshold):
            monitor._register_threat(_make_threat(source_ip="192.168.1.1"))

        assert monitor.is_ip_blocked("192.168.1.1") is True

    def test_ip_not_blocked_below_threshold(self, monitor):
        threshold = monitor._max_before_block
        for _ in range(threshold - 1):
            monitor._register_threat(_make_threat(source_ip="192.168.1.2"))

        assert monitor.is_ip_blocked("192.168.1.2") is False

    def test_different_ips_independent(self, monitor):
        threshold = monitor._max_before_block
        for _ in range(threshold):
            monitor._register_threat(_make_threat(source_ip="192.168.1.10"))

        assert monitor.is_ip_blocked("192.168.1.10") is True
        assert monitor.is_ip_blocked("192.168.1.11") is False


# ── Purga de amenazas expiradas ───────────────────────────────────────────────

class TestThreatPurge:
    def test_expired_threats_removed(self, monitor):
        old_time = datetime.utcnow() - timedelta(seconds=monitor._threat_ttl + 10)
        monitor._register_threat(_make_threat(timestamp=old_time))
        monitor._register_threat(_make_threat())  # reciente

        active = monitor.get_active_threats()
        assert len(active) == 1  # solo la reciente

    def test_all_expired(self, monitor):
        old_time = datetime.utcnow() - timedelta(seconds=monitor._threat_ttl + 10)
        monitor._register_threat(_make_threat(timestamp=old_time))

        assert len(monitor.get_active_threats()) == 0


# ── Ciclo de vida ─────────────────────────────────────────────────────────────

class TestMonitorLifecycle:
    def test_start_without_scapy_does_not_crash(self, monitor):
        """Sin scapy instalado o sin permisos, start_monitoring no lanza error."""
        monitor.start_monitoring(interface="fake0")
        # Si scapy no puede capturar, _running queda False o el hilo termina.
        monitor.stop_monitoring()

    def test_stop_when_not_running(self, monitor):
        monitor.stop_monitoring()  # No debería hacer nada ni lanzar error

    def test_double_start_warning(self, monitor):
        """Llamar start_monitoring dos veces no debería romper nada."""
        monitor._running = True  # simular que ya corre
        monitor.start_monitoring()  # debe loggear warning, no duplicar hilo
        monitor._running = False


# ── Build Threat ──────────────────────────────────────────────────────────────

class TestBuildThreat:
    def test_severity_mapping(self, monitor):
        """Verifica la lógica de mapeo confidence → severity."""
        # Creamos un paquete mock con IP y TCP layers
        mock_packet = MagicMock()
        mock_ip = MagicMock()
        mock_ip.src = "1.1.1.1"
        mock_ip.dst = "2.2.2.2"
        mock_tcp = MagicMock()
        mock_tcp.sport = 1234
        mock_tcp.dport = 80
        mock_packet.__contains__ = lambda self, x: True
        mock_packet.__getitem__ = lambda self, key: mock_ip if key.__name__ == "IP" else mock_tcp

        cases = [
            (0.95, ThreatSeverity.CRITICAL),
            (0.7,  ThreatSeverity.HIGH),
            (0.5,  ThreatSeverity.MEDIUM),
            (0.2,  ThreatSeverity.LOW),
        ]
        for confidence, expected_severity in cases:
            raw = {"rule": "syn_flood", "type": "signature", "confidence": confidence}
            threat = monitor._build_threat(raw, mock_packet)
            assert threat.severity == expected_severity, (
                f"confidence={confidence} → esperado {expected_severity}, obtenido {threat.severity}"
            )
