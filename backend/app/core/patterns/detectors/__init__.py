"""
Detectors Module - Detectores Específicos de Patrones

Cada detector especializado en identificar un patrón algorítmico particular.

Detectores Implementados:
- BruteForceDetector: Algoritmos de fuerza bruta
- RecursiveDetector: Algoritmos recursivos
- DivideConquerDetector: Divide y Vencerás
- DynamicProgrammingDetector: Programación Dinámica
- GreedyDetector: Algoritmos Voraces

Detectores por Implementar:
- BacktrackingDetector: Backtracking
- BranchBoundDetector: Branch and Bound
- SortingDetector: Algoritmos de Ordenamiento
- SearchingDetector: Algoritmos de Búsqueda
- QuantumAlgorithmsDetector: Algoritmos Cuánticos
- BioInspiredDetector: Algoritmos Bio-inspirados
- ApproximationDetector: Algoritmos de Aproximación
"""

from app.core.patterns.detectors.brute_force import BruteForceDetector
from app.core.patterns.detectors.recursive_detector import RecursiveDetector
from app.core.patterns.detectors.divide_conquer_detector import DivideConquerDetector
from app.core.patterns.detectors.dynamic_programming_detector import DynamicProgrammingDetector
from app.core.patterns.detectors.greedy_detector import GreedyDetector

# Los siguientes se importarán cuando estén implementados:
# from app.core.patterns.detectors.backtracking_detector import BacktrackingDetector
# from app.core.patterns.detectors.branch_bound_detector import BranchBoundDetector
# from app.core.patterns.detectors.sorting_detector import SortingDetector
# from app.core.patterns.detectors.searching_detector import SearchingDetector
# from app.core.patterns.detectors.quantum_algorithms import QuantumAlgorithmsDetector
# from app.core.patterns.detectors.bio_inspired_algorithms import BioInspiredDetector
# from app.core.patterns.detectors.approximation_detector import ApproximationDetector

__all__ = [
    "BruteForceDetector",
    "RecursiveDetector",
    "DivideConquerDetector",
    "DynamicProgrammingDetector",
    "GreedyDetector",
    # Agregar los demás cuando se implementen
]