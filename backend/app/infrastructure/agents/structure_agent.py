from typing import Any, Dict

from app.infrastructure.agents.base_agent import BaseAgent, AgentState
from app.core.data_structures import StructureIdentifier
from app.utils.logger import get_logger

logger = get_logger(__name__)

class StructureAgent(BaseAgent):
    """Agente especializado en detección de estructuras de datos"""
    
    def __init__(self):
        super().__init__(llm=None, name="StructureAgent")
        self.identifier = StructureIdentifier()

    async def execute(self, state: AgentState) -> AgentState:
        """Detectar estructuras de datos usadas en el algoritmo"""
        self.log_execution('Iniciando detección de estructuras de datos')

        if not state.ast:
            self.add_error(state, 'No hay AST disponible para detección de estructuras de datos')
            return state
        
        try:
            result = self.identifier.identify(state.ast)

            state.structure_result = {
                'primary_structure': result.primary_structure.value if result.primary_structure else None,
                'all_structures': [
                    {
                        'type': m.structure_type.value,
                        'confidence': m.confidence,
                        'indicators': [i.name for i in m.indicators_found]
                    }
                    for m in result.all_structures
                ],
                'summary': result.summary if hasattr(result, 'summary') else '',
            }

            self.log_execution(
                f'Estructuras detectadas: {state.structure_result['primary_structure']}'
            )
            return state

        except Exception as e:
            self.add_error(state, f'Error en detección de estructuras de datos: {str(e)}')
            return state