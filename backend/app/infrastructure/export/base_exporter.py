"""
Base Exporter - Clase base abstracta para todos los exportadores

Define la interfaz común y funcionalidad compartida para exportar
resultados de análisis a diferentes formatos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from app.infrastructure.database.models.mongo.algorithm import Algorithm
from app.infrastructure.database.models.mongo.analysis_result import AnalysisResult
from app.infrastructure.database.models.mongo.pattern_detection import PatternDetection
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ExportFormat(str, Enum):
    """Formatos de exportación disponibles"""
    JSON = "json"
    MARKDOWN = "md"
    PDF = "pdf"
    EXCEL = "xlsx"
    HTML = "html"
    CSV = "csv"
    DOT = "dot"
    MERMAID = "mmd"
    SVG = "svg"

@dataclass
class ExportConfig:
    """
    Configuración para exportación.
    
    Attributes:
        format: Formato de exportación
        output_path: Ruta de salida (opcional)
        include_metadata: Incluir metadatos
        include_code: Incluir código fuente
        include_visualizations: Incluir visualizaciones
        include_statistics: Incluir estadísticas
        pretty_print: Formato legible (JSON, etc.)
        template: Plantilla personalizada (opcional)
        custom_options: Opciones adicionales por formato
    """
    format: ExportFormat
    output_path: Optional[Path] = None
    include_metadata: bool = True
    include_code: bool = True
    include_visualizations: bool = True
    include_statistics: bool = True
    pretty_print: bool = True
    template: Optional[str] = None
    custom_options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validación y conversión de tipos"""
        if isinstance(self.format, str):
            self.format = ExportFormat(self.format)
        
        if self.output_path and not isinstance(self.output_path, Path):
            self.output_path = Path(self.output_path)

