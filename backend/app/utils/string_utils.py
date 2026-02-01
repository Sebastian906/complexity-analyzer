"""
String Utils - Utilidades para Manipulación de Strings

Proporciona funciones para:
- Formateo y limpieza de strings
- Truncado y padding
- Búsqueda y reemplazo
- Validación y conversión
"""

import re
import unicodedata
from typing import List, Optional, Union, Pattern

# LIMPIEZA Y NORMALIZACIÓN
def clean_whitespace(text: str) -> str:
    """
    Limpiar espacios en blanco múltiples.
    
    Args:
        text: Texto a limpiar
    
    Returns:
        str: Texto con espacios normalizados
    
    Example:
        >>> clean_whitespace("hello    world")
        'hello world'
    """
    return ' '.join(text.split())

def remove_extra_newlines(text: str) -> str:
    """
    Remover líneas vacías múltiples.
    
    Args:
        text: Texto a limpiar
    
    Returns:
        str: Texto sin líneas vacías múltiples
    """
    return re.sub(r'\n\s*\n', '\n\n', text)

def strip_html_tags(text: str) -> str:
    """
    Remover tags HTML de un texto.
    
    Args:
        text: Texto con HTML
    
    Returns:
        str: Texto sin HTML
    
    Example:
        >>> strip_html_tags("<p>Hello <b>World</b></p>")
        'Hello World'
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def normalize_unicode(text: str, form: str = 'NFKC') -> str:
    """
    Normalizar caracteres Unicode.
    
    Args:
        text: Texto a normalizar
        form: Forma de normalización (NFC, NFD, NFKC, NFKD)
    
    Returns:
        str: Texto normalizado
    """
    return unicodedata.normalize(form, text)

def remove_accents(text: str) -> str:
    """
    Remover acentos de caracteres.
    
    Args:
        text: Texto con acentos
    
    Returns:
        str: Texto sin acentos
    
    Example:
        >>> remove_accents("café")
        'cafe'
    """
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

def remove_punctuation(text: str, keep: str = '') -> str:
    """
    Remover puntuación de texto.
    
    Args:
        text: Texto con puntuación
        keep: Caracteres de puntuación a mantener
    
    Returns:
        str: Texto sin puntuación
    
    Example:
        >>> remove_punctuation("Hello, World!")
        'Hello World'
    """
    import string
    
    punctuation = ''.join(c for c in string.punctuation if c not in keep)
    translator = str.maketrans('', '', punctuation)
    return text.translate(translator)

def remove_special_chars(text: str, keep: str = '') -> str:
    """
    Remover caracteres especiales (dejar solo alfanuméricos).
    
    Args:
        text: Texto con caracteres especiales
        keep: Caracteres especiales a mantener
    
    Returns:
        str: Texto limpio
    """
    pattern = f'[^a-zA-Z0-9\\s{re.escape(keep)}]'
    return re.sub(pattern, '', text)

# TRUNCADO Y PADDING
def truncate(
    text: str,
    max_length: int,
    suffix: str = '...',
    whole_words: bool = False
) -> str:
    """
    Truncar texto a longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar
        whole_words: Si se debe truncar en palabras completas
    
    Returns:
        str: Texto truncado
    
    Example:
        >>> truncate("Hello World", 8)
        'Hello...'
        >>> truncate("Hello World", 8, whole_words=True)
        'Hello...'
    """
    if len(text) <= max_length:
        return text
    
    truncated_length = max_length - len(suffix)
    
    if whole_words:
        # Truncar en palabra completa
        words = text[:truncated_length].split()
        if words:
            words.pop()  # Remover última palabra (puede estar cortada)
        return ' '.join(words) + suffix
    else:
        return text[:truncated_length] + suffix

def pad_left(text: str, length: int, char: str = ' ') -> str:
    """
    Agregar padding a la izquierda.
    
    Args:
        text: Texto
        length: Longitud total deseada
        char: Carácter de padding
    
    Returns:
        str: Texto con padding
    
    Example:
        >>> pad_left("42", 5, '0')
        '00042'
    """
    return text.rjust(length, char)

def pad_right(text: str, length: int, char: str = ' ') -> str:
    """
    Agregar padding a la derecha.
    
    Args:
        text: Texto
        length: Longitud total deseada
        char: Carácter de padding
    
    Returns:
        str: Texto con padding
    """
    return text.ljust(length, char)

def pad_center(text: str, length: int, char: str = ' ') -> str:
    """
    Centrar texto con padding.
    
    Args:
        text: Texto
        length: Longitud total deseada
        char: Carácter de padding
    
    Returns:
        str: Texto centrado
    """
    return text.center(length, char)

# TRANSFORMACIONES
def to_title_case(text: str) -> str:
    """
    Convertir a Title Case.
    
    Args:
        text: Texto a convertir
    
    Returns:
        str: Texto en Title Case
    
    Example:
        >>> to_title_case("hello world")
        'Hello World'
    """
    return text.title()

def to_sentence_case(text: str) -> str:
    """
    Convertir a Sentence case (primera letra mayúscula).
    
    Args:
        text: Texto a convertir
    
    Returns:
        str: Texto en Sentence case
    
    Example:
        >>> to_sentence_case("hello world")
        'Hello world'
    """
    return text[0].upper() + text[1:].lower() if text else text

def reverse_string(text: str) -> str:
    """
    Invertir string.
    
    Args:
        text: Texto a invertir
    
    Returns:
        str: Texto invertido
    
    Example:
        >>> reverse_string("hello")
        'olleh'
    """
    return text[::-1]

def swap_case(text: str) -> str:
    """
    Intercambiar mayúsculas y minúsculas.
    
    Args:
        text: Texto
    
    Returns:
        str: Texto con caso intercambiado
    
    Example:
        >>> swap_case("Hello World")
        'hELLO wORLD'
    """
    return text.swapcase()

# BÚSQUEDA Y REEMPLAZO
def count_occurrences(text: str, substring: str, case_sensitive: bool = True) -> int:
    """
    Contar ocurrencias de substring.
    
    Args:
        text: Texto donde buscar
        substring: Substring a contar
        case_sensitive: Si es sensible a mayúsculas
    
    Returns:
        int: Número de ocurrencias
    """
    if not case_sensitive:
        text = text.lower()
        substring = substring.lower()
    
    return text.count(substring)

def replace_multiple(
    text: str,
    replacements: dict,
    case_sensitive: bool = True
) -> str:
    """
    Reemplazar múltiples strings.
    
    Args:
        text: Texto original
        replacements: Dict con {buscar: reemplazar}
        case_sensitive: Si es sensible a mayúsculas
    
    Returns:
        str: Texto con reemplazos
    
    Example:
        >>> replace_multiple("Hello World", {"Hello": "Hi", "World": "Earth"})
        'Hi Earth'
    """
    for old, new in replacements.items():
        if case_sensitive:
            text = text.replace(old, new)
        else:
            text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
    
    return text

def extract_numbers(text: str) -> List[Union[int, float]]:
    """
    Extraer todos los números de un texto.
    
    Args:
        text: Texto con números
    
    Returns:
        List: Números encontrados
    
    Example:
        >>> extract_numbers("I have 2 apples and 3.5 oranges")
        [2, 3.5]
    """
    # Patrón para números enteros y decimales
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        if '.' in match:
            numbers.append(float(match))
        else:
            numbers.append(int(match))
    
    return numbers

def extract_words(text: str, min_length: int = 1) -> List[str]:
    """
    Extraer palabras de un texto.
    
    Args:
        text: Texto
        min_length: Longitud mínima de palabra
    
    Returns:
        List[str]: Palabras encontradas
    """
    words = re.findall(r'\b\w+\b', text)
    return [word for word in words if len(word) >= min_length]

def extract_emails(text: str) -> List[str]:
    """
    Extraer direcciones de email de un texto.
    
    Args:
        text: Texto con emails
    
    Returns:
        List[str]: Emails encontrados
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)

