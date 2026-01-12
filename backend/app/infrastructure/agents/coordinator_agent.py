from typing import Dict, Any, Optional

from app.infrastructure.agents.base_agent import BaseAgent, AgentState
from app.infrastructure.agents.parser_agent import ParserAgent
from app.infrastructure.agents.complexity_agent import ComplexityAgent
from app.infrastructure.agents.pattern_agent import PatternAgent
from app.infrastructure.agents.validation_agent import ValidationAgent
from app.infrastructure.llm.llm_factory import LLMFactory
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CoordinatorAgent:
    """Coordinador del sistema multiagente"""
    
    def __init__(self, use_llm: bool = True):
        """
        Inicializar coordinador.
        
        Args:
            use_llm: Si usar LLMs para validación adicional
        """
        self.use_llm = use_llm
        
        # Crear LLMs si está habilitado
        if use_llm:
            self.primary_llm = LLMFactory.create_primary()
            self.fallback_llm = LLMFactory.create_fallback()
        else:
            self.primary_llm = None
            self.fallback_llm = None
        
        # Inicializar agentes
        self.parser_agent = ParserAgent(None)  # Parser no necesita LLM
        self.complexity_agent = ComplexityAgent(self.primary_llm)
        self.pattern_agent = PatternAgent(self.primary_llm)
        self.validation_agent = ValidationAgent(self.primary_llm)
    
    async def execute_pipeline(self, algorithm_code: str) -> Dict[str, Any]:
        """
        Ejecutar pipeline completo de análisis.
        
        Args:
            algorithm_code: Código del algoritmo
        
        Returns:
            Dict con todos los resultados
        """
        logger.info("Iniciando pipeline multiagente")
        
        # 1. Crear estado inicial
        state = AgentState(algorithm_code=algorithm_code)
        
        # 2. Ejecutar agentes en secuencia
        try:
            # Parser
            state = await self.parser_agent.execute(state)
            if state.errors:
                logger.error("Errores en parsing, deteniendo pipeline")
                return self._format_error_response(state)
            
            # Complexity
            state = await self.complexity_agent.execute(state)
            
            # Patterns
            state = await self.pattern_agent.execute(state)
            
            # Validation
            state = await self.validation_agent.execute(state)
            
            # 3. Formatear resultado final
            return self._format_success_response(state)
            
        except Exception as e:
            logger.error(f"Error en pipeline: {e}")
            state.errors.append({"agent": "coordinator", "error": str(e)})
            return self._format_error_response(state)
    
    def _format_success_response(self, state: AgentState) -> Dict[str, Any]:
        """Formatear respuesta exitosa"""
        return {
            "success": True,
            "algorithm_name": state.algorithm_name,
            "complexity": state.complexity_result,
            "patterns": state.pattern_result,
            "validation": state.validation_result,
            "errors": state.errors,
            "metadata": {
                "use_llm": self.use_llm,
                "primary_llm": self.primary_llm.model if self.primary_llm else None,
            }
        }
    
    def _format_error_response(self, state: AgentState) -> Dict[str, Any]:
        """Formatear respuesta con errores"""
        return {
            "success": False,
            "algorithm_name": state.algorithm_name,
            "errors": state.errors,
            "partial_results": {
                "complexity": state.complexity_result,
                "patterns": state.pattern_result,
                "validation": state.validation_result,
            }
        }