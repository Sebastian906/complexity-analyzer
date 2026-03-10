import numpy as np
from sklearn.ensemble import IsolationForest

class DetectionEngine:
    """Combina la detección basada en firmas y anomalías.

    Uso:
    - Llamar a `train_anomaly_detector(normal_traffic_data)` con una matriz 2D de vectores 
    de características de tráfico normal para habilitar la detección de anomalías.
    - Llamar a `detect_threats(features)` para obtener una lista de amenazas detectadas.
    """
    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.anomaly_detector = IsolationForest(
            contamination=contamination,
            random_state=random_state
        )
        self.signature_rules = self.load_signature_rules()
        self.trained = False

    def load_signature_rules(self):
        return {
            'syn_flood': {
                # Use dest_syn_count (SYNs toward destination in window) as primary indicator
                # Raised threshold to reduce false positives in tests/real traffic
                'condition': lambda features: (
                    features.get('dest_syn_count', 0) >= 5
                )
            },
            'port_scan': {
                # Use number of unique destination ports contacted by a source within window
                # Raised threshold to reduce false positives
                'condition': lambda features: (
                    features.get('unique_dst_ports', 0) >= 4
                )
            }
        }

    def train_anomaly_detector(self, normal_traffic_data):
        # normal_traffic_data expected shape: (n_samples, n_features)
        arr = np.asarray(normal_traffic_data, dtype=float)
        if arr.size == 0:
            raise ValueError("Training data is empty")
        self.anomaly_detector.fit(arr)
        self.trained = True

    def detect_threats(self, features):
        threats = []

        # Signature-based detection
        for rule_name, rule in self.signature_rules.items():
            try:
                if rule['condition'](features):
                    threats.append({
                        'type': 'signature',
                        'rule': rule_name,
                        'confidence': 1.0
                    })
            except Exception:
                # Ignore rule errors to avoid breaking detection loop
                continue

        # Anomaly-based detection (only if trained)
        if self.trained:
            try:
                feature_vector = np.array([[
                    features.get('packet_size', 0),
                    features.get('packet_rate', 0),
                    features.get('byte_rate', 0)
                ]], dtype=float)

                anomaly_score = self.anomaly_detector.score_samples(feature_vector)[0]
                # threshold selection is use-case dependent
                if anomaly_score < -0.5:
                    threats.append({
                        'type': 'anomaly',
                        'score': float(anomaly_score),
                        'confidence': float(min(1.0, abs(anomaly_score)))
                    })
            except Exception:
                # If scoring fails, skip anomaly detection
                pass

        return threats
