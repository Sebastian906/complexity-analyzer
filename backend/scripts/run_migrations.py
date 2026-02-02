"""
Script para ejecutar migraciones de Alembic

Ejecuta migraciones de base de datos usando Alembic.

Uso:
    python scripts/run_migrations.py upgrade head
    python scripts/run_migrations.py downgrade -1
    python scripts/run_migrations.py current
    python scripts/run_migrations.py history
"""

import sys
from pathlib import Path
from argparse import ArgumentParser

# Agregar raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from alembic.config import Config
from alembic import command

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def get_alembic_config() -> Config:
    """
    Obtiene configuración de Alembic.
    
    Returns:
        Config: Configuración de Alembic
    """
    # Ruta al archivo alembic.ini
    alembic_cfg = Config(str(root_dir / "alembic.ini"))
    
    # Configurar la URL de la base de datos desde settings
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    return alembic_cfg

def upgrade(revision: str = "head"):
    """
    Ejecuta upgrade de migraciones.
    
    Args:
        revision: Revisión objetivo (default: head)
    """
    logger.info(f"Ejecutando upgrade a: {revision}")
    
    try:
        alembic_cfg = get_alembic_config()
        command.upgrade(alembic_cfg, revision)
        logger.info("✓ Upgrade completado")
    except Exception as e:
        logger.error(f"Error en upgrade: {e}")
        raise

def downgrade(revision: str = "-1"):
    """
    Ejecuta downgrade de migraciones.
    
    Args:
        revision: Revisión objetivo (default: -1)
    """
    logger.info(f"Ejecutando downgrade a: {revision}")
    
    try:
        alembic_cfg = get_alembic_config()
        command.downgrade(alembic_cfg, revision)
        logger.info("✓ Downgrade completado")
    except Exception as e:
        logger.error(f"Error en downgrade: {e}")
        raise

def current():
    """Muestra la revisión actual."""
    logger.info("Obteniendo revisión actual...")
    
    try:
        alembic_cfg = get_alembic_config()
        command.current(alembic_cfg)
    except Exception as e:
        logger.error(f"Error obteniendo revisión actual: {e}")
        raise

def history():
    """Muestra historial de migraciones."""
    logger.info("Historial de migraciones:")
    
    try:
        alembic_cfg = get_alembic_config()
        command.history(alembic_cfg)
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise

def create_migration(message: str, autogenerate: bool = True):
    """
    Crea una nueva migración.
    
    Args:
        message: Mensaje descriptivo de la migración
        autogenerate: Si True, detecta cambios automáticamente
    """
    logger.info(f"Creando migración: {message}")
    
    try:
        alembic_cfg = get_alembic_config()
        command.revision(
            alembic_cfg,
            message=message,
            autogenerate=autogenerate
        )
        logger.info("✓ Migración creada")
    except Exception as e:
        logger.error(f"Error creando migración: {e}")
        raise

def stamp(revision: str = "head"):
    """
    Marca una revisión como aplicada sin ejecutar las migraciones.
    
    Útil cuando las tablas ya existen pero Alembic no tiene registro.
    
    Args:
        revision: Revisión a marcar (default: head)
    """
    logger.info(f"Marcando revisión como aplicada: {revision}")
    
    try:
        alembic_cfg = get_alembic_config()
        command.stamp(alembic_cfg, revision)
        logger.info("✓ Revisión marcada")
    except Exception as e:
        logger.error(f"Error marcando revisión: {e}")
        raise

def main():
    """Función principal."""
    parser = ArgumentParser(description="Gestión de migraciones con Alembic")
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help="Aplicar migraciones")
    upgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Revisión objetivo (default: head)"
    )
    
    # Downgrade
    downgrade_parser = subparsers.add_parser("downgrade", help="Revertir migraciones")
    downgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="-1",
        help="Revisión objetivo (default: -1)"
    )
    
    # Current
    subparsers.add_parser("current", help="Mostrar revisión actual")
    
    # History
    subparsers.add_parser("history", help="Mostrar historial de migraciones")
    
    # Create
    create_parser = subparsers.add_parser("create", help="Crear nueva migración")
    create_parser.add_argument("message", help="Mensaje de la migración")
    create_parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Deshabilitar auto-generación"
    )
    
    # Stamp
    stamp_parser = subparsers.add_parser("stamp", help="Marcar revisión como aplicada sin ejecutar")
    stamp_parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Revisión a marcar (default: head)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    logger.info("GESTIÓN DE MIGRACIONES - ALEMBIC")
    logger.info(f"Entorno: {settings.APP_ENV}")
    logger.info(f"Base de datos: {settings.DATABASE_TYPE}")
    
    try:
        if args.command == "upgrade":
            upgrade(args.revision)
        elif args.command == "downgrade":
            downgrade(args.revision)
        elif args.command == "current":
            current()
        elif args.command == "history":
            history()
        elif args.command == "create":
            create_migration(
                args.message,
                autogenerate=not args.no_autogenerate
            )
        elif args.command == "stamp":
            stamp(args.revision)
        
        logger.info("✓ OPERACIÓN COMPLETADA")
        
    except Exception as e:
        logger.error("✗ ERROR EN OPERACIÓN")
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()