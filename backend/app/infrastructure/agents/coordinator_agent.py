from typing import Dict, Any, Optional

from app.infrastructure.agents.agent_graph import AgentGraphOrchestrator
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
        primary_llm = LLMFactory.create_primary() if use_llm else None
        fallback_llm = LLMFactory.create_fallback() if use_llm else None
        
        # Inicializar agentes
        self.orchestrator = AgentGraphOrchestrator(
            use_llm=use_llm,
            primary_llm=primary_llm,
            fallback_llm=fallback_llm
        )
    
    async def execute_pipeline(self, algorithm_code: str) -> Dict[str, Any]:
        """
        Ejecutar pipeline completo de análisis.
        
        Args:
            algorithm_code: Código del algoritmo
        
        Returns:
            Dict con todos los resultados
        """
        logger.info("Iniciando pipeline multiagente")
        return await self.orchestrator.execute(algorithm_code)
    
    # def _format_success_response(self, state: AgentState) -> Dict[str, Any]:
    #     """Formatear respuesta exitosa"""
    #     return {
    #         "success": True,
    #         "algorithm_name": state.algorithm_name,
    #         "complexity": state.complexity_result,
    #         "patterns": state.pattern_result,
    #         "validation": state.validation_result,
    #         "errors": state.errors,
    #         "metadata": {
    #             "use_llm": self.use_llm,
    #             "primary_llm": self.primary_llm.model if self.primary_llm else None,
    #         }
    #     }
    
    # def _format_error_response(self, state: AgentState) -> Dict[str, Any]:
    #     """Formatear respuesta con errores"""
    #     return {
    #         "success": False,
    #         "algorithm_name": state.algorithm_name,
    #         "errors": state.errors,
    #         "partial_results": {
    #             "complexity": state.complexity_result,
    #             "patterns": state.pattern_result,
    #             "validation": state.validation_result,
    #         }
    #     }