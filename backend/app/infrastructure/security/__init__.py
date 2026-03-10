"""
Security Infrastructure - IDS de Red

Adaptador que integra el IDS original (src/) con la arquitectura hexagonal.
"""

from app.infrastructure.security.base_ids import (
    BaseIDSPort,
    NetworkThreat,
    ThreatType,
    ThreatSeverity,
)
from app.infrastructure.security.network_monitor import NetworkMonitor
from app.infrastructure.security.ids_alert_service import IDSAlertService

__all__ = [
    "BaseIDSPort",
    "NetworkMonitor",
    "IDSAlertService",
    "NetworkThreat",
    "ThreatType",
    "ThreatSeverity",
]