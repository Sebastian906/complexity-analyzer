"""
Validators - Validadores Personalizados

Proporciona funciones de validación para diferentes tipos de datos
usados en el sistema: algoritmos, emails, passwords, etc.
"""

import re
from typing import Optional, List, Tuple, Any
from pathlib import Path

from app.core.constants import SystemLimits
from app.utils.logger import get_logger

logger = get_logger(__name__)

# VALIDADORES DE ALGORITMOS
def validate_algorithm_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validar código de algoritmo.
    
    Verifica:
    - No está vacío
    - Longitud dentro de límites
    - No contiene caracteres peligrosos
    
    Args:
        code: Código del algoritmo
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    
    Example:
        >>> valid, error = validate_algorithm_code("algorithm test(n)...")
        >>> if valid:
        ...     print("Código válido")
    """
    # Verificar que no esté vacío
    if not code or not code.strip():
        return False, "El código del algoritmo no puede estar vacío"
    
    # Verificar longitud
    if len(code) > SystemLimits.MAX_ALGORITHM_LENGTH:
        return False, f"El código excede el límite de {SystemLimits.MAX_ALGORITHM_LENGTH} caracteres"
    
    # Contar líneas
    lines = code.split('\n')
    if len(lines) > SystemLimits.MAX_ALGORITHM_LINES:
        return False, f"El código excede el límite de {SystemLimits.MAX_ALGORITHM_LINES} líneas"
    
    # Verificar caracteres peligrosos (null bytes, etc)
    if '\x00' in code:
        return False, "El código contiene caracteres nulos no permitidos"
    
    return True, None

def validate_algorithm_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validar nombre de algoritmo.
    
    Args:
        name: Nombre del algoritmo
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    # No vacío
    if not name or not name.strip():
        return False, "El nombre no puede estar vacío"
    
    # Longitud entre 3 y 100 caracteres
    if len(name) < 3:
        return False, "El nombre debe tener al menos 3 caracteres"
    
    if len(name) > 100:
        return False, "El nombre no puede exceder 100 caracteres"
    
    # Solo caracteres alfanuméricos, espacios, guiones y underscores
    if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
        return False, "El nombre solo puede contener letras, números, espacios, guiones y underscores"
    
    return True, None

# VALIDADORES DE USUARIO
def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validar formato de email.
    
    Args:
        email: Email a validar
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    
    Example:
        >>> valid, error = validate_email("user@example.com")
        >>> if valid:
        ...     print("Email válido")
    """
    # Patrón básico de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email or not email.strip():
        return False, "El email no puede estar vacío"
    
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    # Verificar longitud
    if len(email) > 255:
        return False, "El email es demasiado largo"
    
    return True, None

def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validar username.
    
    Reglas:
    - 3-30 caracteres
    - Solo letras, números y underscores
    - Debe empezar con letra
    
    Args:
        username: Username a validar
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    if not username or not username.strip():
        return False, "El username no puede estar vacío"
    
    # Longitud
    if len(username) < 3:
        return False, "El username debe tener al menos 3 caracteres"
    
    if len(username) > 30:
        return False, "El username no puede exceder 30 caracteres"
    
    # Patrón: empezar con letra, solo letras, números y underscores
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False, "El username debe empezar con una letra y solo contener letras, números y underscores"
    
    return True, None

