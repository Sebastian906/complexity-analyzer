from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.infrastructure.llm.base_llm import BaseLLM
from app.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class AgentState:
    """Estado compartido entre agentes"""
    algorithm_code: str
    algorithm_name: Optional[str] = None
    ast: Optional[Any] = None
    complexity_result: Optional[Dict[str, Any]] = None
    pattern_result: Optional[Dict[str, Any]] = None
    structure_result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    errors: list = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class BaseAgent(ABC):
    """Agente base abstracto"""

    def __init__(self, llm: BaseLLM, name: str, fallback_llm: Optional[BaseLLM] = None):
        self.llm = llm
        self.name = name
        self.fallback_llm = fallback_llm
        self.logger = get_logger(f"agent.{name}")

    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """
        Ejecutar lógica del agente.

        Args:
            state: Estado compartido

        Returns:
            AgentState: Estado actualizado
        """
        pass

    def log_execution(self, message: str):
        """Log de ejecución del agente"""
        self.logger.info(f"[{self.name}] {message}")

    def add_error(self, state: AgentState, error: str):
        """Agregar error al estado"""
        state.errors.append({
            "agent": self.name,
            "error": error
        })
        self.logger.error(f"[{self.name}] {error}")