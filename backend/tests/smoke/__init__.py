"""
Módulo de Smoke Tests para el backend de Complexity Analyzer.

Verificación rápida de que la aplicación arranca correctamente, los módulos
principales se importan sin error y los endpoints responden con códigos HTTP
esperados.

- test_smoke.py: Pruebas de humo para arranque, imports y endpoints.
    - TestAppSmoke: La app arranca, responde en / y /health, esquema OpenAPI disponible.
    - TestModulesSmoke: Imports de parser, analyzer, patterns, structures, visualization,
      services, schemas, config, exceptions y profiling.
    - TestEndpointsSmoke: Todos los endpoints responden (analysis, patterns, structures,
      validation, export, visualization).
    - TestParserSmoke: El parser parsea algoritmos simples correctamente.
    - TestAnalyzerSmoke: El analyzer analiza código y produce resultados válidos.

Para ejecutar los smoke tests:
	pytest tests/smoke/ -m smoke
"""
