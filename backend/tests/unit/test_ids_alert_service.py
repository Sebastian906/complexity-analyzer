"""
Tests unitarios — IDSAlertService (distribución de alertas).

Verifica que:
  • _log_threat enruta al nivel de log correcto según severity
  • handle_threat incrementa el contador
  • Con use_mongodb=False no intenta persistir
  • Con use_mongodb=True llama a _persist_to_mongodb
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from app.infrastructure.security.ids_alert_service import IDSAlertService
from app.infrastructure.security.base_ids import (
    NetworkThreat,
    ThreatSeverity,
    ThreatType,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_threat(severity=ThreatSeverity.HIGH):
    return NetworkThreat(
        threat_type=ThreatType.SYN_FLOOD,
        severity=severity,
        source_ip="10.0.0.1",
        destination_ip="10.0.0.2",
        confidence=0.9,
        description="test alert",
    )


@pytest.fixture
def alert_service():
    return IDSAlertService(use_mongodb=False)


@pytest.fixture
def alert_service_mongo():
    return IDSAlertService(use_mongodb=True)


# ── Conteo de alertas ────────────────────────────────────────────────────────

class TestAlertCount:
    @pytest.mark.asyncio
    async def test_count_increments(self, alert_service):
        assert alert_service.alert_count == 0
        await alert_service.handle_threat(_make_threat())
        assert alert_service.alert_count == 1
        await alert_service.handle_threat(_make_threat())
        assert alert_service.alert_count == 2


# ── Logging por severity ─────────────────────────────────────────────────────

class TestLogRouting:
    @patch("app.infrastructure.security.ids_alert_service.logger")
    def test_critical_uses_critical_log(self, mock_logger):
        svc = IDSAlertService(use_mongodb=False)
        svc._log_threat(_make_threat(ThreatSeverity.CRITICAL))
        mock_logger.critical.assert_called_once()

    @patch("app.infrastructure.security.ids_alert_service.logger")
    def test_high_uses_error_log(self, mock_logger):
        svc = IDSAlertService(use_mongodb=False)
        svc._log_threat(_make_threat(ThreatSeverity.HIGH))
        mock_logger.error.assert_called_once()

    @patch("app.infrastructure.security.ids_alert_service.logger")
    def test_medium_uses_warning_log(self, mock_logger):
        svc = IDSAlertService(use_mongodb=False)
        svc._log_threat(_make_threat(ThreatSeverity.MEDIUM))
        mock_logger.warning.assert_called_once()

    @patch("app.infrastructure.security.ids_alert_service.logger")
    def test_low_uses_info_log(self, mock_logger):
        svc = IDSAlertService(use_mongodb=False)
        svc._log_threat(_make_threat(ThreatSeverity.LOW))
        mock_logger.info.assert_called_once()


# ── MongoDB persistence ──────────────────────────────────────────────────────

class TestMongoPersistence:
    @pytest.mark.asyncio
    async def test_no_persist_when_disabled(self, alert_service):
        """Con use_mongodb=False no se persiste."""
        with patch.object(alert_service, "_persist_to_mongodb", new_callable=AsyncMock) as m:
            await alert_service.handle_threat(_make_threat())
            m.assert_not_called()

    @pytest.mark.asyncio
    async def test_persist_called_when_enabled(self, alert_service_mongo):
        """Con use_mongodb=True se llama _persist_to_mongodb."""
        with patch.object(alert_service_mongo, "_persist_to_mongodb", new_callable=AsyncMock) as m:
            await alert_service_mongo.handle_threat(_make_threat())
            m.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_failure_does_not_raise(self, alert_service_mongo):
        """Si MongoDB falla, handle_threat no propaga la excepción."""
        with patch(
            "app.infrastructure.database.mongodb_client.get_mongodb_client",
            side_effect=Exception("MongoDB down"),
        ):
            # No debería lanzar excepción (el try/except interno la captura)
            await alert_service_mongo.handle_threat(_make_threat())
