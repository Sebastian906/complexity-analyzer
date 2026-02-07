"""
Complexity Labeler - Etiquetador Automático de Complejidades

Analiza algoritmos y genera etiquetas de complejidad para datasets.
Usa el motor de análisis existente del proyecto.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict

# Importar módulos del proyecto
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.core.parser import parse_pseudocode
from app.core.analyzer import AnalyzerEngine
from app.core.patterns import PatternDetector
from app.core.data_structures import StructureIdentifier

@dataclass
class ComplexityLabel:
    """Etiqueta de complejidad completa para un algoritmo"""
    
    # Complejidades
    big_o: str
    omega: str
    theta: str
    space_complexity: str
    
    # Patrón principal
    primary_pattern: str
    primary_pattern_confidence: float
    
    # Estructuras de datos
    structures: list
    
    # Metadata
    recurrence_equation: Optional[str] = None
    is_recursive: bool = False
    is_iterative: bool = False
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return {
            "big_o": self.big_o,
            "omega": self.omega,
            "theta": self.theta,
            "space_complexity": self.space_complexity,
            "primary_pattern": self.primary_pattern,
            "primary_pattern_confidence": self.primary_pattern_confidence,
            "structures": self.structures,
            "recurrence_equation": self.recurrence_equation,
            "is_recursive": self.is_recursive,
            "is_iterative": self.is_iterative,
        }

class ComplexityLabeler:
    """Etiquetador automático de complejidades usando motor de análisis"""
    
    def __init__(self):
        """Inicializa el labeler con componentes de análisis"""
        self.analyzer = AnalyzerEngine()
        self.pattern_detector = PatternDetector()
        self.structure_identifier = StructureIdentifier()
    
    def label(self, code: str) -> ComplexityLabel:
        """
        Etiqueta un algoritmo con sus complejidades
        
        Args:
            code: Código del algoritmo en pseudocódigo
        
        Returns:
            ComplexityLabel con todas las métricas
        
        Raises:
            Exception: Si el parsing o análisis falla
        """
        # 1. Parsear código
        ast = parse_pseudocode(code)
        
        # 2. Analizar complejidad
        analysis_result = self.analyzer.analyze(ast)
        
        # 3. Detectar patrones
        pattern_result = self.pattern_detector.detect(ast, min_confidence=0.3)
        
        # 4. Identificar estructuras
        structure_result = self.structure_identifier.identify(ast)
        
        # 5. Construir etiqueta
        label = ComplexityLabel(
            big_o=analysis_result.big_o or "Unknown",
            omega=analysis_result.omega or "Unknown",
            theta=analysis_result.theta or "Unknown",
            space_complexity=analysis_result.space_complexity or "Unknown",
            primary_pattern=pattern_result.primary_pattern_name or "unknown",
            primary_pattern_confidence=pattern_result.primary_pattern_confidence or 0.0,
            structures=[s.structure_type.value for s in structure_result.detected_structures],
            recurrence_equation=str(analysis_result.recurrence_temporal) if analysis_result.recurrence_temporal else None,
            is_recursive=pattern_result.is_recursive,
            is_iterative=not pattern_result.is_recursive,
        )
        
        return label
    
    def label_batch(self, algorithms: list) -> list:
        """
        Etiqueta múltiples algoritmos en lote
        
        Args:
            algorithms: Lista de códigos de algoritmos
        
        Returns:
            Lista de ComplexityLabel
        """
        labels = []
        
        for code in algorithms:
            try:
                label = self.label(code)
                labels.append(label)
            except Exception as e:
                # En caso de error, agregar label con valores por defecto
                labels.append(ComplexityLabel(
                    big_o="Error",
                    omega="Error",
                    theta="Error",
                    space_complexity="Error",
                    primary_pattern="error",
                    primary_pattern_confidence=0.0,
                    structures=[],
                ))
        
        return labels

def label_algorithm(code: str) -> ComplexityLabel:
    """
    Helper function para etiquetar un algoritmo
    
    Args:
        code: Código del algoritmo
    
    Returns:
        ComplexityLabel
    """
    labeler = ComplexityLabeler()
    return labeler.label(code)