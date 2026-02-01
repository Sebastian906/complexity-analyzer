"""
File Utils - Utilidades para Manejo de Archivos

Proporciona funciones para:
- Lectura/escritura de archivos
- Operaciones con paths
- Gestión de directorios
- Validación de archivos
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Union, BinaryIO, TextIO
import json
import yaml

from app.utils.logger import get_logger

logger = get_logger(__name__)

# LECTURA DE ARCHIVOS
def read_file(filepath: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """
    Leer archivo de texto completo.
    
    Args:
        filepath: Ruta del archivo
        encoding: Codificación (default: utf-8)
    
    Returns:
        str: Contenido del archivo o None si falla
    
    Example:
        >>> content = read_file("algorithm.txt")
    """
    try:
        path = Path(filepath)
        return path.read_text(encoding=encoding)
    except Exception as e:
        logger.error(f"Error leyendo archivo {filepath}: {e}")
        return None

def read_lines(
    filepath: Union[str, Path],
    encoding: str = 'utf-8',
    strip: bool = True
) -> List[str]:
    """
    Leer archivo línea por línea.
    
    Args:
        filepath: Ruta del archivo
        encoding: Codificación
        strip: Si se debe hacer strip de cada línea
    
    Returns:
        List[str]: Líneas del archivo
    """
    try:
        path = Path(filepath)
        lines = path.read_text(encoding=encoding).splitlines()
        
        if strip:
            lines = [line.strip() for line in lines]
        
        return lines
    except Exception as e:
        logger.error(f"Error leyendo líneas de {filepath}: {e}")
        return []

def read_json(filepath: Union[str, Path]) -> Optional[dict]:
    """
    Leer archivo JSON.
    
    Args:
        filepath: Ruta del archivo JSON
    
    Returns:
        dict: Contenido deserializado o None
    """
    try:
        path = Path(filepath)
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error leyendo JSON {filepath}: {e}")
        return None

def read_yaml(filepath: Union[str, Path]) -> Optional[dict]:
    """
    Leer archivo YAML.
    
    Args:
        filepath: Ruta del archivo YAML
    
    Returns:
        dict: Contenido deserializado o None
    """
    try:
        path = Path(filepath)
        with path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error leyendo YAML {filepath}: {e}")
        return None

def read_binary(filepath: Union[str, Path]) -> Optional[bytes]:
    """
    Leer archivo binario.
    
    Args:
        filepath: Ruta del archivo
    
    Returns:
        bytes: Contenido binario o None
    """
    try:
        path = Path(filepath)
        return path.read_bytes()
    except Exception as e:
        logger.error(f"Error leyendo archivo binario {filepath}: {e}")
        return None

# ESCRITURA DE ARCHIVOS
def write_file(
    filepath: Union[str, Path],
    content: str,
    encoding: str = 'utf-8',
    create_dirs: bool = True
) -> bool:
    """
    Escribir contenido a archivo de texto.
    
    Args:
        filepath: Ruta del archivo
        content: Contenido a escribir
        encoding: Codificación
        create_dirs: Si se deben crear directorios padre
    
    Returns:
        bool: True si fue exitoso
    
    Example:
        >>> write_file("output/result.txt", "Hello World")
    """
    try:
        path = Path(filepath)
        
        # Crear directorios si no existen
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_text(content, encoding=encoding)
        logger.debug(f"Archivo escrito: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error escribiendo archivo {filepath}: {e}")
        return False

def write_lines(
    filepath: Union[str, Path],
    lines: List[str],
    encoding: str = 'utf-8',
    create_dirs: bool = True
) -> bool:
    """
    Escribir líneas a archivo.
    
    Args:
        filepath: Ruta del archivo
        lines: Lista de líneas
        encoding: Codificación
        create_dirs: Si se deben crear directorios
    
    Returns:
        bool: True si fue exitoso
    """
    content = '\n'.join(lines)
    return write_file(filepath, content, encoding, create_dirs)

def write_json(
    filepath: Union[str, Path],
    data: dict,
    indent: int = 2,
    create_dirs: bool = True
) -> bool:
    """
    Escribir datos a archivo JSON.
    
    Args:
        filepath: Ruta del archivo
        data: Datos a serializar
        indent: Indentación
        create_dirs: Si se deben crear directorios
    
    Returns:
        bool: True si fue exitoso
    """
    try:
        path = Path(filepath)
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        with path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        logger.debug(f"JSON escrito: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error escribiendo JSON {filepath}: {e}")
        return False

def write_yaml(
    filepath: Union[str, Path],
    data: dict,
    create_dirs: bool = True
) -> bool:
    """
    Escribir datos a archivo YAML.
    
    Args:
        filepath: Ruta del archivo
        data: Datos a serializar
        create_dirs: Si se deben crear directorios
    
    Returns:
        bool: True si fue exitoso
    """
    try:
        path = Path(filepath)
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        with path.open('w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        
        logger.debug(f"YAML escrito: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error escribiendo YAML {filepath}: {e}")
        return False

def write_binary(
    filepath: Union[str, Path],
    content: bytes,
    create_dirs: bool = True
) -> bool:
    """
    Escribir contenido binario a archivo.
    
    Args:
        filepath: Ruta del archivo
        content: Contenido binario
        create_dirs: Si se deben crear directorios
    
    Returns:
        bool: True si fue exitoso
    """
    try:
        path = Path(filepath)
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_bytes(content)
        logger.debug(f"Archivo binario escrito: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error escribiendo archivo binario {filepath}: {e}")
        return False

# OPERACIONES CON ARCHIVOS
def copy_file(
    source: Union[str, Path],
    destination: Union[str, Path],
    create_dirs: bool = True
) -> bool:
    """
    Copiar archivo.
    
    Args:
        source: Archivo origen
        destination: Archivo destino
        create_dirs: Si se deben crear directorios destino
    
    Returns:
        bool: True si fue exitoso
    """
    try:
        src = Path(source)
        dst = Path(destination)
        
        if create_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(src, dst)
        logger.debug(f"Archivo copiado: {source} -> {destination}")
        return True
    except Exception as e:
        logger.error(f"Error copiando archivo: {e}")
        return False

def move_file(
    source: Union[str, Path],
    destination: Union[str, Path],
    create_dirs: bool = True
) -> bool:
    """
    Mover archivo.
    
    Args:
        source: Archivo origen
        destination: Archivo destino
        create_dirs: Si se deben crear directorios destino
    
    Returns:
        bool: True si fue exitoso
    """
    try:
        src = Path(source)
        dst = Path(destination)
        
        if create_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(src), str(dst))
        logger.debug(f"Archivo movido: {source} -> {destination}")
        return True
    except Exception as e:
        logger.error(f"Error moviendo archivo: {e}")
        return False

def delete_file(filepath: Union[str, Path]) -> bool:
    """
    Eliminar archivo.
    
    Args:
        filepath: Ruta del archivo
    
    Returns:
        bool: True si fue exitoso
    """
    try:
        path = Path(filepath)
        if path.exists():
            path.unlink()
            logger.debug(f"Archivo eliminado: {filepath}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error eliminando archivo {filepath}: {e}")
        return False

# OPERACIONES CON DIRECTORIOS
def create_directory(dirpath: Union[str, Path], parents: bool = True) -> bool:
    """
    Crear directorio.
    
    Args:
        dirpath: Ruta del directorio
        parents: Si se deben crear directorios padre
    
    Returns:
        bool: True si fue exitoso
    """
    try:
        path = Path(dirpath)
        path.mkdir(parents=parents, exist_ok=True)
        logger.debug(f"Directorio creado: {dirpath}")
        return True
    except Exception as e:
        logger.error(f"Error creando directorio {dirpath}: {e}")
        return False

def delete_directory(
    dirpath: Union[str, Path],
    recursive: bool = False
) -> bool:
    """
    Eliminar directorio.
    
    Args:
        dirpath: Ruta del directorio
        recursive: Si se debe eliminar recursivamente
    
    Returns:
        bool: True si fue exitoso
    """
    try:
        path = Path(dirpath)
        if path.exists():
            if recursive:
                shutil.rmtree(path)
            else:
                path.rmdir()
            logger.debug(f"Directorio eliminado: {dirpath}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error eliminando directorio {dirpath}: {e}")
        return False

def list_files(
    dirpath: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    Listar archivos en directorio.
    
    Args:
        dirpath: Ruta del directorio
        pattern: Patrón de archivos (ej: "*.txt")
        recursive: Si se debe buscar recursivamente
    
    Returns:
        List[Path]: Lista de archivos encontrados
    
    Example:
        >>> files = list_files("data", "*.json")
    """
    try:
        path = Path(dirpath)
        
        if recursive:
            return list(path.rglob(pattern))
        else:
            return list(path.glob(pattern))
    except Exception as e:
        logger.error(f"Error listando archivos en {dirpath}: {e}")
        return []

