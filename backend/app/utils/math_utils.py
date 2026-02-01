"""
Math Utils - Utilidades Matemáticas

Proporciona funciones matemáticas útiles para:
- Análisis de complejidad
- Estadísticas
- Cálculos numéricos
- Operaciones con notaciones Big O
"""

import math
from typing import List, Tuple, Optional, Union
from decimal import Decimal, getcontext
from fractions import Fraction

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Configurar precisión decimal
getcontext().prec = 50

# OPERACIONES MATEMÁTICAS BÁSICAS
def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    División segura que evita división por cero.
    
    Args:
        a: Numerador
        b: Denominador
        default: Valor por defecto si b == 0
    
    Returns:
        float: Resultado de a/b o default
    
    Example:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0.0
    """
    try:
        return a / b if b != 0 else default
    except (ZeroDivisionError, TypeError):
        return default

def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Limitar valor a un rango.
    
    Args:
        value: Valor a limitar
        min_value: Valor mínimo
        max_value: Valor máximo
    
    Returns:
        float: Valor limitado
    
    Example:
        >>> clamp(15, 0, 10)
        10
        >>> clamp(-5, 0, 10)
        0
    """
    return max(min_value, min(value, max_value))

def is_power_of_two(n: int) -> bool:
    """
    Verificar si un número es potencia de 2.
    
    Args:
        n: Número a verificar
    
    Returns:
        bool: True si es potencia de 2
    
    Example:
        >>> is_power_of_two(8)
        True
        >>> is_power_of_two(10)
        False
    """
    return n > 0 and (n & (n - 1)) == 0

def next_power_of_two(n: int) -> int:
    """
    Obtener la siguiente potencia de 2.
    
    Args:
        n: Número
    
    Returns:
        int: Siguiente potencia de 2
    
    Example:
        >>> next_power_of_two(10)
        16
    """
    if n <= 1:
        return 1
    
    return 2 ** math.ceil(math.log2(n))

def gcd(a: int, b: int) -> int:
    """
    Máximo común divisor (Euclides).
    
    Args:
        a: Primer número
        b: Segundo número
    
    Returns:
        int: MCD
    """
    while b:
        a, b = b, a % b
    return abs(a)

def lcm(a: int, b: int) -> int:
    """
    Mínimo común múltiplo.
    
    Args:
        a: Primer número
        b: Segundo número
    
    Returns:
        int: MCM
    """
    return abs(a * b) // gcd(a, b) if a and b else 0

# LOGARITMOS Y EXPONENCIALES
def log_base(n: float, base: float) -> float:
    """
    Logaritmo en cualquier base.
    
    Args:
        n: Número
        base: Base del logaritmo
    
    Returns:
        float: log_base(n)
    
    Example:
        >>> log_base(8, 2)
        3.0
    """
    if n <= 0 or base <= 0 or base == 1:
        raise ValueError("Valores inválidos para logaritmo")
    
    return math.log(n) / math.log(base)

def ceiling_log(n: int, base: int = 2) -> int:
    """
    Techo del logaritmo (útil para árboles).
    
    Args:
        n: Número
        base: Base del logaritmo
    
    Returns:
        int: ⌈log_base(n)⌉
    
    Example:
        >>> ceiling_log(9, 2)  # ⌈log₂(9)⌉ = 4
        4
    """
    if n <= 0:
        raise ValueError("n debe ser positivo")
    
    return math.ceil(log_base(n, base))

def floor_log(n: int, base: int = 2) -> int:
    """
    Piso del logaritmo.
    
    Args:
        n: Número
        base: Base del logaritmo
    
    Returns:
        int: ⌊log_base(n)⌋
    """
    if n <= 0:
        raise ValueError("n debe ser positivo")
    
    return math.floor(log_base(n, base))

# FACTORIAL Y COMBINATORIA
def factorial(n: int) -> int:
    """
    Calcular factorial.
    
    Args:
        n: Número
    
    Returns:
        int: n!
    
    Example:
        >>> factorial(5)
        120
    """
    if n < 0:
        raise ValueError("Factorial no definido para negativos")
    
    return math.factorial(n)