def extract_urls(text: str) -> List[str]:
    """
    Extraer URLs de un texto.
    
    Args:
        text: Texto con URLs
    
    Returns:
        List[str]: URLs encontradas
    """
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(pattern, text)

# VALIDACIÓN
def is_alphanumeric(text: str) -> bool:
    """
    Verificar si texto es alfanumérico.
    
    Args:
        text: Texto a verificar
    
    Returns:
        bool: True si es alfanumérico
    """
    return text.isalnum()

def is_alphabetic(text: str) -> bool:
    """
    Verificar si texto contiene solo letras.
    
    Args:
        text: Texto a verificar
    
    Returns:
        bool: True si solo contiene letras
    """
    return text.isalpha()

def is_numeric(text: str) -> bool:
    """
    Verificar si texto es numérico.
    
    Args:
        text: Texto a verificar
    
    Returns:
        bool: True si es numérico
    """
    return text.isdigit()

def contains_only(text: str, allowed_chars: str) -> bool:
    """
    Verificar si texto contiene solo caracteres permitidos.
    
    Args:
        text: Texto a verificar
        allowed_chars: Caracteres permitidos
    
    Returns:
        bool: True si solo contiene caracteres permitidos
    """
    return all(char in allowed_chars for char in text)

def starts_with_any(text: str, prefixes: List[str]) -> bool:
    """
    Verificar si texto empieza con alguno de los prefijos.
    
    Args:
        text: Texto a verificar
        prefixes: Lista de prefijos
    
    Returns:
        bool: True si empieza con algún prefijo
    """
    return any(text.startswith(prefix) for prefix in prefixes)

