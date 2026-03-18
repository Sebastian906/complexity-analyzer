"""
PipelineContext — Estado compartido que fluye entre pasos del pipeline.

Reglas de diseño:
- Cada paso SOLO modifica los campos que le pertenecen.
- Nunca pasar parámetros individuales entre pasos: todo va en el contexto.
- Los errores en errors[] son críticos (detienen el pipeline si ast es None).
- Los warnings[] son informativos (el pipeline continúa).
- step_times{} se puebla automáticamente por el motor del pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.schemas.analysis_request import CompleteAnalysisRequest

@dataclass
class PipelineContext:
    """
    Contexto compartido del pipeline de análisis.

    Se crea una instancia por cada llamada a analyze_complete().
    El motor del pipeline lo pasa de paso en paso; cada paso
    modifica solo sus campos y retorna el contexto.
    """

    #  Input — inmutable después de creado                                
    request: CompleteAnalysisRequest

    #  Resultados por paso — se van poblando a medida que avanza          

    # ParseStep
    ast: Optional[Any] = None             
    algorithm_info: Optional[Any] = None  

    # ComplexityStep
    complexity: Optional[Any] = None           
    space_complexity: Optional[Any] = None     
    recurrence_temporal: Optional[Any] = None  
    recurrence_spatial: Optional[Any] = None   
    line_by_line: Optional[Any] = None         

    # PatternStep
    patterns: Optional[Any] = None        

    # StructureStep
    structures: Optional[Any] = None      

    # VisualizationStep (opcional, no incluido en el pipeline base)
    visualizations: list = field(default_factory=list)

    # SummarizeStep
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)

    #  Métricas y control de flujo                                        
    started_at: datetime = field(default_factory=datetime.utcnow)

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Tiempos de ejecución por paso — lo llena el motor, no los pasos
    step_times: dict[str, float] = field(default_factory=dict)

    #  Metadatos de versionado (Paso 4 de la hoja de ruta)               
    pipeline_version: str = "2.0"

    #  Propiedades de control                                             
    @property
    def has_critical_error(self) -> bool:
        """
        El pipeline debe detenerse si el parse falló.

        Criterio: hay errores Y el AST nunca se produjo.
        Solo ParseStep puede causar una parada total porque todos
        los demás pasos dependen del AST.
        """
        return self.ast is None and len(self.errors) > 0

    @property
    def parse_succeeded(self) -> bool:
        """El paso de parsing completó con éxito."""
        return self.ast is not None

    @property
    def algorithm_name(self) -> str:
        """Nombre del algoritmo, con fallback seguro."""
        if self.algorithm_info and hasattr(self.algorithm_info, "name"):
            return self.algorithm_info.name
        return "unknown"