def binomial_coefficient(n: int, k: int) -> int:
    """
    Coeficiente binomial C(n, k) = n! / (k! * (n-k)!)
    
    Args:
        n: Total de elementos
        k: Elementos a elegir
    
    Returns:
        int: C(n, k)
    
    Example:
        >>> binomial_coefficient(5, 2)
        10
    """
    if k < 0 or k > n:
        return 0
    
    if k == 0 or k == n:
        return 1
    
    # Optimización: C(n,k) = C(n, n-k)
    k = min(k, n - k)
    
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    
    return result

def permutations(n: int, r: int) -> int:
    """
    Número de permutaciones P(n, r) = n! / (n-r)!
    
    Args:
        n: Total de elementos
        r: Elementos a permutar
    
    Returns:
        int: P(n, r)
    """
    if r < 0 or r > n:
        return 0
    
    result = 1
    for i in range(n, n - r, -1):
        result *= i
    
    return result

# ESTADÍSTICAS
def mean(numbers: List[Union[int, float]]) -> float:
    """
    Calcular media aritmética.
    
    Args:
        numbers: Lista de números
    
    Returns:
        float: Media
    """
    if not numbers:
        return 0.0
    
    return sum(numbers) / len(numbers)

def median(numbers: List[Union[int, float]]) -> float:
    """
    Calcular mediana.
    
    Args:
        numbers: Lista de números
    
    Returns:
        float: Mediana
    """
    if not numbers:
        return 0.0
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    
    if n % 2 == 0:
        return (sorted_numbers[n // 2 - 1] + sorted_numbers[n // 2]) / 2
    else:
        return sorted_numbers[n // 2]

def mode(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    Calcular moda (valor más frecuente).
    
    Args:
        numbers: Lista de números
    
    Returns:
        Valor más frecuente
    """
    if not numbers:
        return 0
    
    from collections import Counter
    counter = Counter(numbers)
    return counter.most_common(1)[0][0]

def variance(numbers: List[Union[int, float]]) -> float:
    """
    Calcular varianza.
    
    Args:
        numbers: Lista de números
    
    Returns:
        float: Varianza
    """
    if not numbers:
        return 0.0
    
    avg = mean(numbers)
    return sum((x - avg) ** 2 for x in numbers) / len(numbers)

def std_deviation(numbers: List[Union[int, float]]) -> float:
    """
    Calcular desviación estándar.
    
    Args:
        numbers: Lista de números
    
    Returns:
        float: Desviación estándar
    """
    return math.sqrt(variance(numbers))

def percentile(numbers: List[Union[int, float]], p: float) -> float:
    """
    Calcular percentil.
    
    Args:
        numbers: Lista de números
        p: Percentil (0-100)
    
    Returns:
        float: Valor del percentil
    
    Example:
        >>> percentile([1, 2, 3, 4, 5], 50)  # Mediana
        3.0
    """
    if not numbers:
        return 0.0
    
    sorted_numbers = sorted(numbers)
    k = (len(sorted_numbers) - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)
    
    if f == c:
        return sorted_numbers[int(k)]
    
    d0 = sorted_numbers[int(f)] * (c - k)
    d1 = sorted_numbers[int(c)] * (k - f)
    
    return d0 + d1

# ANÁLISIS DE COMPLEJIDAD
def compare_complexities(complexity1: str, complexity2: str) -> int:
    """
    Comparar dos complejidades.
    
    Args:
        complexity1: Primera complejidad (ej: "O(n)")
        complexity2: Segunda complejidad (ej: "O(log n)")
    
    Returns:
        int: -1 si c1 < c2, 0 si iguales, 1 si c1 > c2
    
    Example:
        >>> compare_complexities("O(n)", "O(n²)")
        -1  # O(n) es mejor que O(n²)
    """
    # Orden de complejidades (de mejor a peor)
    complexity_order = {
        "O(1)": 0,
        "O(log log n)": 1,
        "O(log n)": 2,
        "O(√n)": 3,
        "O(n)": 4,
        "O(n log n)": 5,
        "O(n²)": 6,
        "O(n³)": 7,
        "O(2^n)": 8,
        "O(n!)": 9,
    }
    
    # Normalizar notaciones
    c1 = complexity1.replace("^", "").replace("log(n)", "log n")
    c2 = complexity2.replace("^", "").replace("log(n)", "log n")
    
    order1 = complexity_order.get(c1, 999)
    order2 = complexity_order.get(c2, 999)
    
    if order1 < order2:
        return -1
    elif order1 > order2:
        return 1
    else:
        return 0

def evaluate_complexity(complexity: str, n: int) -> float:
    """
    Evaluar complejidad para un valor de n.
    
    Args:
        complexity: Notación de complejidad
        n: Tamaño de entrada
    
    Returns:
        float: Valor aproximado
    
    Example:
        >>> evaluate_complexity("O(n²)", 10)
        100.0
    """
    # Extraer la parte interna de la notación
    import re
    match = re.search(r'O\((.*)\)', complexity)
    if not match:
        return 0.0
    
    expr = match.group(1)
    
    # Mapeo de expresiones comunes
    evaluations = {
        "1": 1,
        "log n": math.log2(n) if n > 0 else 0,
        "n": n,
        "n log n": n * math.log2(n) if n > 0 else 0,
        "n²": n ** 2,
        "n^2": n ** 2,
        "n³": n ** 3,
        "n^3": n ** 3,
        "2^n": 2 ** min(n, 30),  # Limitar para evitar overflow
        "n!": min(factorial(min(n, 20)), 10**15),  # Limitar factorial
    }
    
    return evaluations.get(expr, n)

# NÚMEROS PRIMOS
def is_prime(n: int) -> bool:
    """
    Verificar si un número es primo.
    
    Args:
        n: Número a verificar
    
    Returns:
        bool: True si es primo
    
    Example:
        >>> is_prime(17)
        True
        >>> is_prime(18)
        False
    """
    if n < 2:
        return False
    
    if n == 2:
        return True
    
    if n % 2 == 0:
        return False
    
    # Verificar divisores impares hasta √n
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    
    return True

def next_prime(n: int) -> int:
    """
    Encontrar el siguiente número primo.
    
    Args:
        n: Número inicial
    
    Returns:
        int: Siguiente primo
    """
    candidate = n + 1
    while not is_prime(candidate):
        candidate += 1
    return candidate

def prime_factors(n: int) -> List[int]:
    """
    Obtener factores primos de un número.
    
    Args:
        n: Número a factorizar
    
    Returns:
        List[int]: Lista de factores primos
    
    Example:
        >>> prime_factors(12)
        [2, 2, 3]
    """
    factors = []
    d = 2
    
    while n > 1:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
        
        if d * d > n:
            if n > 1:
                factors.append(n)
            break
    
    return factors

# SECUENCIAS
def fibonacci(n: int) -> int:
    """
    Calcular n-ésimo número de Fibonacci.
    
    Args:
        n: Posición en la secuencia
    
    Returns:
        int: Número de Fibonacci
    
    Example:
        >>> fibonacci(10)
        55
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b

def fibonacci_sequence(n: int) -> List[int]:
    """
    Generar secuencia de Fibonacci hasta n elementos.
    
    Args:
        n: Número de elementos
    
    Returns:
        List[int]: Secuencia de Fibonacci
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    
    return sequence

# REDONDEO
def round_to_significant_digits(number: float, digits: int) -> float:
    """
    Redondear a cifras significativas.
    
    Args:
        number: Número a redondear
        digits: Cifras significativas
    
    Returns:
        float: Número redondeado
    
    Example:
        >>> round_to_significant_digits(123.456, 2)
        120.0
    """
    if number == 0:
        return 0
    
    return round(number, -int(math.floor(math.log10(abs(number)))) + (digits - 1))

def round_up_to_nearest(number: float, nearest: float) -> float:
    """
    Redondear hacia arriba al múltiplo más cercano.
    
    Args:
        number: Número a redondear
        nearest: Múltiplo
    
    Returns:
        float: Número redondeado
    
    Example:
        >>> round_up_to_nearest(23, 10)
        30.0
    """
    return math.ceil(number / nearest) * nearest