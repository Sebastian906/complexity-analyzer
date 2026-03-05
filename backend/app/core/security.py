"""
Security Module - Seguridad y Autenticación

Proporciona funciones para:
- Hashing de passwords
- Generación y validación de tokens JWT
- Autenticación y autorización
- Encriptación de datos sensibles
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.utils.logger import get_logger

logger = get_logger(__name__)

# PASSWORD HASHING
# Usar bcrypt directamente (passlib tiene problemas de compatibilidad con Python 3.14+)

def hash_password(password: str) -> str:
    """
    Hash de una contraseña usando bcrypt.
    
    Args:
        password: Contraseña en texto plano
    
    Returns:
        str: Hash de la contraseña
    
    Example:
        >>> hashed = hash_password("mi_password_seguro")
        >>> print(hashed)  # $2b$12$...
    """
    # bcrypt tiene límite de 72 bytes, truncar si es necesario
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar una contraseña contra su hash.
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash almacenado
    
    Returns:
        bool: True si coincide, False en caso contrario
    
    Example:
        >>> hashed = hash_password("mi_password")
        >>> verify_password("mi_password", hashed)  # True
        >>> verify_password("password_incorrecto", hashed)  # False
    """
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Error verificando password: {e}")
        return False

# JWT TOKEN MANAGEMENT
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crear un token JWT de acceso.
    
    Args:
        data: Datos a codificar en el token (típicamente user_id, email, etc.)
        expires_delta: Tiempo de expiración (opcional)
    
    Returns:
        str: Token JWT codificado
    
    Example:
        >>> token = create_access_token(
        ...     data={"sub": "user@example.com", "user_id": "123"}
        ... )
    """
    to_encode = data.copy()
    
    # Calcular tiempo de expiración
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Agregar claim de expiración
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    # Codificar token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crear un token JWT de refresh.
    
    Args:
        data: Datos a codificar
        expires_delta: Tiempo de expiración (opcional, default 7 días)
    
    Returns:
        str: Token JWT codificado
    """
    to_encode = data.copy()
    
    # Tiempo de expiración más largo para refresh tokens
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodificar y validar un token JWT.
    
    Args:
        token: Token JWT a decodificar
    
    Returns:
        Dict: Payload del token
    
    Raises:
        AuthenticationException: Si el token es inválido o expirado
    
    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> payload = decode_token(token)
        >>> print(payload["sub"])  # user@example.com
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Token inválido: {e}")
        raise AuthenticationException("Token inválido o expirado")

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verificar un token y su tipo.
    
    Args:
        token: Token JWT
        token_type: Tipo esperado ("access" o "refresh")
    
    Returns:
        Dict con el payload si es válido, None en caso contrario
    """
    try:
        payload = decode_token(token)
        
        # Verificar tipo de token
        if payload.get("type") != token_type:
            logger.warning(f"Tipo de token incorrecto: esperado {token_type}, recibido {payload.get('type')}")
            return None
        
        return payload
    except AuthenticationException:
        return None

def get_user_from_token(token: str) -> Optional[str]:
    """
    Extraer el identificador de usuario de un token.
    
    Args:
        token: Token JWT
    
    Returns:
        str: User ID/email del token, o None si es inválido
    """
    payload = verify_token(token)
    if not payload:
        return None
    
    # Extraer subject (típicamente email o user_id)
    return payload.get("sub")

# API KEY GENERATION
def generate_api_key(length: int = 32) -> str:
    """
    Generar una API key segura.
    
    Args:
        length: Longitud de la key en bytes (default 32)
    
    Returns:
        str: API key en formato hexadecimal
    
    Example:
        >>> api_key = generate_api_key()
        >>> print(len(api_key))  # 64 (32 bytes * 2 chars hex)
    """
    return secrets.token_hex(length)

def generate_secure_token(length: int = 32) -> str:
    """
    Generar un token seguro para uso general.
    
    Args:
        length: Longitud del token en bytes
    
    Returns:
        str: Token URL-safe
    """
    return secrets.token_urlsafe(length)

# PASSWORD VALIDATION
def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validar la fortaleza de una contraseña.
    
    Reglas:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un carácter especial
    
    Args:
        password: Contraseña a validar
    
    Returns:
        tuple: (es_válida: bool, mensaje_error: str | None)
    
    Example:
        >>> valid, error = validate_password_strength("weak")
        >>> print(valid)  # False
        >>> print(error)  # "La contraseña debe tener al menos 8 caracteres"
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not any(c.isupper() for c in password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not any(c.islower() for c in password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe contener al menos un número"
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "La contraseña debe contener al menos un carácter especial"
    
    return True, None

# DATA ENCRYPTION (simple)
def encrypt_data(data: str, key: Optional[str] = None) -> str:
    """
    Encriptar datos sensibles usando Fernet (cifrado simétrico).
    
    Args:
        data: Datos a encriptar
        key: Clave de encriptación (opcional, usa SECRET_KEY)
    
    Returns:
        str: Datos encriptados en base64
    
    Raises:
        RuntimeError: Si la librería cryptography no está disponible
        ValueError: Si ocurre un error durante la encriptación
    
    Note:
        Usa Fernet de la librería cryptography para encriptación segura.
        La clave debe tener 32 bytes codificados en base64.
    """
    import base64
    import hashlib
    
    from cryptography.fernet import Fernet
    
    # Generar clave Fernet desde SECRET_KEY
    encryption_key = key or settings.SECRET_KEY
    # Fernet requiere una clave de 32 bytes base64-encoded
    # Usamos SHA256 para derivar una clave consistente
    key_bytes = hashlib.sha256(encryption_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    
    fernet = Fernet(fernet_key)
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()

def decrypt_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """
    Desencriptar datos.
    
    Args:
        encrypted_data: Datos encriptados
        key: Clave de desencriptación (opcional)
    
    Returns:
        str: Datos desencriptados
    
    Raises:
        RuntimeError: Si la librería cryptography no está disponible
        ValueError: Si no se pudo desencriptar los datos
    """
    import base64
    import hashlib
    
    from cryptography.fernet import Fernet
    
    # Generar clave Fernet desde SECRET_KEY
    encryption_key = key or settings.SECRET_KEY
    key_bytes = hashlib.sha256(encryption_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    
    fernet = Fernet(fernet_key)
    try:
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error desencriptando datos: {type(e).__name__}")
        raise ValueError("No se pudo desencriptar los datos")

# PERMISSION CHECKING
class PermissionChecker:
    """
    Clase para verificar permisos de usuario.
    
    Útil para implementar RBAC (Role-Based Access Control).
    """
    
    # Definición de roles y sus permisos
    ROLES = {
        "admin": [
            "read:all",
            "write:all",
            "delete:all",
            "manage:users",
        ],
        "user": [
            "read:own",
            "write:own",
        ],
        "guest": [
            "read:public",
        ]
    }
    
    @classmethod
    def has_permission(cls, user_role: str, required_permission: str) -> bool:
        """
        Verificar si un rol tiene un permiso específico.
        
        Args:
            user_role: Rol del usuario
            required_permission: Permiso requerido
        
        Returns:
            bool: True si tiene permiso
        
        Example:
            >>> PermissionChecker.has_permission("admin", "delete:all")  # True
            >>> PermissionChecker.has_permission("user", "delete:all")  # False
        """
        role_permissions = cls.ROLES.get(user_role, [])
        
        # Verificar permiso exacto
        if required_permission in role_permissions:
            return True
        
        # Verificar wildcards (ej: "read:all" cubre "read:own")
        for permission in role_permissions:
            if permission.endswith(":all"):
                action = permission.split(":")[0]
                if required_permission.startswith(f"{action}:"):
                    return True
        
        return False
    
    @classmethod
    def require_permission(cls, required_permission: str):
        """
        Decorador para requerir un permiso específico.
        
        Example:
            >>> @PermissionChecker.require_permission("write:algorithms")
            >>> async def create_algorithm(user_role: str):
            ...     # Solo ejecuta si tiene permiso
            ...     pass
        """
        def decorator(func):
            async def wrapper(*args, user_role: str = "guest", **kwargs):
                if not cls.has_permission(user_role, required_permission):
                    raise AuthenticationException(
                        f"Permiso denegado: se requiere '{required_permission}'"
                    )
                return await func(*args, user_role=user_role, **kwargs)
            return wrapper
        return decorator

# SESSION MANAGEMENT
class SessionManager:
    """
    Gestor de sesiones de usuario.
    
    En producción, debería usar Redis o similar.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        ttl_seconds: int = 3600
    ) -> str:
        """
        Crear una nueva sesión.
        
        Args:
            user_id: ID del usuario
            user_data: Datos adicionales del usuario
            ttl_seconds: Tiempo de vida en segundos
        
        Returns:
            str: Session ID
        """
        session_id = generate_secure_token(32)
        
        self.sessions[session_id] = {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds),
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener datos de una sesión.
        
        Args:
            session_id: ID de la sesión
        
        Returns:
            Dict con datos de la sesión o None si no existe/expiró
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # Verificar expiración
        if datetime.utcnow() > session["expires_at"]:
            self.delete_session(session_id)
            return None
        
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """
        Eliminar una sesión.
        
        Args:
            session_id: ID de la sesión
        
        Returns:
            bool: True si se eliminó
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Limpiar sesiones expiradas"""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self.sessions.items()
            if now > session["expires_at"]
        ]
        
        for sid in expired:
            del self.sessions[sid]
        
        logger.info(f"Limpiadas {len(expired)} sesiones expiradas")

# Singleton del gestor de sesiones
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """Obtener instancia singleton del gestor de sesiones"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

# SECURITY UTILITIES
def sanitize_filename(filename: str) -> str:
    """
    Sanitizar nombre de archivo para prevenir path traversal.
    
    Args:
        filename: Nombre de archivo a sanitizar
    
    Returns:
        str: Nombre de archivo seguro
    """
    import re
    
    # Remover path separators
    filename = filename.replace("/", "_").replace("\\", "_")
    
    # Remover caracteres peligrosos
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Limitar longitud
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename

def is_safe_redirect_url(url: str, allowed_hosts: list[str]) -> bool:
    """
    Verificar si una URL de redirección es segura.
    
    Args:
        url: URL a verificar
        allowed_hosts: Lista de hosts permitidos
    
    Returns:
        bool: True si es segura
    """
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    
    # URLs relativas son seguras
    if not parsed.netloc:
        return True
    
    # Verificar contra whitelist
    return parsed.netloc in allowed_hosts