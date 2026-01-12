from typing import Dict, Any

from app.infrastructure.agents.base_agent import BaseAgent, AgentState
from app.infrastructure.llm.base_llm import BaseLLM
from app.core.parser import parse_pseudocode
from app.core.exceptions import ParserException

class ParserAgent(BaseAgent):
    """Agente especializado en parsing de código"""
    
    def __init__(self, llm: BaseLLM):
        super().__init__(llm, "ParserAgent")
    
    async def execute(self, state: AgentState) -> AgentState:
        """Parsear algoritmo y extraer AST"""
        self.log_execution("Iniciando parsing del algoritmo")
        
        try:
            # 1. Parsear código
            ast = parse_pseudocode(state.algorithm_code)
            
            # 2. Actualizar estado
            state.ast = ast
            state.algorithm_name = ast.algorithm.name if ast.algorithm else "unknown"
            
            self.log_execution(f"Parsing exitoso: {state.algorithm_name}")
            
            # 3. Validación con LLM (opcional - para detección de errores sutiles)
            if self.llm:
                validation = await self._validate_with_llm(state.algorithm_code)
                if not validation.get("is_valid", True):
                    self.add_error(state, f"LLM detectó problemas: {validation.get('issues')}")
            
            return state
            
        except ParserException as e:
            self.add_error(state, f"Error de parsing: {e.message}")
            return state
        except Exception as e:
            self.add_error(state, f"Error inesperado en parsing: {str(e)}")
            return state
    
    async def _validate_with_llm(self, code: str) -> Dict[str, Any]:
        """Validar código con LLM"""
        prompt = f"""Analiza el siguiente pseudocódigo y detecta posibles errores sintácticos o semánticos:
```
{code}
```

Responde SOLO en formato JSON:
{{
    "is_valid": true/false,
    "issues": ["lista de problemas detectados"],
    "suggestions": ["sugerencias de corrección"]
}}"""
        
        try:
            return await self.llm.generate_json(prompt)
        except Exception as e:
            self.logger.warning(f"Error en validación LLM: {e}")
            return {"is_valid": True, "issues": [], "suggestions": []}