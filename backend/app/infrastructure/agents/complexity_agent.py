from typing import Dict, Any

from app.infrastructure.agents.base_agent import BaseAgent, AgentState
from app.infrastructure.llm.base_llm import BaseLLM
from app.core.analyzer.analyzer_engine import AnalyzerEngine
from app.infrastructure.llm.prompt_templates import COMPLEXITY_VALIDATION_PROMPT

class ComplexityAgent(BaseAgent):
    """Agente especializado en análisis de complejidad"""
    
    def __init__(self, llm: BaseLLM):
        super().__init__(llm, "ComplexityAgent")
        self.analyzer = AnalyzerEngine()
    
    async def execute(self, state: AgentState) -> AgentState:
        """Analizar complejidad del algoritmo"""
        self.log_execution("Iniciando análisis de complejidad")
        
        if not state.ast:
            self.add_error(state, "No hay AST disponible para análisis")
            return state
        
        try:
            # 1. Análisis con el motor tradicional
            result = self.analyzer.analyze(
                state.ast,
                analyze_line_by_line=True
            )
            
            # 2. Guardar resultado
            state.complexity_result = {
                "big_o": result.big_o,
                "omega": result.omega,
                "theta": result.theta,
                "space_complexity": result.space_complexity,
                "temporal_recurrence": result.temporal_recurrence,
                "spatial_recurrence": result.spatial_recurrence,
                "line_by_line": result.line_by_line.to_dict() if result.line_by_line else None,
                "metadata": result.metadata,
            }
            
            self.log_execution(f"Análisis completado: {result.big_o}")
            
            # 3. Validación con LLM
            if self.llm:
                llm_validation = await self._validate_with_llm(state)
                state.complexity_result["llm_validation"] = llm_validation
                
                # Comparar resultados
                if not llm_validation.get("matches_our_analysis", True):
                    self.logger.warning("LLM no concuerda con nuestro análisis")
            
            return state
            
        except Exception as e:
            self.add_error(state, f"Error en análisis de complejidad: {str(e)}")
            return state

    async def _validate_with_llm(self, state: AgentState) -> Dict[str, Any]:
        """Validar análisis con LLM"""
        prompt = COMPLEXITY_VALIDATION_PROMPT.format(
            algorithm_code=state.algorithm_code,
            big_o=state.complexity_result["big_o"],
            omega=state.complexity_result["omega"],
            theta=state.complexity_result.get("theta", "N/A")
        )

        try:
            return await self.llm.generate_json(prompt)
        except Exception as e:
            self.logger.warning(f"Error en validación LLM: {e}")
            return {
                "big_o": state.complexity_result["big_o"],
                "matches_our_analysis": True,
                "errors": [],
                "warnings": []
            }