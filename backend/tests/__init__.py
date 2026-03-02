"""
Tests package initialization.

Permite imports relativos entre subcarpetas de tests.

Incluye los siguientes módulos de pruebas:

- unit/: Tests unitarios para componentes individuales del sistema.
- integration/: Tests de integración entre módulos y endpoints de la API.
- e2e/: Tests end-to-end de flujos completos del sistema.
- contract/: Contract Testing - Valida contratos de respuesta de la API.
- smoke/: Smoke Testing - Verificación rápida de que la app arranca y responde.
- whitebox/: White Box Testing - Cobertura de ramas internas del código fuente.
- blackbox/: Black Box Testing - Partición de equivalencia, valores frontera y tablas de decisión.
- load/: Load & Performance Testing - Tiempos de respuesta, throughput y concurrencia.
- regression/: Regression Testing - Fijación de resultados conocidos para algoritmos canónicos.
- fixtures/: Datos y fixtures compartidos entre módulos de pruebas.

Para ejecutar todos los tests:
	pytest tests/
"""