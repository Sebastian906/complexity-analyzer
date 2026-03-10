"""
IDS Core - Módulos del sistema de detección de intrusiones.

Contiene los componentes originales del IDS integrados dentro
del complexity-analyzer como submódulo de infraestructura.

Módulos:
    - detection_engine: Motor de detección (firmas + anomalías)
    - traffic_analysis: Análisis de tráfico de red
    - packet_capture:   Captura de paquetes con Scapy
"""

from app.infrastructure.security.ids_core.detection_engine import DetectionEngine
from app.infrastructure.security.ids_core.traffic_analysis import TrafficAnalyzer
from app.infrastructure.security.ids_core.packet_capture import PacketCapture

__all__ = [
    "DetectionEngine",
    "TrafficAnalyzer",
    "PacketCapture",
]