def list_directories(dirpath: Union[str, Path]) -> List[Path]:
    """
    Listar subdirectorios.
    
    Args:
        dirpath: Ruta del directorio
    
    Returns:
        List[Path]: Lista de subdirectorios
    """
    try:
        path = Path(dirpath)
        return [p for p in path.iterdir() if p.is_dir()]
    except Exception as e:
        logger.error(f"Error listando directorios en {dirpath}: {e}")
        return []

# INFORMACIÓN DE ARCHIVOS
def get_file_size(filepath: Union[str, Path]) -> int:
    """
    Obtener tamaño de archivo en bytes.
    
    Args:
        filepath: Ruta del archivo
    
    Returns:
        int: Tamaño en bytes
    """
    try:
        return Path(filepath).stat().st_size
    except Exception as e:
        logger.error(f"Error obteniendo tamaño de {filepath}: {e}")
        return 0

def get_file_extension(filepath: Union[str, Path]) -> str:
    """
    Obtener extensión de archivo.
    
    Args:
        filepath: Ruta del archivo
    
    Returns:
        str: Extensión (sin punto)
    """
    return Path(filepath).suffix.lstrip('.')

def get_filename_without_extension(filepath: Union[str, Path]) -> str:
    """
    Obtener nombre de archivo sin extensión.
    
    Args:
        filepath: Ruta del archivo
    
    Returns:
        str: Nombre sin extensión
    """
    return Path(filepath).stem

