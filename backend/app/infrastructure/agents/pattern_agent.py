from typing import Dict, Any, Optional

from app.infrastructure.agents.base_agent import BaseAgent, AgentState
from app.infrastructure.llm.base_llm import BaseLLM
from app.core.patterns import PatternDetector
from app.infrastructure.llm.prompt_templates import PATTERN_DETECTION_PROMPT

class PatternAgent(BaseAgent):
    """Agente especializado en detección de patrones"""
    
    def __init__(self, llm: BaseLLM, fallback_llm: Optional[BaseLLM] = None):
        super().__init__(llm, "PatternAgent", fallback_llm=fallback_llm)
        self.detector = PatternDetector()
    
    async def execute(self, state: AgentState) -> AgentState:
        """Detectar patrones algorítmicos"""
        self.log_execution("Iniciando detección de patrones")
        
        if not state.ast:
            self.add_error(state, "No hay AST disponible para detección")
            return state
        
        try:
            # 1. Detección con sistema tradicional
            result = self.detector.detect(state.ast, min_confidence=0.3)
            
            # 2. Guardar resultado
            state.pattern_result = {
                "primary_pattern": result.primary_pattern_name,
                "primary_confidence": result.primary_confidence,
                "all_patterns": [
                    {
                        "name": p.pattern.pattern_name,
                        "confidence": p.final_score,
                        "indicators": [ind.name for ind in p.pattern.indicators_found]
                    }
                    for p in result.all_patterns
                ],
                "summary": result.summary
            }
            
            self.log_execution(f"Patrón detectado: {result.primary_pattern_name} ({result.primary_confidence:.2%})")
            
            # 3. Validación con LLM
            if self.llm:
                llm_detection = await self._detect_with_llm(state)
                state.pattern_result["llm_detection"] = llm_detection
                
                # Comparar
                if llm_detection.get("primary_pattern") != result.primary_pattern_name:
                    self.logger.warning(
                        f"LLM detectó patrón diferente: {llm_detection.get('primary_pattern')}"
                    )
            
            return state
            
        except Exception as e:
            self.add_error(state, f"Error en detección de patrones: {str(e)}")
            return state
    
    async def _detect_with_llm(self, state: AgentState) -> Dict[str, Any]:
        """Detectar patrones con LLM"""
        prompt = PATTERN_DETECTION_PROMPT.format(
            algorithm_code=state.algorithm_code
        )
        
        try:
            return await self.llm.generate_with_fallback(prompt, fallback_llm=self.fallback_llm)
        except Exception as e:
            self.logger.warning(f"Error en detección LLM: {e}")
            return {
                "primary_pattern": state.pattern_result["primary_pattern"],
                "confidence": state.pattern_result["primary_confidence"]
            }