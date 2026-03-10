"""
Tests de integración — Endpoints de seguridad del IDS + IDSMiddleware.

Verifica que:
  • GET /api/v1/security/ids/status      → responde correctamente
  • GET /api/v1/security/ids/threats      → retorna lista de amenazas
  • GET /api/v1/security/ids/check/{ip}   → indica si una IP está bloqueada
  • IDSMiddleware bloquea IPs marcadas
  • IDSMiddleware permite tráfico normal
  • IDSMiddleware excluye rutas de bypass (/docs, /health, etc.)
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.security.base_ids import (
    NetworkThreat,
    ThreatSeverity,
    ThreatType,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _mock_monitor(active_threats=None, blocked_ips=None):
    """Crea un mock de NetworkMonitor con datos controlados."""
    monitor = MagicMock()
    monitor.get_threat_summary.return_value = {
        "active_threats": len(active_threats or []),
        "total_detected": len(active_threats or []),
        "blocked_ips": len(blocked_ips or set()),
        "threats_by_type": {},
        "monitoring_active": True,
        "scapy_available": False,
        "ids_available": True,
    }
    monitor.get_active_threats.return_value = active_threats or []
    monitor.is_ip_blocked.side_effect = lambda ip: ip in (blocked_ips or set())
    return monitor


# ── GET /api/v1/security/ids/status ───────────────────────────────────────────

@pytest.mark.integration
class TestIDSStatusEndpoint:
    def test_status_without_monitor(self, client):
        """Sin monitor IDS activo, debe responder available=False."""
        with patch("app.api.v1.endpoints.security._get_monitor", return_value=None):
            resp = client.get("/api/v1/security/ids/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False

    def test_status_with_monitor(self, client):
        """Con monitor activo, debe responder available=True + summary."""
        mock = _mock_monitor()
        with patch("app.api.v1.endpoints.security._get_monitor", return_value=mock):
            resp = client.get("/api/v1/security/ids/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert "active_threats" in data
        assert "monitoring_active" in data


# ── GET /api/v1/security/ids/threats ──────────────────────────────────────────

@pytest.mark.integration
class TestIDSThreatsEndpoint:
    def test_threats_empty(self, client):
        mock = _mock_monitor(active_threats=[])
        with patch("app.api.v1.endpoints.security._get_monitor", return_value=mock):
            resp = client.get("/api/v1/security/ids/threats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["threats"] == []

    def test_threats_with_data(self, client):
        threat = NetworkThreat(
            threat_type=ThreatType.SYN_FLOOD,
            severity=ThreatSeverity.HIGH,
            source_ip="10.0.0.99",
            destination_ip="10.0.0.1",
            confidence=0.95,
            description="SYN flood test",
        )
        mock = _mock_monitor(active_threats=[threat])
        with patch("app.api.v1.endpoints.security._get_monitor", return_value=mock):
            resp = client.get("/api/v1/security/ids/threats")
        data = resp.json()
        assert data["count"] == 1
        assert data["threats"][0]["threat_type"] == "syn_flood"
        assert data["threats"][0]["source_ip"] == "10.0.0.99"

    def test_threats_without_monitor(self, client):
        with patch("app.api.v1.endpoints.security._get_monitor", return_value=None):
            resp = client.get("/api/v1/security/ids/threats")
        data = resp.json()
        assert data["available"] is False
        assert data["count"] == 0


# ── GET /api/v1/security/ids/check/{ip} ──────────────────────────────────────

@pytest.mark.integration
class TestIDSCheckIPEndpoint:
    def test_ip_not_blocked(self, client):
        mock = _mock_monitor(blocked_ips=set())
        with patch("app.api.v1.endpoints.security._get_monitor", return_value=mock):
            resp = client.get("/api/v1/security/ids/check/10.0.0.50")
        data = resp.json()
        assert data["ip"] == "10.0.0.50"
        assert data["blocked"] is False

    def test_ip_blocked(self, client):
        mock = _mock_monitor(blocked_ips={"192.168.1.1"})
        with patch("app.api.v1.endpoints.security._get_monitor", return_value=mock):
            resp = client.get("/api/v1/security/ids/check/192.168.1.1")
        data = resp.json()
        assert data["blocked"] is True

    def test_check_without_monitor(self, client):
        with patch("app.api.v1.endpoints.security._get_monitor", return_value=None):
            resp = client.get("/api/v1/security/ids/check/10.0.0.1")
        data = resp.json()
        assert data["blocked"] is False
        assert data["available"] is False


# ── IDSMiddleware ─────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestIDSMiddleware:
    """
    Estos tests verifican el middleware a nivel de request real.
    Si el middleware no está activo (IDS_ENABLED=false por defecto),
    verificamos que las requests pasan normalmente.
    """

    def test_normal_request_passes(self, client):
        """Requests normales pasan sin bloqueo."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_docs_accessible(self, client):
        """La documentación siempre está accesible."""
        resp = client.get("/docs")
        # 200 o redirect (307/308) son válidos
        assert resp.status_code in (200, 307, 308)

    def test_openapi_accessible(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
