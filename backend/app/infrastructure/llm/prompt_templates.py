"""Templates de prompts para LLMs"""

COMPLEXITY_VALIDATION_PROMPT = """Eres un experto en análisis de algoritmos. Analiza el siguiente pseudocódigo y determina su complejidad temporal.

PSEUDOCÓDIGO:
```
{algorithm_code}
```

NUESTRO ANÁLISIS:
- Mejor caso (Ω): {omega}
- Peor caso (O): {big_o}
- Caso promedio (Θ): {theta}

INSTRUCCIONES:
1. Analiza el algoritmo línea por línea
2. Determina la complejidad en cada notación (O, Ω, Θ)
3. Compara con nuestro análisis
4. Indica si hay errores o advertencias

Responde SOLO en formato JSON sin markdown:
{{
    "big_o": "...",
    "omega": "...",
    "theta": "...",
    "matches_our_analysis": true/false,
    "errors": ["..."],
    "warnings": ["..."],
    "reasoning": "..."
}}"""

PATTERN_DETECTION_PROMPT = """Analiza el siguiente pseudocódigo e identifica las técnicas algorítmicas utilizadas (Divide y Conquista, Programación Dinámica, Greedy, Backtracking, etc.)

PSEUDOCÓDIGO:
```
{algorithm_code}
```

Responde SOLO en formato JSON sin markdown:
{{
    "primary_pattern": "nombre del patrón principal",
    "confidence": 0.0-1.0,
    "secondary_patterns": ["patrón1", "patrón2"],
    "indicators": ["indicador1", "indicador2"],
    "reasoning": "explicación detallada"
}}"""

STRUCTURE_DETECTION_PROMPT = """Identifica las estructuras de datos utilizadas en el siguiente algoritmo:

PSEUDOCÓDIGO:
```
{algorithm_code}
```

Responde SOLO en formato JSON sin markdown:
{{
    "primary_structure": "nombre de estructura principal",
    "all_structures": ["estructura1", "estructura2"],
    "operations": ["operación1", "operación2"],
    "reasoning": "explicación"
}}"""