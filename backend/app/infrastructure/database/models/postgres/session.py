"""
Session Model - PostgreSQL

Modelo para gestión de sesiones de usuario en PostgreSQL.
Almacena información de sesiones activas, tokens y metadata.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid

from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.postgres.base import Base, TimestampMixin
from app.utils.logger import get_logger

logger = get_logger(__name__)

# SESSION MODEL
class Session(Base, TimestampMixin):
    """
    Modelo de sesión de usuario.
    
    Almacena sesiones activas con tokens, metadata y expiración.
    Útil para tracking de usuarios logueados y revocación de tokens.
    
    Attributes:
        id: UUID único de la sesión
        user_id: ID del usuario (FK a users)
        token: Token JWT de la sesión (único)
        refresh_token: Token de refresh (único)
        ip_address: IP desde donde se creó la sesión
        user_agent: User agent del navegador/cliente
        is_active: Si la sesión está activa
        expires_at: Fecha/hora de expiración
        last_activity: Última actividad registrada
        metadata: Datos adicionales (JSON)
    """
    
    __tablename__ = "sessions"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign Key a User
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Tokens
    token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=True, index=True)
    
    # Session Info
    ip_address = Column(String(45), nullable=True)  # IPv6 puede ser largo
    user_agent = Column(String(500), nullable=True)
    device_info = Column(String(200), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    expires_at = Column(DateTime, nullable=False, index=True)
    last_activity = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Metadata adicional (JSON)
    metadata = Column(JSON, nullable=True, default=dict)
    
    # Revocation info
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(200), nullable=True)
    
    # Relationship con User
    # user = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return (
            f"<Session(id={self.id}, user_id={self.user_id}, "
            f"active={self.is_active}, expires={self.expires_at})>"
        )
    
    @property
    def is_expired(self) -> bool:
        """Verificar si la sesión ha expirado"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Verificar si la sesión es válida (activa y no expirada)"""
        return self.is_active and not self.is_expired
    
    def revoke(self, reason: Optional[str] = None) -> None:
        """
        Revocar la sesión.
        
        Args:
            reason: Razón de la revocación (opcional)
        """
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason
        logger.info(f"Sesión {self.id} revocada: {reason}")
    
    def extend_expiration(self, hours: int = 24) -> None:
        """
        Extender la expiración de la sesión.
        
        Args:
            hours: Horas a extender (default 24)
        """
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        logger.debug(f"Sesión {self.id} extendida hasta {self.expires_at}")
    
    def update_activity(self) -> None:
        """Actualizar timestamp de última actividad"""
        self.last_activity = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario (sin información sensible)"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "ip_address": self.ip_address,
            "device_info": self.device_info,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "expires_at": self.expires_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

# SESSION TOKEN MODEL (Alternativa más granular)
class SessionToken(Base, TimestampMixin):
    """
    Modelo de token individual (alternativa granular).
    
    Permite tener múltiples tokens por sesión (web, mobile, etc.)
    y control más fino de revocación.
    """
    
    __tablename__ = "session_tokens"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign Key a Session
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Token info
    token = Column(String(500), unique=True, nullable=False, index=True)
    token_type = Column(String(20), nullable=False)  # 'access' o 'refresh'
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Usage tracking
    times_used = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Revocation
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(200), nullable=True)
    
    # Relationship
    # session = relationship("Session", back_populates="tokens")
    
    def __repr__(self) -> str:
        return (
            f"<SessionToken(id={self.id}, type={self.token_type}, "
            f"active={self.is_active})>"
        )
    
    @property
    def is_expired(self) -> bool:
        """Verificar si el token ha expirado"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Verificar si el token es válido"""
        return self.is_active and not self.is_expired
    
    def use(self) -> None:
        """Registrar uso del token"""
        self.times_used += 1
        self.last_used_at = datetime.utcnow()
    
    def revoke(self, reason: Optional[str] = None) -> None:
        """Revocar el token"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason

# REFRESH TOKEN MODEL
class RefreshToken(Base, TimestampMixin):
    """
    Modelo específico para refresh tokens.
    
    Almacena tokens de refresh con mayor tiempo de vida
    y permite rotación de tokens.
    """
    
    __tablename__ = "refresh_tokens"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign Key a User
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Token
    token = Column(String(500), unique=True, nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Token rotation
    replaced_by = Column(
        UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Verificar si ha expirado"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Verificar si es válido"""
        return self.is_active and not self.is_revoked and not self.is_expired
    
    def use(self) -> None:
        """Marcar como usado"""
        self.used_at = datetime.utcnow()
    
    def revoke(self) -> None:
        """Revocar el token"""
        self.is_active = False
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()

# INDEXES Y CONSTRAINTS

# Indexes adicionales se pueden definir aquí si es necesario
# Por ejemplo, índices compuestos para queries comunes:

"""
CREATE INDEX idx_sessions_user_active ON sessions(user_id, is_active);
CREATE INDEX idx_sessions_expires_active ON sessions(expires_at, is_active);
CREATE INDEX idx_tokens_session_type ON session_tokens(session_id, token_type);
"""