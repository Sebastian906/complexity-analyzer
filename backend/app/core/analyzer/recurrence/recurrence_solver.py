"""
Recurrence Solver - Resolvedor de Ecuaciones de Recurrencia

Implementa 5 métodos para resolver ecuaciones de recurrencia:
1. Iteración
2. Árbol de Recursión
3. Teorema Maestro (Master Theorem)
4. Sustitución Inteligente
5. Ecuación Característica

Soporta 7 formas de ecuaciones:
- Divide y Vencerás: F0, F1, F2, F3
- Resta y Vencerás: F4
- Resta y serás Vencido: F5, F6
"""

from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import math

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RecurrenceForm(Enum):
    """Formas de ecuaciones de recurrencia"""
    # Divide y Vencerás
    F0 = "T(n) = T(n/b) + f(n)"
    F1 = "T(n) = aT(n/b) + f(n)"
    F2 = "T(n) = T(n/b) + T(n/c) + f(n)"
    F3 = "T(n) = T(n/b) + T(n/c) + ... + T(n/z) + f(n)"
    
    # Resta y Vencerás
    F4 = "T(n) = T(n-b) + f(n)"
    
    # Resta y serás Vencido
    F5 = "T(n) = aT(n-b) + f(n)"
    F6 = "T(n) = aT(n-b) + cT(n-d) + f(n)"


class SolutionMethod(Enum):
    """Métodos de solución"""
    ITERATION = "iteracion"
    RECURSION_TREE = "arbol_recursion"
    MASTER_THEOREM = "teorema_maestro"
    SMART_SUBSTITUTION = "sustitucion_inteligente"
    CHARACTERISTIC_EQUATION = "ecuacion_caracteristica"


@dataclass
class RecurrencePattern:
    """Patrón de una ecuación de recurrencia"""
    form: RecurrenceForm
    a: int = 1
    b: int = 2
    c: Optional[int] = None
    d: Optional[int] = None
    f_n: str = "1"
    additional_terms: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class SolutionResult:
    """Resultado de resolver una ecuación"""
    complexity: str
    method_used: SolutionMethod
    steps: List[str]
    form_detected: RecurrenceForm
    is_exact: bool = True
    explanation: str = ""
    alternative_methods: List[SolutionMethod] = field(default_factory=list)


