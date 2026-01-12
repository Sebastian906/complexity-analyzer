from typing import Dict, Any

from app.infrastructure.agents.base_agent import BaseAgent, AgentState
from app.infrastructure.llm.base_llm import BaseLLM

class ValidationAgent(BaseAgent):
    """Agente especializado en validación final"""
    
    def __init__(self, llm: BaseLLM):
        super().__init__(llm, "ValidationAgent")
    
    async def execute(self, state: AgentState) -> AgentState:
        """Validar resultados completos"""
        self.log_execution("Iniciando validación final")
        
        try:
            # 1. Validar consistencia interna
            consistency = self._validate_consistency(state)
            
            # 2. Validación con LLM
            if self.llm:
                llm_validation = await self._validate_with_llm(state)
            else:
                llm_validation = {"is_valid": True, "issues": []}
            
            # 3. Guardar resultado de validación
            state.validation_result = {
                "internal_consistency": consistency,
                "llm_validation": llm_validation,
                "overall_valid": consistency["is_consistent"] and llm_validation.get("is_valid", True),
                "issues": consistency.get("issues", []) + llm_validation.get("issues", [])
            }
            
            self.log_execution(f"Validación completada: {state.validation_result['overall_valid']}")
            
            return state
            
        except Exception as e:
            self.add_error(state, f"Error en validación: {str(e)}")
            return state
    
    def _validate_consistency(self, state: AgentState) -> Dict[str, Any]:
        """Validar consistencia entre resultados"""
        issues = []
        
        # Verificar que los resultados existan
        if not state.complexity_result:
            issues.append("No hay resultado de análisis de complejidad")
        
        if not state.pattern_result:
            issues.append("No hay resultado de detección de patrones")
        
        # Validar coherencia entre complejidad y patrón
        if state.complexity_result and state.pattern_result:
            big_o = state.complexity_result.get("big_o", "")
            pattern = state.pattern_result.get("primary_pattern", "")
            
            # Ejemplos de incoherencias
            if "O(n²)" in big_o and "divide_and_conquer" in pattern:
                issues.append("Complejidad O(n²) no es típica de Divide y Vencerás")
            
            if "O(2^n)" in big_o and "greedy" in pattern:
                issues.append("Complejidad exponencial no es típica de algoritmos Greedy")
        
        return {
            "is_consistent": len(issues) == 0,
            "issues": issues
        }
    
    async def _validate_with_llm(self, state: AgentState) -> Dict[str, Any]:
        """Validación final con LLM"""
        prompt = f"""Revisa los siguientes resultados de análisis algorítmico y valida su consistencia:

ALGORITMO:
```
{state.algorithm_code}
```

RESULTADOS:
- Nombre: {state.algorithm_name}
- Big O: {state.complexity_result.get("big_o") if state.complexity_result else "N/A"}
- Omega: {state.complexity_result.get("omega") if state.complexity_result else "N/A"}
- Theta: {state.complexity_result.get("theta") if state.complexity_result else "N/A"}
- Patrón: {state.pattern_result.get("primary_pattern") if state.pattern_result else "N/A"}

Responde SOLO en formato JSON:
{{
    "is_valid": true/false,
    "issues": ["lista de inconsistencias o errores detectados"],
    "suggestions": ["sugerencias de corrección"],
    "overall_assessment": "evaluación general"
}}"""
        
        try:
            return await self.llm.generate_json(prompt)
        except Exception as e:
            self.logger.warning(f"Error en validación LLM: {e}")
            return {"is_valid": True, "issues": []}