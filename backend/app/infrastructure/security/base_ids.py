"""
Base IDS - Puerto de Detección de Intrusiones

Define la interfaz que cualquier implementación de IDS debe cumplir,
siguiendo el patrón Ports & Adapters de la arquitectura hexagonal.
El dominio nunca importa Scapy ni DetectionEngine directamente.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

class ThreatType(str, Enum):
    SYN_FLOOD       = "syn_flood"
    PORT_SCAN       = "port_scan"
    ANOMALY         = "anomaly"
    UNKNOWN         = "unknown"

class ThreatSeverity(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

@dataclass
class NetworkThreat:
    """Representa una amenaza detectada en la red."""
    threat_type:      ThreatType
    severity:         ThreatSeverity
    source_ip:        str
    destination_ip:   str
    confidence:       float
    description:      str
    timestamp:        datetime     = field(default_factory=datetime.utcnow)
    details:          dict         = field(default_factory=dict)
    source_port:      Optional[int] = None
    destination_port: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "threat_type":       self.threat_type.value,
            "severity":          self.severity.value,
            "source_ip":         self.source_ip,
            "destination_ip":    self.destination_ip,
            "confidence":        self.confidence,
            "description":       self.description,
            "timestamp":         self.timestamp.isoformat(),
            "details":           self.details,
            "source_port":       self.source_port,
            "destination_port":  self.destination_port,
        }

class BaseIDSPort(ABC):
    """
    Puerto (interface) para el sistema de detección de intrusiones.
    Cualquier implementación concreta hereda de esta clase.
    """

    @abstractmethod
    def start_monitoring(self, interface: Optional[str] = None) -> None: ...

    @abstractmethod
    def stop_monitoring(self) -> None: ...

    @abstractmethod
    def get_active_threats(self) -> list[NetworkThreat]: ...

    @abstractmethod
    def get_threat_summary(self) -> dict: ...

    @abstractmethod
    def is_ip_blocked(self, ip: str) -> bool: ...