@dataclass
class ExportResult:
    """
    Resultado de una operación de exportación.
    
    Attributes:
        success: Si la exportación fue exitosa
        format: Formato exportado
        output_path: Ruta del archivo generado
        file_size: Tamaño del archivo en bytes
        export_time: Tiempo de exportación en segundos
        content: Contenido exportado (si no se guardó en archivo)
        metadata: Metadatos adicionales
        errors: Lista de errores (si hubo)
    """
    success: bool
    format: ExportFormat
    output_path: Optional[Path] = None
    file_size: Optional[int] = None
    export_time: float = 0.0
    content: Optional[Union[str, bytes]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        """Representación en cadena"""
        status = "✓" if self.success else "✗"
        if self.output_path:
            return f"{status} {self.format.value}: {self.output_path} ({self.file_size} bytes)"
        return f"{status} {self.format.value}: in-memory export"

@dataclass
class ExportData:
    """
    Datos completos para exportación.
    
    Agrupa todos los datos necesarios para exportar un análisis completo.
    
    Attributes:
        algorithm: Datos del algoritmo
        analysis: Resultados del análisis
        patterns: Patrones detectados
        visualizations: Datos de visualizaciones (árboles, grafos)
        timestamp: Timestamp de la exportación
    """
    algorithm: Algorithm
    analysis: AnalysisResult
    patterns: Optional[PatternDetection] = None
    visualizations: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte los datos a diccionario para exportación"""
        return {
            "algorithm": {
                "name": self.algorithm.name,
                "code": self.algorithm.code,
                "language": self.algorithm.language,
                "category": self.algorithm.category,
                "tags": self.algorithm.tags,
                "description": self.algorithm.description,
                "author": self.algorithm.author,
            },
            "analysis": {
                "big_o": self.analysis.big_o,
                "omega": self.analysis.omega,
                "theta": self.analysis.theta,
                "space_complexity": self.analysis.space_complexity,
                "temporal_recurrence": self.analysis.temporal_recurrence,
                "spatial_recurrence": self.analysis.spatial_recurrence,
                "line_by_line": self.analysis.line_by_line,
                "analysis_time": self.analysis.analysis_time,
            },
            "patterns": {
                "primary_pattern": self.patterns.primary_pattern,
                "primary_confidence": self.patterns.primary_confidence,
                "patterns_found": self.patterns.patterns_found,
                "structures_found": self.patterns.structures_found,
            } if self.patterns else None,
            "visualizations": self.visualizations,
            "metadata": {
                "export_timestamp": self.timestamp.isoformat(),
                "analyzer_version": self.analysis.analyzer_version,
            }
        }

class BaseExporter(ABC):
    """
    Clase base abstracta para exportadores.
    
    Define la interfaz común que todos los exportadores deben implementar
    y proporciona funcionalidad compartida.
    """
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Inicializa el exportador.
        
        Args:
            config: Configuración de exportación
        """
        self.config = config or ExportConfig(format=self.get_format())
        self.logger = setup_logger(self.__class__.__name__)
        
        self.logger.debug(f"{self.__class__.__name__} inicializado")
    
    @abstractmethod
    def get_format(self) -> ExportFormat:
        """
        Retorna el formato que maneja este exportador.
        
        Returns:
            ExportFormat: Formato del exportador
        """
        pass
    
    @abstractmethod
    def export(self, data: ExportData) -> ExportResult:
        """
        Exporta los datos al formato correspondiente.
        
        Args:
            data: Datos a exportar
            
        Returns:
            ExportResult: Resultado de la exportación
        """
        pass
    
    def validate_data(self, data: ExportData) -> List[str]:
        """
        Valida los datos antes de exportar.
        
        Args:
            data: Datos a validar
            
        Returns:
            List[str]: Lista de errores de validación (vacía si es válido)
        """
        errors = []
        
        if not data.algorithm:
            errors.append("Algoritmo no proporcionado")
        elif not data.algorithm.code:
            errors.append("Código del algoritmo vacío")
        
        if not data.analysis:
            errors.append("Análisis no proporcionado")
        elif not data.analysis.big_o:
            errors.append("Complejidad Big O no calculada")
        
        return errors
    
    def prepare_output_path(self, data: ExportData, suffix: str = "") -> Path:
        """
        Prepara la ruta de salida para el archivo exportado.
        
        Args:
            data: Datos a exportar
            suffix: Sufijo adicional para el nombre (ej: "_summary", "_patterns")
            
        Returns:
            Path: Ruta de salida preparada
        """
        # Obtener extensión del formato
        extension = self.get_format().value
        
        # Mapeo de extensiones a carpetas
        folder_mapping = {
            "md": "markdown",
            "mmd": "mermaid",
            "xlsx": "excel",
            # Otros formatos usan su extensión como nombre de carpeta
        }
        format_folder = folder_mapping.get(extension, extension)
        
        if self.config.output_path:
            output_path = self.config.output_path
            
            # Asegurar que esté en la carpeta correcta del formato
            if output_path.parent.name != format_folder:
                # Reemplazar carpeta padre con la correcta
                output_path = Path("data/exports") / format_folder / output_path.name
            
            # Si hay sufijo, modificar el nombre manteniendo la carpeta
            if suffix:
                stem = output_path.stem
                output_path = output_path.parent / f"{stem}{suffix}.{extension}"
        else:
            # Generar nombre automático sin timestamp
            base_name = data.algorithm.name
            
            # Construir nombre de archivo
            if suffix:
                filename = f"{base_name}{suffix}.{extension}"
            else:
                filename = f"{base_name}.{extension}"
            
            # Crear ruta con subcarpeta del formato
            output_path = Path("data/exports") / format_folder / filename
        
        # Crear directorios si no existen
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def save_to_file(
        self,
        content: Union[str, bytes],
        output_path: Path
    ) -> int:
        """
        Guarda contenido en archivo.
        
        Args:
            content: Contenido a guardar
            output_path: Ruta del archivo
            
        Returns:
            int: Tamaño del archivo en bytes
        """
        mode = "wb" if isinstance(content, bytes) else "w"
        encoding = None if isinstance(content, bytes) else "utf-8"
        
        with open(output_path, mode, encoding=encoding) as f:
            f.write(content)
        
        file_size = output_path.stat().st_size
        self.logger.info(f"Archivo guardado: {output_path} ({file_size} bytes)")
        
        return file_size
    
    def create_result(
        self,
        success: bool,
        output_path: Optional[Path] = None,
        content: Optional[Union[str, bytes]] = None,
        file_size: Optional[int] = None,
        export_time: float = 0.0,
        errors: Optional[List[str]] = None,
        **metadata
    ) -> ExportResult:
        """
        Crea un resultado de exportación.
        
        Args:
            success: Si la exportación fue exitosa
            output_path: Ruta del archivo generado
            content: Contenido exportado
            file_size: Tamaño del archivo
            export_time: Tiempo de exportación
            errors: Lista de errores
            **metadata: Metadatos adicionales
            
        Returns:
            ExportResult: Resultado de la exportación
        """
        return ExportResult(
            success=success,
            format=self.get_format(),
            output_path=output_path,
            file_size=file_size,
            export_time=export_time,
            content=content,
            metadata=metadata,
            errors=errors or []
        )
    
    def format_complexity(self, complexity: Optional[str]) -> str:
        """
        Formatea una expresión de complejidad.
        
        Args:
            complexity: Expresión de complejidad
            
        Returns:
            str: Expresión formateada
        """
        if not complexity:
            return "No calculado"
        return complexity
    
    def format_timestamp(self, timestamp: datetime) -> str:
        """
        Formatea un timestamp.
        
        Args:
            timestamp: Timestamp a formatear
            
        Returns:
            str: Timestamp formateado
        """
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def extract_visualization_data(self, visualizations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae y prepara datos de visualización para exportación.
        
        Args:
            visualizations: Datos de visualización crudos
            
        Returns:
            Dict[str, Any]: Datos preparados
        """
        prepared = {}
        
        # Extraer árbol de recursión si existe
        if "recursion_tree" in visualizations:
            tree = visualizations["recursion_tree"]
            if hasattr(tree, "to_dict"):
                prepared["recursion_tree"] = tree.to_dict()
            else:
                prepared["recursion_tree"] = tree
        
        # Extraer grafo de ejecución si existe
        if "execution_flow" in visualizations:
            flow = visualizations["execution_flow"]
            if hasattr(flow, "to_dict"):
                prepared["execution_flow"] = flow.to_dict()
            else:
                prepared["execution_flow"] = flow
        
        # Otras visualizaciones
        for key, value in visualizations.items():
            if key not in prepared:
                if hasattr(value, "to_dict"):
                    prepared[key] = value.to_dict()
                else:
                    prepared[key] = value
        
        return prepared
    
    def __repr__(self) -> str:
        """Representación del exportador"""
        return f"{self.__class__.__name__}(format={self.get_format().value})"