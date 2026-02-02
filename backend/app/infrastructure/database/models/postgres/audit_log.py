"""
Audit Log Model - PostgreSQL

Modelo para registrar eventos de auditoría del sistema.
Permite tracking de todas las acciones importantes para compliance,
debugging y análisis de comportamiento.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from enum import Enum

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ENUM

from app.infrastructure.database.models.postgres.base import Base, TimestampMixin
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ENUMS
class AuditEventType(str, Enum):
    """Tipos de eventos de auditoría"""
    # Autenticación
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    
    # Usuarios
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    
    # Algoritmos
    ALGORITHM_CREATED = "algorithm_created"
    ALGORITHM_UPDATED = "algorithm_updated"
    ALGORITHM_DELETED = "algorithm_deleted"
    ALGORITHM_ANALYZED = "algorithm_analyzed"
    
    # Análisis
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    
    # Exportación
    EXPORT_GENERATED = "export_generated"
    EXPORT_DOWNLOADED = "export_downloaded"
    
    # Sistema
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    DATABASE_MIGRATION = "database_migration"
    CONFIGURATION_CHANGED = "configuration_changed"
    
    # Seguridad
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # Errores
    ERROR_OCCURRED = "error_occurred"
    EXCEPTION_RAISED = "exception_raised"

class AuditSeverity(str, Enum):
    """Niveles de severidad de eventos"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# AUDIT LOG MODEL
class AuditLog(Base, TimestampMixin):
    """
    Modelo de registro de auditoría.
    
    Registra todos los eventos importantes del sistema para:
    - Compliance y regulaciones
    - Debugging y troubleshooting
    - Análisis de seguridad
    - Métricas y estadísticas
    
    Attributes:
        id: UUID único del evento
        event_type: Tipo de evento
        severity: Nivel de severidad
        user_id: Usuario que causó el evento (opcional)
        session_id: Sesión asociada (opcional)
        ip_address: IP de origen
        user_agent: User agent
        resource_type: Tipo de recurso afectado
        resource_id: ID del recurso afectado
        action: Acción realizada
        details: Detalles adicionales (JSON)
        error_message: Mensaje de error (si aplica)
        request_id: ID de la request HTTP
        duration_ms: Duración de la operación
    """
    
    __tablename__ = "audit_logs"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Event Information
    event_type = Column(
        ENUM(AuditEventType, name="audit_event_type", create_type=True),
        nullable=False,
        index=True
    )
    
    severity = Column(
        ENUM(AuditSeverity, name="audit_severity", create_type=True),
        nullable=False,
        default=AuditSeverity.INFO,
        index=True
    )
    
    # User Context (opcional - eventos del sistema no tienen user)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Request Context
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Resource Information
    resource_type = Column(String(100), nullable=True, index=True)  # 'algorithm', 'user', etc.
    resource_id = Column(String(100), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # 'create', 'update', 'delete', etc.
    
    # Event Details
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True, default=dict)  # Datos adicionales estructurados
    
    # Error Information (si aplica)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(200), nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # Performance
    duration_ms = Column(Integer, nullable=True)  # Duración de la operación
    
    # Metadata adicional
    # Nota: 'metadata' es un nombre reservado en SQLAlchemy Declarative API
    audit_metadata = Column(JSON, nullable=True, default=dict)
    
    # Timestamp ya viene de TimestampMixin (created_at)
    # Pero podemos agregar timestamp explícito para el evento
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, type={self.event_type.value}, "
            f"severity={self.severity.value}, timestamp={self.timestamp})>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización"""
        return {
            "id": str(self.id),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": str(self.session_id) if self.session_id else None,
            "ip_address": self.ip_address,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "description": self.description,
            "details": self.details,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def log_event(
        cls,
        event_type: AuditEventType,
        action: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> 'AuditLog':
        """
        Crear y retornar un registro de auditoría.
        
        Args:
            event_type: Tipo de evento
            action: Acción realizada
            severity: Nivel de severidad
            ... (otros parámetros opcionales)
        
        Returns:
            AuditLog: Instancia del registro creado
        
        Example:
            >>> log = AuditLog.log_event(
            ...     event_type=AuditEventType.ALGORITHM_CREATED,
            ...     action="create",
            ...     resource_type="algorithm",
            ...     resource_id="123",
            ...     details={"name": "quicksort"}
            ... )
        """
        return cls(
            event_type=event_type,
            action=action,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=details or {},
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            duration_ms=duration_ms,
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
        )

# SECURITY AUDIT MODEL (Especializado)
class SecurityAudit(Base, TimestampMixin):
    """
    Modelo especializado para eventos de seguridad.
    
    Registra eventos críticos de seguridad con mayor detalle.
    """
    
    __tablename__ = "security_audits"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Event info
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # User context
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Network info
    ip_address = Column(String(45), nullable=False, index=True)
    country_code = Column(String(2), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Attack details
    attack_type = Column(String(100), nullable=True)
    threat_level = Column(String(20), nullable=True)  # low, medium, high, critical
    
    # Response
    action_taken = Column(String(200), nullable=True)
    blocked = Column(Integer, default=0)  # 0=allowed, 1=blocked
    
    # Details
    details = Column(JSON, nullable=True)
    
    # Timestamp
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<SecurityAudit(type={self.event_type}, ip={self.ip_address})>"

# PERFORMANCE METRICS LOG
class PerformanceLog(Base, TimestampMixin):
    """
    Modelo para métricas de performance.
    
    Registra tiempos de ejecución y uso de recursos para
    análisis de performance.
    """
    
    __tablename__ = "performance_logs"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Operation info
    operation = Column(String(200), nullable=False, index=True)
    endpoint = Column(String(200), nullable=True, index=True)
    method = Column(String(10), nullable=True)  # GET, POST, etc.
    
    # Performance metrics
    duration_ms = Column(Integer, nullable=False)
    memory_used_mb = Column(Integer, nullable=True)
    cpu_percent = Column(Integer, nullable=True)
    
    # Request info
    request_id = Column(String(100), nullable=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Status
    status_code = Column(Integer, nullable=True)
    success = Column(Integer, default=1)  # 0=failed, 1=success
    
    # Additional data
    details = Column(JSON, nullable=True)
    
    # Timestamp
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<PerformanceLog(op={self.operation}, duration={self.duration_ms}ms)>"

# INDEXES

# Índices compuestos para queries comunes
Index(
    'idx_audit_logs_user_timestamp',
    AuditLog.user_id,
    AuditLog.timestamp.desc()
)

Index(
    'idx_audit_logs_type_severity_timestamp',
    AuditLog.event_type,
    AuditLog.severity,
    AuditLog.timestamp.desc()
)

Index(
    'idx_audit_logs_resource',
    AuditLog.resource_type,
    AuditLog.resource_id,
    AuditLog.timestamp.desc()
)

Index(
    'idx_security_audits_ip_timestamp',
    SecurityAudit.ip_address,
    SecurityAudit.timestamp.desc()
)

Index(
    'idx_performance_logs_operation_timestamp',
    PerformanceLog.operation,
    PerformanceLog.timestamp.desc()
)