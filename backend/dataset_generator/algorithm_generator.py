"""
Algorithm Generator - Generador de Variaciones Sintéticas de Algoritmos

Genera variaciones de algoritmos base para crear datasets diversos.
Técnicas:
- Renombrado de variables
- Reordenamiento de statements independientes
- Variación de estructuras de control (for/while intercambiables)
- Inserción de operaciones neutras (comentarios, asignaciones dummy)
"""

import random
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class VariationType(str, Enum):
    """Tipos de variaciones aplicables"""
    RENAME_VARIABLES = "rename_variables"
    REORDER_STATEMENTS = "reorder_statements"
    CHANGE_LOOP_TYPE = "change_loop_type"
    ADD_NEUTRAL_OPS = "add_neutral_ops"
    MODIFY_WHITESPACE = "modify_whitespace"

@dataclass
class GenerationConfig:
    """Configuración para generación de variaciones"""
    variation_types: List[VariationType] = field(default_factory=lambda: [
        VariationType.RENAME_VARIABLES,
        VariationType.MODIFY_WHITESPACE
    ])
    max_variations: int = 10
    preserve_complexity: bool = True
    seed: Optional[int] = None

@dataclass
class AlgorithmTemplate:
    """Template de algoritmo base"""
    name: str
    code: str
    category: str
    expected_complexity: str
    pattern: str
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return {
            "name": self.name,
            "code": self.code,
            "category": self.category,
            "expected_complexity": self.expected_complexity,
            "pattern": self.pattern,
            "tags": self.tags
        }