def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validar fortaleza de contraseña.
    
    Reglas:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un carácter especial
    
    Args:
        password: Contraseña a validar
    
    Returns:
        Tuple: (es_válida: bool, mensaje_error: str | None)
    """
    if not password:
        return False, "La contraseña no puede estar vacía"
    
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if len(password) > 128:
        return False, "La contraseña es demasiado larga"
    
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

# VALIDADORES DE ARCHIVOS
def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validar nombre de archivo.
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    if not filename or not filename.strip():
        return False, "El nombre de archivo no puede estar vacío"
    
    # Verificar longitud
    if len(filename) > 255:
        return False, "El nombre de archivo es demasiado largo"
    
    # Caracteres prohibidos en nombres de archivo
    forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\x00']
    for char in forbidden_chars:
        if char in filename:
            return False, f"El nombre de archivo contiene el carácter prohibido: {char}"
    
    # No debe empezar o terminar con espacio o punto
    if filename.startswith((' ', '.')):
        return False, "El nombre de archivo no puede empezar con espacio o punto"
    
    if filename.endswith(' '):
        return False, "El nombre de archivo no puede terminar con espacio"
    
    return True, None

def validate_file_extension(
    filename: str,
    allowed_extensions: List[str]
) -> Tuple[bool, Optional[str]]:
    """
    Validar extensión de archivo.
    
    Args:
        filename: Nombre del archivo
        allowed_extensions: Lista de extensiones permitidas (sin punto)
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    
    Example:
        >>> valid, error = validate_file_extension(
        ...     "documento.pdf",
        ...     ["pdf", "docx"]
        ... )
    """
    # Obtener extensión
    path = Path(filename)
    extension = path.suffix.lstrip('.')
    
    if not extension:
        return False, "El archivo no tiene extensión"
    
    if extension.lower() not in [ext.lower() for ext in allowed_extensions]:
        return False, f"Extensión no permitida. Permitidas: {', '.join(allowed_extensions)}"
    
    return True, None

def validate_file_size(
    size_bytes: int,
    max_size_mb: int = 10
) -> Tuple[bool, Optional[str]]:
    """
    Validar tamaño de archivo.
    
    Args:
        size_bytes: Tamaño en bytes
        max_size_mb: Tamaño máximo en MB
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if size_bytes <= 0:
        return False, "El archivo está vacío"
    
    if size_bytes > max_size_bytes:
        return False, f"El archivo excede el tamaño máximo de {max_size_mb}MB"
    
    return True, None

# VALIDADORES DE DATOS
def validate_uuid(uuid_string: str) -> Tuple[bool, Optional[str]]:
    """
    Validar formato UUID.
    
    Args:
        uuid_string: String a validar
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    import uuid
    
    try:
        uuid.UUID(uuid_string)
        return True, None
    except (ValueError, AttributeError):
        return False, "Formato de UUID inválido"

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validar formato de URL.
    
    Args:
        url: URL a validar
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    # Patrón básico de URL
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    
    if not url or not url.strip():
        return False, "La URL no puede estar vacía"
    
    if not re.match(pattern, url, re.IGNORECASE):
        return False, "Formato de URL inválido"
    
    # Verificar longitud
    if len(url) > 2048:
        return False, "La URL es demasiado larga"
    
    return True, None

def validate_json(json_string: str) -> Tuple[bool, Optional[str]]:
    """
    Validar formato JSON.
    
    Args:
        json_string: String JSON a validar
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    import json
    
    try:
        json.loads(json_string)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"JSON inválido: {str(e)}"