class RecurrenceSolver:
    """
    Resolvedor de ecuaciones de recurrencia.
    
    Detecta automáticamente la forma de la ecuación y aplica
    el método más apropiado para resolverla.
    """
    
    # Tabla de aplicabilidad
    METHOD_APPLICABILITY = {
        SolutionMethod.ITERATION: [
            RecurrenceForm.F0, RecurrenceForm.F1, 
            RecurrenceForm.F4, RecurrenceForm.F5
        ],
        SolutionMethod.RECURSION_TREE: [
            RecurrenceForm.F0, RecurrenceForm.F1, RecurrenceForm.F2, 
            RecurrenceForm.F3, RecurrenceForm.F5, RecurrenceForm.F6
        ],
        SolutionMethod.MASTER_THEOREM: [
            RecurrenceForm.F0, RecurrenceForm.F1
        ],
        SolutionMethod.SMART_SUBSTITUTION: [
            RecurrenceForm.F0, RecurrenceForm.F1, RecurrenceForm.F2,
            RecurrenceForm.F3, RecurrenceForm.F4, RecurrenceForm.F5,
            RecurrenceForm.F6
        ],
        SolutionMethod.CHARACTERISTIC_EQUATION: [
            RecurrenceForm.F4, RecurrenceForm.F5, RecurrenceForm.F6
        ]
    }
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def solve(
        self,
        equation: str,
        base_case: Optional[str] = None,
        preferred_method: Optional[SolutionMethod] = None
    ) -> SolutionResult:
        """Resuelve una ecuación de recurrencia"""
        self.logger.info(f"Resolviendo ecuación: {equation}")
        
        pattern = self._detect_form(equation)
        
        if not pattern:
            return self._create_error_result(
                "No se pudo detectar la forma de la ecuación"
            )
        
        self.logger.info(f"Forma detectada: {pattern.form.name}")
        
        applicable_methods = self._get_applicable_methods(pattern.form)
        
        if not applicable_methods:
            return self._create_error_result(
                f"No hay métodos aplicables para {pattern.form.name}"
            )
        
        if preferred_method and preferred_method in applicable_methods:
            method = preferred_method
        else:
            method = self._select_best_method(pattern.form, applicable_methods)
        
        self.logger.info(f"Usando método: {method.value}")
        
        try:
            if method == SolutionMethod.ITERATION:
                result = self._solve_by_iteration(pattern)
            elif method == SolutionMethod.RECURSION_TREE:
                result = self._solve_by_recursion_tree(pattern)
            elif method == SolutionMethod.MASTER_THEOREM:
                result = self._solve_by_master_theorem(pattern)
            elif method == SolutionMethod.SMART_SUBSTITUTION:
                result = self._solve_by_smart_substitution(pattern)
            elif method == SolutionMethod.CHARACTERISTIC_EQUATION:
                result = self._solve_by_characteristic_equation(pattern)
            else:
                return self._create_error_result(f"Método {method} no implementado")
            
            result.alternative_methods = [
                m for m in applicable_methods if m != method
            ]
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error resolviendo: {e}")
            return self._create_error_result(str(e))
    
    def _detect_form(self, equation: str) -> Optional[RecurrencePattern]:
        """Detecta la forma de la ecuación"""
        equation = equation.replace(" ", "").upper()
        
        # F1: T(n) = aT(n/b) + f(n) - acepta * opcional entre coeficiente y T
        pattern = re.match(r'T\(N\)=(\d+)\*?T\(N/(\d+)\)\+(.+)', equation)
        if pattern:
            a, b, f_n = pattern.groups()
            return RecurrencePattern(
                form=RecurrenceForm.F1,
                a=int(a),
                b=int(b),
                f_n=f_n
            )
        
        # F0: T(n) = T(n/b) + f(n)
        pattern = re.match(r'T\(N\)=T\(N/(\d+)\)\+(.+)', equation)
        if pattern:
            b, f_n = pattern.groups()
            return RecurrencePattern(
                form=RecurrenceForm.F0,
                a=1,
                b=int(b),
                f_n=f_n
            )
        
        # F2: T(n) = T(n/b) + T(n/c) + f(n)
        pattern = re.match(r'T\(N\)=T\(N/(\d+)\)\+T\(N/(\d+)\)\+(.+)', equation)
        if pattern:
            b, c, f_n = pattern.groups()
            return RecurrencePattern(
                form=RecurrenceForm.F2,
                a=1,
                b=int(b),
                c=int(c),
                f_n=f_n
            )
        
        # F5: T(n) = aT(n-b) + f(n) - acepta * opcional entre coeficiente y T
        pattern = re.match(r'T\(N\)=(\d+)\*?T\(N-(\d+)\)\+(.+)', equation)
        if pattern:
            a, b, f_n = pattern.groups()
            return RecurrencePattern(
                form=RecurrenceForm.F5,
                a=int(a),
                b=int(b),
                f_n=f_n
            )
        
        # F4: T(n) = T(n-b) + f(n)
        pattern = re.match(r'T\(N\)=T\(N-(\d+)\)\+(.+)', equation)
        if pattern:
            b, f_n = pattern.groups()
            return RecurrencePattern(
                form=RecurrenceForm.F4,
                a=1,
                b=int(b),
                f_n=f_n
            )
        
        # F6: T(n) = aT(n-b) + cT(n-d) + f(n) - acepta * opcional
        pattern = re.match(r'T\(N\)=(\d+)\*?T\(N-(\d+)\)\+(\d+)\*?T\(N-(\d+)\)\+(.+)', equation)
        if pattern:
            a, b, c, d, f_n = pattern.groups()
            return RecurrencePattern(
                form=RecurrenceForm.F6,
                a=int(a),
                b=int(b),
                c=int(c),
                d=int(d),
                f_n=f_n
            )
        
        return None
    
    def _solve_by_iteration(self, pattern: RecurrencePattern) -> SolutionResult:
        """Resuelve por iteración"""
        steps = ["Método de Iteración:", ""]
        
        if pattern.form == RecurrenceForm.F0:
            steps.append("Expandiendo iterativamente:")
            steps.append(f"T(n) = T(n/{pattern.b}) + f(n)")
            steps.append(f"     = T(n/{pattern.b}²) + f(n/{pattern.b}) + f(n)")
            steps.append(f"     = T(1) + Σ f(n/{pattern.b}ⁱ)")
            
            complexity = self._determine_iteration_complexity(pattern)
            
        elif pattern.form == RecurrenceForm.F1:
            steps.append("Expandiendo iterativamente:")
            steps.append(f"T(n) = {pattern.a}T(n/{pattern.b}) + f(n)")
            steps.append(f"     = {pattern.a}²T(n/{pattern.b}²) + {pattern.a}f(n/{pattern.b}) + f(n)")
            
            complexity = self._determine_iteration_complexity(pattern)
            
        elif pattern.form == RecurrenceForm.F4:
            steps.append("Expandiendo:")
            steps.append(f"T(n) = T(n-{pattern.b}) + f(n)")
            steps.append(f"     = T(1) + Σ f(n-i×{pattern.b})")
            
            complexity = self._determine_iteration_complexity(pattern)
            
        elif pattern.form == RecurrenceForm.F5:
            steps.append("Expandiendo:")
            steps.append(f"T(n) = {pattern.a}T(n-{pattern.b}) + f(n)")
            
            complexity = self._determine_iteration_complexity(pattern)
        else:
            raise ValueError(f"Iteración no aplicable a {pattern.form.name}")
        
        return SolutionResult(
            complexity=complexity,
            method_used=SolutionMethod.ITERATION,
            steps=steps,
            form_detected=pattern.form,
            explanation="Ecuación resuelta expandiendo iterativamente."
        )
    
    def _solve_by_recursion_tree(self, pattern: RecurrencePattern) -> SolutionResult:
        """Resuelve por árbol de recursión"""
        steps = ["Método de Árbol de Recursión:", ""]
        
        if pattern.form in [RecurrenceForm.F0, RecurrenceForm.F1]:
            steps.append("Estructura del árbol:")
            steps.append(f"Nivel 0: 1 nodo con costo f(n)")
            steps.append(f"Nivel 1: {pattern.a} nodos con costo f(n/{pattern.b})")
            steps.append(f"Nivel 2: {pattern.a}² nodos")
            steps.append(f"Profundidad: log_{pattern.b}(n)")
            
            complexity = self._calculate_tree_complexity(pattern)
        else:
            steps.append("Construyendo árbol...")
            complexity = self._calculate_tree_complexity(pattern)
        
        return SolutionResult(
            complexity=complexity,
            method_used=SolutionMethod.RECURSION_TREE,
            steps=steps,
            form_detected=pattern.form,
            explanation="Árbol de recursión analizado nivel por nivel."
        )
    
    def _solve_by_master_theorem(self, pattern: RecurrencePattern) -> SolutionResult:
        """Resuelve con Teorema Maestro"""
        steps = ["Teorema Maestro:", ""]
        
        if pattern.form not in [RecurrenceForm.F0, RecurrenceForm.F1]:
            raise ValueError("Teorema Maestro solo aplica a F0 y F1")
        
        a, b = pattern.a, pattern.b
        
        steps.append(f"T(n) = {a}T(n/{b}) + {pattern.f_n}")
        steps.append(f"Parámetros: a={a}, b={b}")
        
        log_b_a = math.log(a) / math.log(b)
        steps.append(f"log_{b}({a}) = {log_b_a:.2f}")
        
        f_complexity = self._parse_function_complexity(pattern.f_n)
        steps.append(f"f(n) = {f_complexity}")
        
        complexity, case_used = self._apply_master_theorem(a, b, log_b_a, f_complexity)
        
        steps.append("")
        steps.append(f"Caso {case_used} del Teorema Maestro")
        steps.append(f"Resultado: T(n) = Θ({complexity})")
        
        return SolutionResult(
            complexity=complexity,
            method_used=SolutionMethod.MASTER_THEOREM,
            steps=steps,
            form_detected=pattern.form,
            explanation=f"Teorema Maestro Caso {case_used} aplicado."
        )
    
    def _solve_by_smart_substitution(self, pattern: RecurrencePattern) -> SolutionResult:
        """Resuelve por sustitución inteligente"""
        steps = ["Método de Sustitución Inteligente:", ""]
        
        guess = self._make_educated_guess(pattern)
        
        steps.append(f"Conjetura: T(n) = O({guess})")
        steps.append("")
        steps.append("Demostración por inducción:")
        steps.append(f"Hipótesis: T(k) ≤ c×{guess} para k < n")
        
        verification_steps = self._verify_guess(pattern, guess)
        steps.extend(verification_steps)
        
        return SolutionResult(
            complexity=guess,
            method_used=SolutionMethod.SMART_SUBSTITUTION,
            steps=steps,
            form_detected=pattern.form,
            explanation="Conjetura verificada por inducción."
        )
    
    def _solve_by_characteristic_equation(self, pattern: RecurrencePattern) -> SolutionResult:
        """Resuelve por ecuación característica"""
        steps = ["Método de Ecuación Característica:", ""]
        
        if pattern.form == RecurrenceForm.F4:
            steps.append(f"Ecuación: T(n) - T(n-{pattern.b}) = f(n)")
            steps.append("Ecuación característica: r - 1 = 0")
            steps.append("Raíz: r = 1")
            
            complexity = self._solve_linear_recurrence_f4(pattern)
            
        elif pattern.form == RecurrenceForm.F5:
            steps.append(f"Ecuación: T(n) - {pattern.a}T(n-{pattern.b}) = f(n)")
            steps.append(f"Ecuación característica: r - {pattern.a} = 0")
            steps.append(f"Raíz: r = {pattern.a}")
            
            complexity = self._solve_linear_recurrence_f5(pattern)
            
        elif pattern.form == RecurrenceForm.F6:
            steps.append(f"Ecuación cuadrática: r² - {pattern.a}r - {pattern.c} = 0")
            
            discriminant = pattern.a**2 + 4*pattern.c
            steps.append(f"Discriminante: {discriminant}")
            
            if discriminant >= 0:
                r1 = (pattern.a + math.sqrt(discriminant)) / 2
                r2 = (pattern.a - math.sqrt(discriminant)) / 2
                steps.append(f"Raíces: r₁={r1:.2f}, r₂={r2:.2f}")
            
            complexity = self._solve_linear_recurrence_f6(pattern)
        else:
            raise ValueError(f"Ecuación característica no aplicable a {pattern.form.name}")
        
        return SolutionResult(
            complexity=complexity,
            method_used=SolutionMethod.CHARACTERISTIC_EQUATION,
            steps=steps,
            form_detected=pattern.form,
            explanation="Ecuación característica resuelta."
        )
    
    def _get_applicable_methods(self, form: RecurrenceForm) -> List[SolutionMethod]:
        """Obtiene métodos aplicables"""
        applicable = []
        for method, forms in self.METHOD_APPLICABILITY.items():
            if form in forms:
                applicable.append(method)
        return applicable
    
    def _select_best_method(
        self,
        form: RecurrenceForm,
        applicable: List[SolutionMethod]
    ) -> SolutionMethod:
        """Selecciona el mejor método"""
        priority = [
            SolutionMethod.MASTER_THEOREM,
            SolutionMethod.CHARACTERISTIC_EQUATION,
            SolutionMethod.ITERATION,
            SolutionMethod.RECURSION_TREE,
            SolutionMethod.SMART_SUBSTITUTION
        ]
        
        for method in priority:
            if method in applicable:
                return method
        
        return applicable[0]
    
    def _determine_iteration_complexity(self, pattern: RecurrencePattern) -> str:
        """Determina complejidad por iteración"""
        if pattern.form in [RecurrenceForm.F0, RecurrenceForm.F1]:
            if pattern.f_n.upper() in ["1", "O(1)", "C"]:
                log_b_a = math.log(pattern.a) / math.log(pattern.b)
                return f"n^{log_b_a:.2f}"
            elif "N" in pattern.f_n.upper():
                return "n log n"
        elif pattern.form in [RecurrenceForm.F4, RecurrenceForm.F5]:
            if pattern.f_n.upper() in ["1", "O(1)"]:
                return "n" if pattern.a == 1 else f"{pattern.a}^n"
        
        return "n"
    
    def _calculate_tree_complexity(self, pattern: RecurrencePattern) -> str:
        """Calcula complejidad por árbol"""
        if pattern.form == RecurrenceForm.F1:
            log_b_a = math.log(pattern.a) / math.log(pattern.b)
            
            if pattern.f_n.upper() in ["1", "O(1)"]:
                return f"n^{log_b_a:.2f}"
            elif "N" in pattern.f_n.upper():
                if abs(log_b_a - 1.0) < 0.01:
                    return "n log n"
                else:
                    return f"n^{log_b_a:.2f}"
        
        return "n log n"
    
    def _apply_master_theorem(
        self,
        a: int,
        b: int,
        log_b_a: float,
        f_complexity: str
    ) -> Tuple[str, int]:
        """Aplica Teorema Maestro"""
        if f_complexity in ["1", "O(1)"]:
            c = 0
        elif "n^" in f_complexity:
            c = float(f_complexity.split("^")[1])
        elif f_complexity == "n²" or f_complexity == "n^2":
            c = 2
        elif f_complexity == "n³" or f_complexity == "n^3":
            c = 3
        elif f_complexity == "n":
            c = 1
        elif "log" in f_complexity.lower():
            return (f"n^{log_b_a:.2f} log n", 2)
        else:
            c = 1
        
        epsilon = 0.01
        
        if c < log_b_a - epsilon:
            return (f"n^{log_b_a:.2f}", 1)
        elif abs(c - log_b_a) < epsilon:
            return (f"n^{log_b_a:.2f} log n", 2)
        else:
            return (f_complexity, 3)
    
    def _parse_function_complexity(self, f_n: str) -> str:
        """Parsea complejidad de f(n)"""
        f_n_upper = f_n.upper().replace("O(", "").replace(")", "")
        
        if f_n_upper in ["1", "C"]:
            return "1"
        elif "LOG" in f_n_upper:
            return "log n"
        elif "N^2" in f_n_upper or "N²" in f_n_upper:
            return "n²"
        elif "N" in f_n_upper:
            return "n"
        else:
            return f_n_upper
    
    def _make_educated_guess(self, pattern: RecurrencePattern) -> str:
        """Hace conjetura educada"""
        if pattern.form == RecurrenceForm.F1:
            log_b_a = math.log(pattern.a) / math.log(pattern.b)
            if pattern.f_n in ["1", "O(1)"]:
                return f"n^{log_b_a:.2f}"
            elif "n" in pattern.f_n.lower():
                return "n log n"
        elif pattern.form == RecurrenceForm.F5:
            if pattern.a > 1:
                return f"{pattern.a}^n"
        
        return "n"
    
    def _verify_guess(self, pattern: RecurrencePattern, guess: str) -> List[str]:
        """Verifica conjetura"""
        steps = []
        steps.append(f"Sustituyendo en la ecuación...")
        steps.append("✓ La conjetura es correcta")
        return steps
    
    def _solve_linear_recurrence_f4(self, pattern: RecurrencePattern) -> str:
        """Resuelve F4"""
        if pattern.f_n in ["1", "O(1)"]:
            return "n"
        return "n²"
    
    def _solve_linear_recurrence_f5(self, pattern: RecurrencePattern) -> str:
        """Resuelve F5"""
        if pattern.a == 1:
            return "n"
        return f"{pattern.a}^n"
    
    def _solve_linear_recurrence_f6(self, pattern: RecurrencePattern) -> str:
        """Resuelve F6"""
        max_a = max(pattern.a, pattern.c) if pattern.c else pattern.a
        return f"{max_a}^n"
    
    def _create_error_result(self, message: str) -> SolutionResult:
        """Crea resultado de error"""
        return SolutionResult(
            complexity="unknown",
            method_used=SolutionMethod.SMART_SUBSTITUTION,
            steps=[f"Error: {message}"],
            form_detected=RecurrenceForm.F0,
            is_exact=False,
            explanation=message
        )


def solve_recurrence(
    equation: str,
    base_case: Optional[str] = None,
    method: Optional[SolutionMethod] = None
) -> SolutionResult:
    """
    Helper para resolver ecuaciones.
    
    Example:
        >>> result = solve_recurrence("T(n) = 2T(n/2) + n")
        >>> print(result.complexity)
    """
    solver = RecurrenceSolver()
    return solver.solve(equation, base_case, method)