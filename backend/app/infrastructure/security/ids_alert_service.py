"""
IDS Alert Service - Distribución de alertas del IDS.

Conecta las amenazas detectadas con el sistema de logging del proyecto
y opcionalmente con MongoDB (colección ids_threats).
"""

import json
from datetime import datetime

from app.infrastructure.security.base_ids import NetworkThreat, ThreatSeverity
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class IDSAlertService:
    """
    Recibe NetworkThreat y los enruta a los canales configurados:
      1. Logger estructurado del proyecto (siempre)
      2. MongoDB colección 'ids_threats' (si IDS_PERSIST_TO_MONGODB=true)
    """

    def __init__(self, use_mongodb: bool = False):
        self._use_mongodb  = use_mongodb
        self._alert_count  = 0

    async def handle_threat(self, threat: NetworkThreat) -> None:
        self._alert_count += 1
        self._log_threat(threat)
        if self._use_mongodb:
            await self._persist_to_mongodb(threat)

    def _log_threat(self, threat: NetworkThreat) -> None:
        payload = json.dumps(threat.to_dict(), default=str)
        if threat.severity == ThreatSeverity.CRITICAL:
            logger.critical(f"[IDS] {payload}")
        elif threat.severity == ThreatSeverity.HIGH:
            logger.error(f"[IDS] {payload}")
        elif threat.severity == ThreatSeverity.MEDIUM:
            logger.warning(f"[IDS] {payload}")
        else:
            logger.info(f"[IDS] {payload}")

    async def _persist_to_mongodb(self, threat: NetworkThreat) -> None:
        """
        Persiste la amenaza en MongoDB usando el cliente ya configurado
        en app/infrastructure/database/mongodb_client.py.
        """
        try:
            from app.infrastructure.database.mongodb_client import get_mongodb_client
            client = get_mongodb_client()
            if client and client.is_connected:
                await client.database["ids_threats"].insert_one({
                    **threat.to_dict(),
                    "created_at": datetime.utcnow(),
                })
        except Exception as exc:
            # No detener el flujo principal si MongoDB falla
            logger.debug(f"No se persistió amenaza en MongoDB: {exc}")

    @property
    def alert_count(self) -> int:
        return self._alert_count