def validate_positive_integer(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validar entero positivo.
    
    Args:
        value: Valor a validar
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            return False, "El valor debe ser un entero positivo"
        return True, None
    except (ValueError, TypeError):
        return False, "El valor debe ser un número entero"

def validate_float_range(
    value: Any,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validar que un float esté en un rango.
    
    Args:
        value: Valor a validar
        min_value: Valor mínimo (opcional)
        max_value: Valor máximo (opcional)
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    try:
        float_value = float(value)
        
        if min_value is not None and float_value < min_value:
            return False, f"El valor debe ser mayor o igual a {min_value}"
        
        if max_value is not None and float_value > max_value:
            return False, f"El valor debe ser menor o igual a {max_value}"
        
        return True, None
    except (ValueError, TypeError):
        return False, "El valor debe ser un número"

# VALIDADORES DE COMPLEJIDAD
def validate_complexity_notation(notation: str) -> Tuple[bool, Optional[str]]:
    """
    Validar notación de complejidad.
    
    Args:
        notation: Notación a validar (ej: "O(n)", "Θ(log n)")
    
    Returns:
        Tuple: (es_válida: bool, mensaje_error: str | None)
    """
    if not notation or not notation.strip():
        return False, "La notación no puede estar vacía"
    
    # Patrones válidos de complejidad
    valid_patterns = [
        r'^O\(.+\)$',      # Big O
        r'^Ω\(.+\)$',      # Omega
        r'^Θ\(.+\)$',      # Theta
        r'^o\(.+\)$',      # little o
        r'^ω\(.+\)$',      # little omega
    ]
    
    is_valid = any(re.match(pattern, notation) for pattern in valid_patterns)
    
    if not is_valid:
        return False, "Formato de notación de complejidad inválido"
    
    return True, None

# VALIDADORES DE PAGINACIÓN
def validate_pagination(
    skip: int,
    limit: int,
    max_limit: int = 1000
) -> Tuple[bool, Optional[str]]:
    """
    Validar parámetros de paginación.
    
    Args:
        skip: Registros a saltar
        limit: Límite de registros
        max_limit: Límite máximo permitido
    
    Returns:
        Tuple: (es_válido: bool, mensaje_error: str | None)
    """
    if skip < 0:
        return False, "El parámetro 'skip' no puede ser negativo"
    
    if limit <= 0:
        return False, "El parámetro 'limit' debe ser mayor a 0"
    
    if limit > max_limit:
        return False, f"El parámetro 'limit' no puede exceder {max_limit}"
    
    return True, None

# VALIDADORES COMPUESTOS
def validate_algorithm_input(
    name: str,
    code: str,
    category: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validar input completo de algoritmo.
    
    Args:
        name: Nombre del algoritmo
        code: Código del algoritmo
        category: Categoría (opcional)
    
    Returns:
        Tuple: (es_válido: bool, lista_errores: List[str])
    
    Example:
        >>> valid, errors = validate_algorithm_input(
        ...     name="QuickSort",
        ...     code="algorithm quicksort(A)..."
        ... )
        >>> if not valid:
        ...     print("Errores:", errors)
    """
    errors = []
    
    # Validar nombre
    valid_name, error_name = validate_algorithm_name(name)
    if not valid_name:
        errors.append(f"Nombre: {error_name}")
    
    # Validar código
    valid_code, error_code = validate_algorithm_code(code)
    if not valid_code:
        errors.append(f"Código: {error_code}")
    
    # Validar categoría si se proporciona
    if category:
        if not category.strip():
            errors.append("Categoría: no puede estar vacía")
        elif len(category) > 50:
            errors.append("Categoría: no puede exceder 50 caracteres")
    
    return len(errors) == 0, errors

def validate_user_registration(
    email: str,
    username: str,
    password: str
) -> Tuple[bool, List[str]]:
    """
    Validar datos de registro de usuario.
    
    Args:
        email: Email
        username: Username
        password: Password
    
    Returns:
        Tuple: (es_válido: bool, lista_errores: List[str])
    """
    errors = []
    
    # Validar email
    valid_email, error_email = validate_email(email)
    if not valid_email:
        errors.append(f"Email: {error_email}")
    
    # Validar username
    valid_username, error_username = validate_username(username)
    if not valid_username:
        errors.append(f"Username: {error_username}")
    
    # Validar password
    valid_password, error_password = validate_password(password)
    if not valid_password:
        errors.append(f"Password: {error_password}")
    
    return len(errors) == 0, errors

# SANITIZACIÓN
def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitizar string removiendo caracteres peligrosos.
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima (opcional)
    
    Returns:
        str: Texto sanitizado
    """
    if not text:
        return ""
    
    # Remover null bytes
    text = text.replace('\x00', '')
    
    # Remover caracteres de control excepto newline y tab
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    # Limitar longitud si se especifica
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()