"""
Excepciones Personalizadas del Sistema

Define todas las excepciones custom para manejo de errores específicos.
"""

from typing import Any, Dict, Optional

class ComplexityAnalyzerException(Exception):
    """
    Excepción base para todas las excepciones del sistema.
    
    Attributes:
        message: Mensaje de error
        details: Detalles adicionales del error
        error_code: Código de error interno
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la excepción a diccionario"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "error_code": self.error_code,
        }

# Excepciones del Parser

class ParserException(ComplexityAnalyzerException):
    """Excepción base para errores del parser"""
    pass

class SyntaxErrorException(ParserException):
    """Error de sintaxis en el pseudocódigo"""
    
    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        expected: Optional[str] = None,
        got: Optional[str] = None
    ):
        details = {}
        if line is not None:
            details["line"] = line
        if column is not None:
            details["column"] = column
        if expected:
            details["expected"] = expected
        if got:
            details["got"] = got
        
        super().__init__(
            message=f"Error de sintaxis: {message}",
            details=details,
            error_code="SYNTAX_ERROR"
        )

class SemanticErrorException(ParserException):
    """Error semántico en el algoritmo"""
    
    def __init__(self, message: str, context: Optional[str] = None):
        details = {"context": context} if context else {}
        super().__init__(
            message=f"Error semántico: {message}",
            details=details,
            error_code="SEMANTIC_ERROR"
        )

class TokenizationException(ParserException):
    """Error durante la tokenización"""
    
    def __init__(self, message: str, position: Optional[int] = None):
        details = {"position": position} if position else {}
        super().__init__(
            message=f"Error de tokenización: {message}",
            details=details,
            error_code="TOKENIZATION_ERROR"
        )

class ASTBuildException(ParserException):
    """Error durante la construcción del AST"""
    
    def __init__(self, message: str, node_type: Optional[str] = None):
        details = {"node_type": node_type} if node_type else {}
        super().__init__(
            message=f"Error construyendo AST: {message}",
            details=details,
            error_code="AST_BUILD_ERROR"
        )

# Excepciones del Analizador

class AnalyzerException(ComplexityAnalyzerException):
    """Excepción base para errores del analizador"""
    pass

class ComplexityAnalysisException(AnalyzerException):
    """Error durante el análisis de complejidad"""
    
    def __init__(self, message: str, analysis_type: Optional[str] = None):
        details = {"analysis_type": analysis_type} if analysis_type else {}
        super().__init__(
            message=f"Error en análisis de complejidad: {message}",
            details=details,
            error_code="COMPLEXITY_ANALYSIS_ERROR"
        )

class RecurrenceException(AnalyzerException):
    """Error en el análisis de recurrencia"""
    
    def __init__(self, message: str, equation: Optional[str] = None):
        details = {"equation": equation} if equation else {}
        super().__init__(
            message=f"Error en ecuación de recurrencia: {message}",
            details=details,
            error_code="RECURRENCE_ERROR"
        )

class TimeoutException(AnalyzerException):
    """El análisis excedió el tiempo límite"""
    
    def __init__(self, timeout_seconds: int, operation: Optional[str] = None):
        super().__init__(
            message=f"Operación excedió el tiempo límite de {timeout_seconds}s",
            details={"timeout": timeout_seconds, "operation": operation},
            error_code="TIMEOUT_ERROR"
        )

class MaxDepthExceededException(AnalyzerException):
    """Se excedió la profundidad máxima de análisis"""
    
    def __init__(self, max_depth: int, current_depth: int):
        super().__init__(
            message=f"Se excedió la profundidad máxima ({max_depth})",
            details={"max_depth": max_depth, "current_depth": current_depth},
            error_code="MAX_DEPTH_EXCEEDED"
        )

# Excepciones de Patrones

class PatternDetectionException(ComplexityAnalyzerException):
    """Error durante la detección de patrones"""
    
    def __init__(self, message: str, pattern_type: Optional[str] = None):
        details = {"pattern_type": pattern_type} if pattern_type else {}
        super().__init__(
            message=f"Error detectando patrón: {message}",
            details=details,
            error_code="PATTERN_DETECTION_ERROR"
        )

# Excepciones de LLM

class LLMException(ComplexityAnalyzerException):
    """Excepción base para errores de LLM"""
    pass

class LLMAPIException(LLMException):
    """Error al comunicarse con la API del LLM"""
    
    def __init__(
        self,
        message: str,
        llm_provider: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        details = {}
        if llm_provider:
            details["provider"] = llm_provider
        if status_code:
            details["status_code"] = status_code
        
        super().__init__(
            message=f"Error de API LLM: {message}",
            details=details,
            error_code="LLM_API_ERROR"
        )

class LLMResponseParseException(LLMException):
    """Error al parsear la respuesta del LLM"""
    
    def __init__(self, message: str, raw_response: Optional[str] = None):
        details = {}
        if raw_response and len(raw_response) < 500:
            details["raw_response"] = raw_response
        
        super().__init__(
            message=f"Error parseando respuesta LLM: {message}",
            details=details,
            error_code="LLM_PARSE_ERROR"
        )

class LLMValidationException(LLMException):
    """Error durante la validación con LLM"""
    
    def __init__(self, message: str, validation_type: Optional[str] = None):
        details = {"validation_type": validation_type} if validation_type else {}
        super().__init__(
            message=f"Error en validación LLM: {message}",
            details=details,
            error_code="LLM_VALIDATION_ERROR"
        )

# Excepciones de Base de Datos

class DatabaseException(ComplexityAnalyzerException):
    """Excepción base para errores de base de datos"""
    pass

class DatabaseConnectionException(DatabaseException):
    """Error de conexión a la base de datos"""
    
    def __init__(self, message: str, database_type: Optional[str] = None):
        details = {"database_type": database_type} if database_type else {}
        super().__init__(
            message=f"Error de conexión a BD: {message}",
            details=details,
            error_code="DB_CONNECTION_ERROR"
        )

class DatabaseQueryException(DatabaseException):
    """Error al ejecutar query en la base de datos"""
    
    def __init__(self, message: str, query: Optional[str] = None):
        details = {}
        if query and len(query) < 200:
            details["query"] = query
        
        super().__init__(
            message=f"Error en query: {message}",
            details=details,
            error_code="DB_QUERY_ERROR"
        )

class DocumentNotFoundException(DatabaseException):
    """Documento no encontrado en la base de datos"""
    
    def __init__(self, document_id: str, collection: Optional[str] = None):
        details = {"document_id": document_id}
        if collection:
            details["collection"] = collection
        
        super().__init__(
            message=f"Documento no encontrado: {document_id}",
            details=details,
            error_code="DOCUMENT_NOT_FOUND"
        )

# Excepciones de Caché

class CacheException(ComplexityAnalyzerException):
    """Excepción base para errores de caché"""
    pass

class CacheConnectionException(CacheException):
    """Error de conexión al sistema de caché"""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"Error de conexión a caché: {message}",
            error_code="CACHE_CONNECTION_ERROR"
        )

# Excepciones de Visualización

class VisualizationException(ComplexityAnalyzerException):
    """Error durante la generación de visualizaciones"""
    
    def __init__(self, message: str, visualization_type: Optional[str] = None):
        details = {"type": visualization_type} if visualization_type else {}
        super().__init__(
            message=f"Error generando visualización: {message}",
            details=details,
            error_code="VISUALIZATION_ERROR"
        )

# Excepciones de Exportación

class ExportException(ComplexityAnalyzerException):
    """Excepción base para errores de exportación"""
    pass

class ExportFormatException(ExportException):
    """Formato de exportación no soportado o inválido"""
    
    def __init__(self, format_name: str, supported_formats: Optional[list] = None):
        details = {"format": format_name}
        if supported_formats:
            details["supported_formats"] = supported_formats
        
        super().__init__(
            message=f"Formato de exportación inválido: {format_name}",
            details=details,
            error_code="EXPORT_FORMAT_ERROR"
        )

class ExportGenerationException(ExportException):
    """Error durante la generación del archivo de exportación"""
    
    def __init__(self, message: str, export_format: Optional[str] = None):
        details = {"format": export_format} if export_format else {}
        super().__init__(
            message=f"Error generando exportación: {message}",
            details=details,
            error_code="EXPORT_GENERATION_ERROR"
        )

# Excepciones de Validación

class ValidationException(ComplexityAnalyzerException):
    """Error de validación de datos"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=f"Error de validación: {message}",
            details=details,
            error_code="VALIDATION_ERROR"
        )

class AlgorithmTooLargeException(ValidationException):
    """El algoritmo excede el tamaño máximo permitido"""
    
    def __init__(self, size: int, max_size: int):
        super().__init__(
            message=f"Algoritmo demasiado grande ({size} > {max_size})",
            field="algorithm_code"
        )
        self.details["size"] = size
        self.details["max_size"] = max_size
        self.error_code = "ALGORITHM_TOO_LARGE"

# Excepciones de Autenticación/Autorización

class AuthenticationException(ComplexityAnalyzerException):
    """Error de autenticación"""
    
    def __init__(self, message: str = "No autorizado"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR"
        )

class RateLimitException(ComplexityAnalyzerException):
    """Se excedió el límite de requests"""
    
    def __init__(self, limit: int, window: str):
        super().__init__(
            message=f"Se excedió el límite de {limit} requests por {window}",
            details={"limit": limit, "window": window},
            error_code="RATE_LIMIT_EXCEEDED"
        )