"""
Módulo de Load & Performance Tests para el backend de Complexity Analyzer.

Pruebas de carga y rendimiento que miden tiempos de respuesta, throughput,
escalabilidad, concurrencia y consumo de memoria.

- test_load_performance.py: Pruebas de rendimiento y carga.
    - TestResponseTimes: Tiempos de respuesta individuales (analysis-complete,
      quick, pattern detection, validation, health).
    - TestThroughput: Throughput sostenido (health, analysis, validation con
      múltiples peticiones secuenciales).
    - TestScalability: Escalabilidad del parser y analyzer con anidamiento
      creciente (1 a 10 niveles de for-loops).
    - TestConcurrentLoad: Carga concurrente con ThreadPoolExecutor (health
      checks, análisis y endpoints mixtos en paralelo).
    - TestMemoryPerformance: Detección de fugas de memoria en parser y
      analyzer tras múltiples ejecuciones.

Para ejecutar los load tests:
	pytest tests/load/ -m load
"""
