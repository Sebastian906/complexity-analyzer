"""
Tests unitarios — DetectionEngine (firmas + anomalías con IsolationForest).

Verifica que el motor de detección:
  • Detecta SYN flood cuando dest_syn_count >= 5
  • Detecta port scan  cuando unique_dst_ports >= 4
  • NO dispara falsos positivos con tráfico normal
  • Entrena el modelo de anomalías y genera alertas
  • Maneja datos vacíos y condiciones de borde
"""

import sys
from unittest.mock import MagicMock

import pytest
import numpy as np

# Mock scapy antes de importar módulos IDS que lo requieren transitivamente
if "scapy" not in sys.modules:
    _scapy_mock = MagicMock()
    sys.modules["scapy"] = _scapy_mock
    sys.modules["scapy.all"] = _scapy_mock

from app.infrastructure.security.ids_core.detection_engine.engine import DetectionEngine


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    """Motor de detección fresco (sin entrenar)."""
    return DetectionEngine(contamination=0.1, random_state=42)


@pytest.fixture
def trained_engine():
    """Motor entrenado con tráfico "normal" para detección de anomalías."""
    eng = DetectionEngine(contamination=0.1, random_state=42)
    # 50 muestras de tráfico normal: packet_size ~500, packet_rate ~10, byte_rate ~5000
    rng = np.random.default_rng(0)
    normal = np.column_stack([
        rng.normal(500, 50, 50),   # packet_size
        rng.normal(10, 2, 50),     # packet_rate
        rng.normal(5000, 500, 50), # byte_rate
    ])
    eng.train_anomaly_detector(normal)
    return eng


# ── Signature: SYN Flood ─────────────────────────────────────────────────────

class TestSYNFloodDetection:
    def test_detects_syn_flood(self, engine):
        features = {"dest_syn_count": 5, "unique_dst_ports": 0}
        threats = engine.detect_threats(features)
        rules = [t["rule"] for t in threats if t["type"] == "signature"]
        assert "syn_flood" in rules

    def test_detects_syn_flood_high_count(self, engine):
        features = {"dest_syn_count": 100, "unique_dst_ports": 0}
        threats = engine.detect_threats(features)
        assert any(t["rule"] == "syn_flood" for t in threats)

    def test_no_syn_flood_below_threshold(self, engine):
        features = {"dest_syn_count": 4, "unique_dst_ports": 0}
        threats = engine.detect_threats(features)
        assert not any(t.get("rule") == "syn_flood" for t in threats)


# ── Signature: Port Scan ──────────────────────────────────────────────────────

class TestPortScanDetection:
    def test_detects_port_scan(self, engine):
        features = {"unique_dst_ports": 4, "dest_syn_count": 0}
        threats = engine.detect_threats(features)
        rules = [t["rule"] for t in threats if t["type"] == "signature"]
        assert "port_scan" in rules

    def test_detects_port_scan_high_count(self, engine):
        features = {"unique_dst_ports": 50, "dest_syn_count": 0}
        threats = engine.detect_threats(features)
        assert any(t["rule"] == "port_scan" for t in threats)

    def test_no_port_scan_below_threshold(self, engine):
        features = {"unique_dst_ports": 3, "dest_syn_count": 0}
        threats = engine.detect_threats(features)
        assert not any(t.get("rule") == "port_scan" for t in threats)


# ── Combinaciones de firmas ───────────────────────────────────────────────────

class TestCombinedSignatures:
    def test_both_rules_triggered(self, engine):
        features = {"dest_syn_count": 10, "unique_dst_ports": 10}
        threats = engine.detect_threats(features)
        rules = {t["rule"] for t in threats if t["type"] == "signature"}
        assert rules == {"syn_flood", "port_scan"}

    def test_normal_traffic_no_signature(self, engine):
        features = {"dest_syn_count": 0, "unique_dst_ports": 1, "packet_size": 200}
        threats = engine.detect_threats(features)
        assert threats == []

    def test_confidence_is_one_for_signatures(self, engine):
        features = {"dest_syn_count": 5}
        threats = engine.detect_threats(features)
        for t in threats:
            if t["type"] == "signature":
                assert t["confidence"] == 1.0


# ── Anomaly Detection ─────────────────────────────────────────────────────────

class TestAnomalyDetection:
    def test_not_trained_no_anomaly(self, engine):
        """Sin entrenar el modelo, no debe reportar anomalías."""
        features = {"packet_size": 999999, "packet_rate": 999999, "byte_rate": 999999}
        threats = engine.detect_threats(features)
        assert not any(t["type"] == "anomaly" for t in threats)

    def test_trained_flag(self, engine, trained_engine):
        assert engine.trained is False
        assert trained_engine.trained is True

    def test_anomaly_with_extreme_values(self, trained_engine):
        """Valores extremos deben generar alerta de anomalía."""
        features = {
            "packet_size": 999999,
            "packet_rate": 999999,
            "byte_rate": 999999,
            "dest_syn_count": 0,
            "unique_dst_ports": 0,
        }
        threats = trained_engine.detect_threats(features)
        anomalies = [t for t in threats if t["type"] == "anomaly"]
        assert len(anomalies) >= 1
        assert "score" in anomalies[0]
        assert 0 <= anomalies[0]["confidence"] <= 1.0

    def test_normal_traffic_no_anomaly(self, trained_engine):
        """Tráfico dentro de la distribución normal no dispara anomalía."""
        features = {
            "packet_size": 500,
            "packet_rate": 10,
            "byte_rate": 5000,
            "dest_syn_count": 0,
            "unique_dst_ports": 1,
        }
        threats = trained_engine.detect_threats(features)
        assert not any(t["type"] == "anomaly" for t in threats)


# ── Training Edge Cases ───────────────────────────────────────────────────────

class TestTrainingEdgeCases:
    def test_train_with_empty_data_raises(self, engine):
        with pytest.raises(ValueError, match="empty"):
            engine.train_anomaly_detector([])

    def test_train_with_single_sample(self, engine):
        """Una sola muestra no debería lanzar error (sklearn lo permite)."""
        engine.train_anomaly_detector([[100, 10, 1000]])
        assert engine.trained is True

    def test_train_with_list_of_lists(self, engine):
        data = [[100, 10, 500], [200, 20, 1000], [150, 15, 750]]
        engine.train_anomaly_detector(data)
        assert engine.trained is True

    def test_retrain_does_not_break(self, trained_engine):
        """Re-entrenamiento con nuevos datos funciona."""
        rng = np.random.default_rng(99)
        new_data = rng.normal(100, 10, (20, 3))
        trained_engine.train_anomaly_detector(new_data)
        assert trained_engine.trained is True


# ── Misc / Robustez ───────────────────────────────────────────────────────────

class TestDetectionEngineRobustness:
    def test_empty_features(self, engine):
        threats = engine.detect_threats({})
        assert threats == []

    def test_features_with_extra_keys(self, engine):
        features = {"dest_syn_count": 10, "random_key": "abc", "unique_dst_ports": 0}
        threats = engine.detect_threats(features)
        assert any(t["rule"] == "syn_flood" for t in threats)

    def test_default_contamination_and_state(self):
        eng = DetectionEngine()
        assert eng.anomaly_detector.contamination == 0.1
        assert eng.anomaly_detector.random_state == 42

    def test_custom_contamination(self):
        eng = DetectionEngine(contamination=0.05, random_state=123)
        assert eng.anomaly_detector.contamination == 0.05
        assert eng.anomaly_detector.random_state == 123
