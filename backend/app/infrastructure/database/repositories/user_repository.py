"""
User Repository - PostgreSQL

Repositorio para gestionar usuarios en PostgreSQL.
Proporciona operaciones CRUD y queries especializadas para usuarios.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.infrastructure.database.models.postgres.user import User
from app.core.security import hash_password, verify_password
from app.utils.logger import get_logger

logger = get_logger(__name__)

class UserRepository(BaseRepository[User]):
    """
    Repositorio para usuarios (PostgreSQL).
    
    Gestiona operaciones CRUD y autenticación de usuarios.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializar repositorio.
        
        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
    
    async def create(self, entity: User) -> User:
        """
        Crear un nuevo usuario.
        
        Args:
            entity: Usuario a crear
        
        Returns:
            User: Usuario creado
        
        Example:
            >>> repo = UserRepository(session)
            >>> user = User(
            ...     email="user@example.com",
            ...     username="testuser",
            ...     hashed_password=hash_password("password123")
            ... )
            >>> created = await repo.create(user)
        """
        try:
            self.session.add(entity)
            await self.session.commit()
            await self.session.refresh(entity)
            
            logger.info(f"Usuario creado: {entity.email}")
            return entity
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creando usuario: {e}")
            raise
    
    async def get_by_id(self, id: str) -> Optional[User]:
        """
        Obtener usuario por ID.
        
        Args:
            id: UUID del usuario
        
        Returns:
            User o None
        """
        try:
            stmt = select(User).where(User.id == id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error obteniendo usuario {id}: {e}")
            return None
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[User]:
        """
        Actualizar un usuario.
        
        Args:
            id: UUID del usuario
            data: Datos a actualizar
        
        Returns:
            User actualizado o None
        """
        try:
            # Actualizar updated_at
            data["updated_at"] = datetime.utcnow()
            
            stmt = (
                update(User)
                .where(User.id == id)
                .values(**data)
                .returning(User)
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            user = result.scalar_one_or_none()
            
            if user:
                logger.info(f"Usuario {id} actualizado")
            
            return user
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error actualizando usuario {id}: {e}")
            raise
    
    async def delete(self, id: str) -> bool:
        """
        Eliminar un usuario.
        
        Args:
            id: UUID del usuario
        
        Returns:
            bool: True si se eliminó
        """
        try:
            stmt = delete(User).where(User.id == id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            deleted = result.rowcount > 0
            
            if deleted:
                logger.info(f"Usuario {id} eliminado")
            
            return deleted
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error eliminando usuario {id}: {e}")
            return False
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Listar usuarios con paginación.
        
        Args:
            skip: Registros a saltar
            limit: Máximo de registros
        
        Returns:
            List[User]: Lista de usuarios
        """
        try:
            stmt = select(User).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listando usuarios: {e}")
            return []
    
    # QUERIES ESPECIALIZADAS
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtener usuario por email.
        
        Args:
            email: Email del usuario
        
        Returns:
            User o None
        """
        try:
            stmt = select(User).where(User.email == email)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error obteniendo usuario por email: {e}")
            return None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Obtener usuario por username.
        
        Args:
            username: Username del usuario
        
        Returns:
            User o None
        """
        try:
            stmt = select(User).where(User.username == username)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error obteniendo usuario por username: {e}")
            return None
    
    async def authenticate(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Autenticar usuario.
        
        Args:
            email: Email del usuario
            password: Password en texto plano
        
        Returns:
            User si las credenciales son válidas, None en caso contrario
        
        Example:
            >>> user = await repo.authenticate("user@example.com", "password123")
            >>> if user:
            ...     print("Autenticado")
        """
        try:
            user = await self.get_by_email(email)
            
            if not user:
                logger.warning(f"Intento de login con email no existente: {email}")
                return None
            
            if not user.is_active:
                logger.warning(f"Intento de login con usuario inactivo: {email}")
                return None
            
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Password incorrecta para usuario: {email}")
                return None
            
            logger.info(f"Usuario autenticado: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            return None
    
    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        is_superuser: bool = False
    ) -> User:
        """
        Crear usuario con password hasheada.
        
        Args:
            email: Email del usuario
            username: Username
            password: Password en texto plano
            is_superuser: Si es superusuario
        
        Returns:
            User: Usuario creado
        
        Example:
            >>> user = await repo.create_user(
            ...     email="user@example.com",
            ...     username="testuser",
            ...     password="secure_password"
            ... )
        """
        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            is_superuser=is_superuser,
        )
        
        return await self.create(user)
    
    async def update_password(
        self,
        user_id: str,
        new_password: str
    ) -> bool:
        """
        Actualizar password de usuario.
        
        Args:
            user_id: ID del usuario
            new_password: Nueva password
        
        Returns:
            bool: True si se actualizó
        """
        try:
            hashed = hash_password(new_password)
            
            await self.update(user_id, {"hashed_password": hashed})
            
            logger.info(f"Password actualizada para usuario {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando password: {e}")
            return False
    
    async def deactivate_user(self, user_id: str) -> bool:
        """
        Desactivar usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            bool: True si se desactivó
        """
        try:
            await self.update(user_id, {"is_active": False})
            logger.info(f"Usuario {user_id} desactivado")
            return True
        except Exception as e:
            logger.error(f"Error desactivando usuario: {e}")
            return False
    
    async def activate_user(self, user_id: str) -> bool:
        """
        Activar usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            bool: True si se activó
        """
        try:
            await self.update(user_id, {"is_active": True})
            logger.info(f"Usuario {user_id} activado")
            return True
        except Exception as e:
            logger.error(f"Error activando usuario: {e}")
            return False
    
    async def get_active_users(self, limit: int = 100) -> List[User]:
        """
        Obtener usuarios activos.
        
        Args:
            limit: Máximo de usuarios
        
        Returns:
            List[User]: Usuarios activos
        """
        try:
            stmt = (
                select(User)
                .where(User.is_active == True)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error obteniendo usuarios activos: {e}")
            return []
    
    async def get_superusers(self) -> List[User]:
        """
        Obtener todos los superusuarios.
        
        Returns:
            List[User]: Superusuarios
        """
        try:
            stmt = select(User).where(User.is_superuser == True)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error obteniendo superusuarios: {e}")
            return []
    
    async def search_users(
        self,
        query: str,
        limit: int = 50
    ) -> List[User]:
        """
        Buscar usuarios por email o username.
        
        Args:
            query: Texto a buscar
            limit: Máximo de resultados
        
        Returns:
            List[User]: Usuarios que coinciden
        """
        try:
            search_pattern = f"%{query}%"
            
            stmt = (
                select(User)
                .where(
                    or_(
                        User.email.ilike(search_pattern),
                        User.username.ilike(search_pattern)
                    )
                )
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error buscando usuarios: {e}")
            return []
    
    async def count_users(
        self,
        active_only: bool = False
    ) -> int:
        """
        Contar usuarios.
        
        Args:
            active_only: Solo contar activos
        
        Returns:
            int: Número de usuarios
        """
        try:
            from sqlalchemy import func
            
            stmt = select(func.count(User.id))
            
            if active_only:
                stmt = stmt.where(User.is_active == True)
            
            result = await self.session.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            logger.error(f"Error contando usuarios: {e}")
            return 0
    
    async def email_exists(self, email: str) -> bool:
        """
        Verificar si un email ya existe.
        
        Args:
            email: Email a verificar
        
        Returns:
            bool: True si existe
        """
        user = await self.get_by_email(email)
        return user is not None
    
    async def username_exists(self, username: str) -> bool:
        """
        Verificar si un username ya existe.
        
        Args:
            username: Username a verificar
        
        Returns:
            bool: True si existe
        """
        user = await self.get_by_username(username)
        return user is not None