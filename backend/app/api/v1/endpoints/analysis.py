"""
API Endpoints - Análisis de Complejidad

Endpoints REST para analizar algoritmos y obtener su complejidad.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.parser import PseudocodeParser
from app.core.analyzer.analyzer_engine import AnalyzerEngine
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

class AnalysisRequest(BaseModel):
    """Request para análisis de complejidad"""
    code: str = Field(..., description="Código del algoritmo")
    analyze_temporal: bool = Field(True, description="Analizar complejidad temporal")
    analyze_spatial: bool = Field(True, description="Analizar complejidad espacial")
    analyze_line_by_line: bool = Field(True, description="Análisis línea por línea")

class AnalysisResponse(BaseModel):
    """Response del análisis"""
    success: bool
    algorithm_name: str
    big_o: str
    omega: str
    theta: str
    line_by_line: dict = None
    metadata: dict = None
    message: str

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analizar Complejidad",
    description="Analiza la complejidad temporal de un algoritmo"
)
async def analyze_complexity(request: AnalysisRequest):
    """Analiza la complejidad de un algoritmo"""
    try:
        logger.info("Recibida solicitud de análisis")
        
        # 1. Parsear el código
        parser = PseudocodeParser()
        ast = parser.parse(request.code)
        
        logger.info(f"Código parseado: {ast.algorithm.name}")
        
        # 2. Analizar con el motor principal
        engine = AnalyzerEngine()
        result = engine.analyze(
            ast,
            analyze_line_by_line=request.analyze_line_by_line
        )
        
        # 3. Convertir a dict
        result_dict = result.to_dict()
        
        return AnalysisResponse(
            success=True,
            algorithm_name=result.algorithm_name,
            big_o=result.big_o,
            omega=result.omega,
            theta=result.theta,
            line_by_line=result_dict.get("line_by_line"),
            metadata=result_dict.get("metadata"),
            message="Análisis completado exitosamente"
        )
    
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AnalysisError",
                "message": str(e)
            }
        )