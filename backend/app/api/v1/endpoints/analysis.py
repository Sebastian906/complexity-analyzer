"""
API Endpoints - Análisis de Complejidad

Endpoints REST para analizar algoritmos y obtener su complejidad.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request para análisis de complejidad"""
    code: str = Field(..., description="Código del algoritmo")
    analyze_temporal: bool = Field(True, description="Analizar complejidad temporal")
    analyze_spatial: bool = Field(True, description="Analizar complejidad espacial")


class AnalysisResponse(BaseModel):
    """Response del análisis (placeholder)"""
    success: bool
    algorithm_name: str
    big_o: str = "TBD"
    omega: str = "TBD"
    theta: str = "TBD"
    message: str


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analizar Complejidad",
    description="Analiza la complejidad de un algoritmo"
)
async def analyze_complexity(request: AnalysisRequest):
    """
    Placeholder para análisis de complejidad.
    
    Este endpoint se implementará en el MÓDULO 2.
    """
    return AnalysisResponse(
        success=False,
        algorithm_name="unknown",
        message="MÓDULO 2 (Análisis de Complejidad) aún no implementado"
    )