def file_exists(filepath: Union[str, Path]) -> bool:
    """
    Verificar si archivo existe.
    
    Args:
        filepath: Ruta del archivo
    
    Returns:
        bool: True si existe
    """
    return Path(filepath).exists() and Path(filepath).is_file()

def directory_exists(dirpath: Union[str, Path]) -> bool:
    """
    Verificar si directorio existe.
    
    Args:
        dirpath: Ruta del directorio
    
    Returns:
        bool: True si existe
    """
    return Path(dirpath).exists() and Path(dirpath).is_dir()

def is_empty_directory(dirpath: Union[str, Path]) -> bool:
    """
    Verificar si directorio está vacío.
    
    Args:
        dirpath: Ruta del directorio
    
    Returns:
        bool: True si está vacío
    """
    try:
        path = Path(dirpath)
        return path.is_dir() and not any(path.iterdir())
    except Exception:
        return False

# PATHS
def get_absolute_path(filepath: Union[str, Path]) -> Path:
    """
    Obtener path absoluto.
    
    Args:
        filepath: Ruta del archivo
    
    Returns:
        Path: Path absoluto
    """
    return Path(filepath).resolve()

def get_relative_path(
    filepath: Union[str, Path],
    base: Union[str, Path]
) -> Path:
    """
    Obtener path relativo respecto a una base.
    
    Args:
        filepath: Ruta del archivo
        base: Ruta base
    
    Returns:
        Path: Path relativo
    """
    return Path(filepath).relative_to(base)

def join_paths(*parts: Union[str, Path]) -> Path:
    """
    Unir partes de path.
    
    Args:
        *parts: Partes del path
    
    Returns:
        Path: Path unido
    
    Example:
        >>> join_paths("data", "exports", "file.pdf")
        Path('data/exports/file.pdf')
    """
    return Path(*parts)

def ensure_directory(dirpath: Union[str, Path]) -> Path:
    """
    Asegurar que un directorio existe (crear si no existe).
    
    Args:
        dirpath: Ruta del directorio
    
    Returns:
        Path: Path del directorio
    """
    path = Path(dirpath)
    path.mkdir(parents=True, exist_ok=True)
    return path

# LIMPIEZA
def clean_directory(
    dirpath: Union[str, Path],
    pattern: str = "*",
    keep_subdirs: bool = True
) -> int:
    """
    Limpiar archivos de un directorio.
    
    Args:
        dirpath: Ruta del directorio
        pattern: Patrón de archivos a eliminar
        keep_subdirs: Si se deben mantener subdirectorios
    
    Returns:
        int: Número de archivos eliminados
    """
    try:
        count = 0
        path = Path(dirpath)
        
        for item in path.glob(pattern):
            if item.is_file():
                item.unlink()
                count += 1
            elif item.is_dir() and not keep_subdirs:
                shutil.rmtree(item)
                count += 1
        
        logger.info(f"Directorio limpiado: {dirpath} ({count} items eliminados)")
        return count
    except Exception as e:
        logger.error(f"Error limpiando directorio {dirpath}: {e}")
        return 0

def get_directory_size(dirpath: Union[str, Path]) -> int:
    """
    Obtener tamaño total de un directorio.
    
    Args:
        dirpath: Ruta del directorio
    
    Returns:
        int: Tamaño en bytes
    """
    total = 0
    try:
        for item in Path(dirpath).rglob('*'):
            if item.is_file():
                total += item.stat().st_size
        return total
    except Exception as e:
        logger.error(f"Error calculando tamaño de {dirpath}: {e}")
        return 0