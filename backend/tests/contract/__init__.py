"""
Módulo de Contract Tests para el backend de Complexity Analyzer.

Valida que los contratos (schemas) de respuesta de cada endpoint de la API
se mantienen estables. Si un campo cambia de nombre, tipo o desaparece,
estos tests fallarán.

- test_api_contracts.py: Contratos de respuesta para todos los endpoints.
    - TestHealthContract: Contrato del endpoint /health.
    - TestRootContract: Contrato del endpoint raíz /.
    - TestAnalysisCompleteContract: Contrato de /api/v1/analysis/analyze-complete.
    - TestQuickAnalysisContract: Contrato de /api/v1/analysis/quick.
    - TestPatternDetectionContract: Contrato de /api/v1/patterns/detect.
    - TestStructureDetectionContract: Contrato de /api/v1/structures/detect.
    - TestValidationContract: Contrato de /api/v1/validation/validate.
    - TestExportContract: Contrato de /api/v1/export.

Para ejecutar los contract tests:
	pytest tests/contract/ -m contract
"""
