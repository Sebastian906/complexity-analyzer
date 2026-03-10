"""
Tests unitarios — base_ids.py (NetworkThreat, ThreatType, ThreatSeverity, BaseIDSPort).

Verifica que:
  • Los enums contienen los valores esperados
  • NetworkThreat se construye correctamente y to_dict() funciona
  • BaseIDSPort es abstracta y no se puede instanciar directamente
"""

import pytest
from datetime import datetime

from app.infrastructure.security.base_ids import (
    BaseIDSPort,
    NetworkThreat,
    ThreatSeverity,
    ThreatType,
)


# ── Enums ─────────────────────────────────────────────────────────────────────

class TestThreatType:
    def test_values(self):
        assert ThreatType.SYN_FLOOD.value == "syn_flood"
        assert ThreatType.PORT_SCAN.value == "port_scan"
        assert ThreatType.ANOMALY.value == "anomaly"
        assert ThreatType.UNKNOWN.value == "unknown"

    def test_is_str_enum(self):
        assert isinstance(ThreatType.SYN_FLOOD, str)


class TestThreatSeverity:
    def test_values(self):
        assert ThreatSeverity.LOW.value == "low"
        assert ThreatSeverity.MEDIUM.value == "medium"
        assert ThreatSeverity.HIGH.value == "high"
        assert ThreatSeverity.CRITICAL.value == "critical"

    def test_is_str_enum(self):
        assert isinstance(ThreatSeverity.CRITICAL, str)


# ── NetworkThreat ─────────────────────────────────────────────────────────────

class TestNetworkThreat:
    @pytest.fixture
    def sample_threat(self):
        return NetworkThreat(
            threat_type=ThreatType.SYN_FLOOD,
            severity=ThreatSeverity.HIGH,
            source_ip="192.168.1.100",
            destination_ip="10.0.0.1",
            confidence=0.95,
            description="SYN flood detectado",
            source_port=12345,
            destination_port=80,
            details={"rule": "syn_flood"},
        )

    def test_creation(self, sample_threat):
        assert sample_threat.threat_type == ThreatType.SYN_FLOOD
        assert sample_threat.severity == ThreatSeverity.HIGH
        assert sample_threat.source_ip == "192.168.1.100"
        assert sample_threat.destination_ip == "10.0.0.1"
        assert sample_threat.confidence == 0.95
        assert sample_threat.source_port == 12345
        assert sample_threat.destination_port == 80

    def test_defaults(self):
        threat = NetworkThreat(
            threat_type=ThreatType.UNKNOWN,
            severity=ThreatSeverity.LOW,
            source_ip="0.0.0.0",
            destination_ip="0.0.0.0",
            confidence=0.0,
            description="test",
        )
        assert isinstance(threat.timestamp, datetime)
        assert threat.details == {}
        assert threat.source_port is None
        assert threat.destination_port is None

    def test_to_dict(self, sample_threat):
        d = sample_threat.to_dict()
        assert d["threat_type"] == "syn_flood"
        assert d["severity"] == "high"
        assert d["source_ip"] == "192.168.1.100"
        assert d["destination_ip"] == "10.0.0.1"
        assert d["confidence"] == 0.95
        assert d["source_port"] == 12345
        assert d["destination_port"] == 80
        assert "timestamp" in d
        assert d["details"] == {"rule": "syn_flood"}

    def test_to_dict_timestamp_iso_format(self, sample_threat):
        d = sample_threat.to_dict()
        # Debe poder parsearse de vuelta
        datetime.fromisoformat(d["timestamp"])


# ── BaseIDSPort (abstracta) ──────────────────────────────────────────────────

class TestBaseIDSPort:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseIDSPort()  # type: ignore[abstract]

    def test_concrete_subclass_works(self):
        """Una subclase que implemente todos los métodos es instanciable."""

        class StubIDS(BaseIDSPort):
            def start_monitoring(self, interface=None):
                pass

            def stop_monitoring(self):
                pass

            def get_active_threats(self):
                return []

            def get_threat_summary(self):
                return {}

            def is_ip_blocked(self, ip):
                return False

        ids = StubIDS()
        assert ids.get_active_threats() == []
        assert ids.get_threat_summary() == {}
        assert ids.is_ip_blocked("1.2.3.4") is False
