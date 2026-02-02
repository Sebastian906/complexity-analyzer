"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade database schema."""
    
    # Crear tabla users
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    
    # Crear tabla sessions
    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('token', sa.String(500), unique=True, nullable=False, index=True),
        sa.Column('refresh_token', sa.String(500), unique=True, nullable=True, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('device_info', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revocation_reason', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Crear ENUMs para audit_logs
    audit_event_type_enum = ENUM(
        'login', 'logout', 'login_failed', 'password_changed', 'password_reset',
        'user_created', 'user_updated', 'user_deleted', 'user_activated', 'user_deactivated',
        'algorithm_created', 'algorithm_updated', 'algorithm_deleted', 'algorithm_analyzed',
        'analysis_started', 'analysis_completed', 'analysis_failed',
        'export_generated', 'export_downloaded',
        'system_started', 'system_stopped', 'database_migration', 'configuration_changed',
        'unauthorized_access', 'permission_denied', 'api_key_created', 'api_key_revoked',
        'suspicious_activity', 'error_occurred', 'exception_raised',
        name='audit_event_type',
        create_type=True
    )
    
    audit_severity_enum = ENUM(
        'debug', 'info', 'warning', 'error', 'critical',
        name='audit_severity',
        create_type=True
    )
    
    # Crear tabla audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', audit_event_type_enum, nullable=False, index=True),
        sa.Column('severity', audit_severity_enum, nullable=False, index=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True, index=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True, index=True),
        sa.Column('resource_type', sa.String(100), nullable=True, index=True),
        sa.Column('resource_id', sa.String(100), nullable=True, index=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(200), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='SET NULL'),
    )
    
    # Crear índices compuestos
    op.create_index(
        'idx_audit_logs_user_timestamp',
        'audit_logs',
        ['user_id', sa.text('timestamp DESC')]
    )
    
    op.create_index(
        'idx_audit_logs_type_severity_timestamp',
        'audit_logs',
        ['event_type', 'severity', sa.text('timestamp DESC')]
    )
    
    op.create_index(
        'idx_audit_logs_resource',
        'audit_logs',
        ['resource_type', 'resource_id', sa.text('timestamp DESC')]
    )

def downgrade() -> None:
    """Downgrade database schema."""
    
    # Eliminar índices compuestos
    op.drop_index('idx_audit_logs_resource', table_name='audit_logs')
    op.drop_index('idx_audit_logs_type_severity_timestamp', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_timestamp', table_name='audit_logs')
    
    # Eliminar tablas
    op.drop_table('audit_logs')
    op.drop_table('sessions')
    op.drop_table('users')
    
    # Eliminar ENUMs
    op.execute('DROP TYPE IF EXISTS audit_severity')
    op.execute('DROP TYPE IF EXISTS audit_event_type')