class AlgorithmGenerator:
    """Generador de variaciones sintéticas de algoritmos"""
    
    # Nombres alternativos para variables comunes
    VARIABLE_ALTERNATIVES = {
        "i": ["idx", "counter", "k", "index"],
        "j": ["jdx", "col", "m", "pos"],
        "n": ["size", "length", "count", "num"],
        "x": ["val", "value", "item", "elem"],
        "temp": ["tmp", "swap", "aux", "buffer"],
        "A": ["arr", "array", "list", "data"],
        "left": ["l", "low", "start", "begin"],
        "right": ["r", "high", "end", "finish"],
        "mid": ["middle", "center", "pivot"],
    }
    
    def __init__(self, config: GenerationConfig = None):
        """
        Inicializa el generador
        
        Args:
            config: Configuración de generación
        """
        self.config = config or GenerationConfig()
        
        if self.config.seed is not None:
            random.seed(self.config.seed)
    
    def generate_variations(
        self,
        template: AlgorithmTemplate,
        count: int = None
    ) -> List[AlgorithmTemplate]:
        """
        Genera variaciones de un template
        
        Args:
            template: Template base
            count: Número de variaciones (default: config.max_variations)
        
        Returns:
            Lista de templates variados
        """
        count = count or self.config.max_variations
        variations = []
        
        for i in range(count):
            # Aplicar variaciones según configuración
            code = template.code
            
            for variation_type in self.config.variation_types:
                if variation_type == VariationType.RENAME_VARIABLES:
                    code = self._rename_variables(code)
                elif variation_type == VariationType.MODIFY_WHITESPACE:
                    code = self._modify_whitespace(code)
                # Otros tipos de variación se pueden agregar aquí
            
            # Crear nuevo template
            variation = AlgorithmTemplate(
                name=f"{template.name}_var{i+1}",
                code=code,
                category=template.category,
                expected_complexity=template.expected_complexity,
                pattern=template.pattern,
                tags=template.tags.copy()
            )
            
            variations.append(variation)
        
        return variations
    
    def _rename_variables(self, code: str) -> str:
        """
        Renombra variables manteniendo consistencia
        
        Args:
            code: Código original
        
        Returns:
            Código con variables renombradas
        """
        # Mapeo de renombramientos
        renames = {}
        
        # Identificar variables a renombrar
        for var, alternatives in self.VARIABLE_ALTERNATIVES.items():
            if var in code:
                # Elegir alternativa aleatoria
                new_name = random.choice(alternatives)
                renames[var] = new_name
        
        # Aplicar renombramientos (cuidado con orden para evitar colisiones)
        modified_code = code
        
        for old_var, new_var in renames.items():
            # Usar word boundaries para evitar renombrar partes de palabras
            pattern = r'\b' + re.escape(old_var) + r'\b'
            modified_code = re.sub(pattern, new_var, modified_code)
        
        return modified_code
    
    def _modify_whitespace(self, code: str) -> str:
        """
        Modifica whitespace (espacios, indentación)
        
        Args:
            code: Código original
        
        Returns:
            Código con whitespace modificado
        """
        lines = code.split('\n')
        modified_lines = []
        
        for line in lines:
            # Añadir espacios aleatorios al final (que no afecten parsing)
            if random.random() < 0.3:  # 30% de probabilidad
                line = line.rstrip() + ' ' * random.randint(1, 3)
            
            modified_lines.append(line)
        
        return '\n'.join(modified_lines)
    
    def generate_from_pattern(
        self,
        pattern: str,
        count: int = 10
    ) -> List[AlgorithmTemplate]:
        """
        Genera algoritmos de un patrón específico
        
        Args:
            pattern: Patrón algorítmico (divide_conquer, dynamic_programming, etc.)
            count: Número de algoritmos
        
        Returns:
            Lista de templates generados
        """
        # Templates base por patrón
        base_templates = self._get_base_templates_for_pattern(pattern)
        
        if not base_templates:
            return []
        
        all_variations = []
        
        # Distribuir count entre templates base
        variations_per_template = max(1, count // len(base_templates))
        
        for template in base_templates:
            variations = self.generate_variations(template, variations_per_template)
            all_variations.extend(variations)
        
        # Ajustar a count exacto
        return all_variations[:count]
    
    def _get_base_templates_for_pattern(self, pattern: str) -> List[AlgorithmTemplate]:
        """
        Obtiene templates base para un patrón
        
        Args:
            pattern: Nombre del patrón
        
        Returns:
            Lista de templates base
        """
        # Templates predefinidos (se pueden expandir)
        templates_db = {
            "divide_and_conquer": [
                AlgorithmTemplate(
                    name="mergeSort",
                    code="""algorithm mergeSort(A[1..n])
begin
    if (n > 1) then
    begin
        mid ← n / 2
        call mergeSort(A[1..mid])
        call mergeSort(A[mid+1..n])
        call merge(A, 1, mid, n)
    end
end""",
                    category="sorting",
                    expected_complexity="O(n log n)",
                    pattern="divide_and_conquer",
                    tags=["sorting", "divide-conquer", "recursive"]
                ),
                AlgorithmTemplate(
                    name="quickSort",
                    code="""algorithm quickSort(A[1..n], low, high)
begin
    if (low < high) then
    begin
        pivot ← partition(A, low, high)
        call quickSort(A, low, pivot - 1)
        call quickSort(A, pivot + 1, high)
    end
end""",
                    category="sorting",
                    expected_complexity="O(n log n)",
                    pattern="divide_and_conquer",
                    tags=["sorting", "divide-conquer"]
                ),
            ],
            "dynamic_programming": [
                AlgorithmTemplate(
                    name="fibonacciDP",
                    code="""algorithm fibonacciDP(n)
begin
    dp[0] ← 0
    dp[1] ← 1
    
    for i ← 2 to n do
    begin
        dp[i] ← dp[i-1] + dp[i-2]
    end
    
    return dp[n]
end""",
                    category="recursion",
                    expected_complexity="O(n)",
                    pattern="dynamic_programming",
                    tags=["dynamic-programming", "fibonacci"]
                ),
            ],
            "brute_force": [
                AlgorithmTemplate(
                    name="bubbleSort",
                    code="""algorithm bubbleSort(A[1..n])
begin
    for i ← 1 to n - 1 do
    begin
        for j ← 1 to n - i do
        begin
            if (A[j] > A[j + 1]) then
            begin
                temp ← A[j]
                A[j] ← A[j + 1]
                A[j + 1] ← temp
            end
        end
    end
end""",
                    category="sorting",
                    expected_complexity="O(n²)",
                    pattern="brute_force",
                    tags=["sorting", "quadratic"]
                ),
            ],
        }
        
        return templates_db.get(pattern, [])

def generate_algorithm_variations(
    template: AlgorithmTemplate,
    count: int = 10,
    config: GenerationConfig = None
) -> List[AlgorithmTemplate]:
    """
    Helper function para generar variaciones
    
    Args:
        template: Template base
        count: Número de variaciones
        config: Configuración
    
    Returns:
        Lista de variaciones
    """
    generator = AlgorithmGenerator(config)
    return generator.generate_variations(template, count)