def ends_with_any(text: str, suffixes: List[str]) -> bool:
    """
    Verificar si texto termina con alguno de los sufijos.
    
    Args:
        text: Texto a verificar
        suffixes: Lista de sufijos
    
    Returns:
        bool: True si termina con algún sufijo
    """
    return any(text.endswith(suffix) for suffix in suffixes)

# FORMATEO
def indent_text(text: str, spaces: int = 4, char: str = ' ') -> str:
    """
    Indentar texto.
    
    Args:
        text: Texto a indentar
        spaces: Número de espacios
        char: Carácter de indentación
    
    Returns:
        str: Texto indentado
    """
    indent = char * spaces
    lines = text.split('\n')
    return '\n'.join(indent + line for line in lines)

def wrap_text(text: str, width: int = 80) -> str:
    """
    Ajustar texto a ancho específico.
    
    Args:
        text: Texto a ajustar
        width: Ancho máximo de línea
    
    Returns:
        str: Texto ajustado
    """
    import textwrap
    return textwrap.fill(text, width=width)

def align_text(
    text: str,
    alignment: str = 'left',
    width: int = 80,
    fill_char: str = ' '
) -> str:
    """
    Alinear texto.
    
    Args:
        text: Texto a alinear
        alignment: Tipo de alineación ('left', 'right', 'center')
        width: Ancho total
        fill_char: Carácter de relleno
    
    Returns:
        str: Texto alineado
    """
    if alignment == 'left':
        return text.ljust(width, fill_char)
    elif alignment == 'right':
        return text.rjust(width, fill_char)
    elif alignment == 'center':
        return text.center(width, fill_char)
    else:
        return text

def add_line_numbers(text: str, start: int = 1, separator: str = ' | ') -> str:
    """
    Agregar números de línea al texto.
    
    Args:
        text: Texto
        start: Número inicial
        separator: Separador entre número y texto
    
    Returns:
        str: Texto con números de línea
    
    Example:
        >>> add_line_numbers("hello\\nworld")
        '1 | hello\\n2 | world'
    """
    lines = text.split('\n')
    max_digits = len(str(start + len(lines) - 1))
    
    numbered_lines = []
    for i, line in enumerate(lines, start=start):
        line_num = str(i).rjust(max_digits)
        numbered_lines.append(f"{line_num}{separator}{line}")
    
    return '\n'.join(numbered_lines)

# CONVERSIÓN
def to_bool(text: str) -> bool:
    """
    Convertir string a booleano.
    
    Args:
        text: Texto a convertir
    
    Returns:
        bool: Valor booleano
    
    Example:
        >>> to_bool("true")
        True
        >>> to_bool("no")
        False
    """
    true_values = {'true', 'yes', '1', 'y', 't', 'on', 'si', 'sí'}
    return text.lower().strip() in true_values

def split_and_strip(text: str, separator: str = ',') -> List[str]:
    """
    Dividir texto y hacer strip de cada parte.
    
    Args:
        text: Texto a dividir
        separator: Separador
    
    Returns:
        List[str]: Partes divididas y limpias
    
    Example:
        >>> split_and_strip("apple, banana , orange")
        ['apple', 'banana', 'orange']
    """
    return [part.strip() for part in text.split(separator) if part.strip()]

def join_with_and(items: List[str], conjunction: str = 'and') -> str:
    """
    Unir lista de items con conjunción.
    
    Args:
        items: Lista de items
        conjunction: Conjunción a usar
    
    Returns:
        str: Items unidos
    
    Example:
        >>> join_with_and(['apple', 'banana', 'orange'])
        'apple, banana and orange'
    """
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f'{items[0]} {conjunction} {items[1]}'
    
    return f"{', '.join(items[:-1])}, {conjunction} {items[-1]}"

# SLUGIFY
def slugify(text: str, separator: str = '-') -> str:
    """
    Convertir texto a slug URL-friendly.
    
    Args:
        text: Texto a convertir
        separator: Separador a usar
    
    Returns:
        str: Slug
    
    Example:
        >>> slugify("Hello World!")
        'hello-world'
    """
    # Convertir a minúsculas y remover acentos
    text = remove_accents(text.lower())
    
    # Reemplazar espacios y caracteres especiales
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', separator, text)
    text = re.sub(f'{separator}+', separator, text)
    
    return text.strip(separator)

def unslugify(slug: str, separator: str = '-') -> str:
    """
    Convertir slug a texto legible.
    
    Args:
        slug: Slug a convertir
        separator: Separador usado
    
    Returns:
        str: Texto legible
    
    Example:
        >>> unslugify("hello-world")
        'Hello World'
    """
    return slug.replace(separator, ' ').title()