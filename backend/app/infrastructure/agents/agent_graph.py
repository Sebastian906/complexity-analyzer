from typing import Dict, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

from app.infrastructure.agents.base_agent import AgentState
from app.infrastructure.agents.parser_agent import ParserAgent
from app.infrastructure.agents.complexity_agent import ComplexityAgent
from app.infrastructure.agents.pattern_agent import PatternAgent
from app.infrastructure.agents.validation_agent import ValidationAgent
from app.infrastructure.llm.llm_factory import LLMFactory
from app.utils.logger import get_logger

logger = get_logger(__name__)

class GraphState(TypedDict):
    """Estado del grafo de LangGraph"""
    algorithm_code: str
    algorithm_name: str
    ast: Any
    complexity_result: Dict[str, Any]
    pattern_result: Dict[str, Any]
    validation_result: Dict[str, Any]
    errors: Annotated[list, operator.add]


class AgentGraphOrchestrator:
    """Orquestador usando LangGraph"""
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        
        # LLMs
        if use_llm:
            self.llm = LLMFactory.create_primary()
        else:
            self.llm = None
        
        # Agentes
        self.parser = ParserAgent(None)
        self.complexity = ComplexityAgent(self.llm)
        self.pattern = PatternAgent(self.llm)
        self.validation = ValidationAgent(self.llm)
        
        # Crear grafo
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Crear grafo de ejecución"""
        workflow = StateGraph(GraphState)
        
        # Agregar nodos
        workflow.add_node("parse", self._parse_node)
        workflow.add_node("analyze_complexity", self._complexity_node)
        workflow.add_node("detect_patterns", self._pattern_node)
        workflow.add_node("validate", self._validation_node)
        
        # Definir flujo
        workflow.set_entry_point("parse")
        workflow.add_edge("parse", "analyze_complexity")
        workflow.add_edge("analyze_complexity", "detect_patterns")
        workflow.add_edge("detect_patterns", "validate")
        workflow.add_edge("validate", END)
        
        return workflow.compile()
    
    async def _parse_node(self, state: GraphState) -> GraphState:
        """Nodo de parsing"""
        agent_state = AgentState(algorithm_code=state["algorithm_code"])
        result = await self.parser.execute(agent_state)
        
        return {
            **state,
            "ast": result.ast,
            "algorithm_name": result.algorithm_name,
            "errors": result.errors
        }
    
    async def _complexity_node(self, state: GraphState) -> GraphState:
        """Nodo de análisis de complejidad"""
        agent_state = AgentState(
            algorithm_code=state["algorithm_code"],
            ast=state.get("ast")
        )
        result = await self.complexity.execute(agent_state)
        
        return {
            **state,
            "complexity_result": result.complexity_result,
            "errors": state.get("errors", []) + result.errors
        }
    
    async def _pattern_node(self, state: GraphState) -> GraphState:
        """Nodo de detección de patrones"""
        agent_state = AgentState(
            algorithm_code=state["algorithm_code"],
            ast=state.get("ast")
        )
        result = await self.pattern.execute(agent_state)
        
        return {
            **state,
            "pattern_result": result.pattern_result,
            "errors": state.get("errors", []) + result.errors
        }
    
    async def _validation_node(self, state: GraphState) -> GraphState:
        """Nodo de validación"""
        agent_state = AgentState(
            algorithm_code=state["algorithm_code"],
            algorithm_name=state.get("algorithm_name"),
            complexity_result=state.get("complexity_result"),
            pattern_result=state.get("pattern_result")
        )
        result = await self.validation.execute(agent_state)
        
        return {
            **state,
            "validation_result": result.validation_result,
            "errors": state.get("errors", []) + result.errors
        }
    
    async def execute(self, algorithm_code: str) -> Dict[str, Any]:
        """Ejecutar pipeline con LangGraph"""
        logger.info("Ejecutando pipeline con LangGraph")
        
        # Estado inicial
        initial_state = {
            "algorithm_code": algorithm_code,
            "algorithm_name": "",
            "ast": None,
            "complexity_result": {},
            "pattern_result": {},
            "validation_result": {},
            "errors": []
        }
        
        # Ejecutar grafo
        result = await self.graph.ainvoke(initial_state)
        
        return {
            "success": len(result.get("errors", [])) == 0,
            "algorithm_name": result.get("algorithm_name"),
            "complexity": result.get("complexity_result"),
            "patterns": result.get("pattern_result"),
            "validation": result.get("validation_result"),
            "errors": result.get("errors", [])
        }