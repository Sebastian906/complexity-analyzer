"""Parser para respuestas de LLMs"""

import json
import re
from typing import Dict, Any, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

class ResponseParser:
    """Parser de respuestas JSON de LLMs"""
    
    @staticmethod
    def parse_json(content: str) -> Optional[Dict[str, Any]]:
        """
        Parsea contenido JSON, manejando casos especiales.
        
        Args:
            content: Contenido crudo del LLM
        
        Returns:
            Dict parseado o None si falla
        """
        # Limpiar contenido
        cleaned = ResponseParser._clean_json_content(content)
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            logger.debug(f"Contenido: {cleaned[:500]}")
            return None
    
    @staticmethod
    def _clean_json_content(content: str) -> str:
        """Limpia contenido JSON"""
        # Remover markdown code blocks
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Remover espacios y saltos de línea innecesarios
        content = content.strip()
        
        return content
    
    @staticmethod
    def validate_complexity_response(data: Dict[str, Any]) -> bool:
        """Valida respuesta de análisis de complejidad"""
        required_fields = ["big_o", "omega", "matches_our_analysis"]
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_pattern_response(data: Dict[str, Any]) -> bool:
        """Valida respuesta de detección de patrones"""
        required_fields = ["primary_pattern", "confidence"]
        return all(field in data for field in required_fields)