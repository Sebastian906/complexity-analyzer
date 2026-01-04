# Jupyter Notebooks - Complexity Analyzer

Este directorio contiene notebooks interactivos para explorar, probar y documentar las funcionalidades del Analizador de Complejidades.

## Estructura

```
notebooks/
├── 01_exploratory/           # Exploración y pruebas del parser
│   ├── parser_testing.ipynb
│   ├── ast_visualization.ipynb
│   └── grammar_experiments.ipynb
├── 02_complexity_analysis/   # Análisis de complejidad
│   ├── big_o_examples.ipynb
│   ├── recurrence_solver.ipynb
│   └── complexity_comparison.ipynb
├── 03_pattern_detection/     # Detección de patrones
│   ├── pattern_signatures.ipynb
│   ├── scoring_calibration.ipynb
│   └── pattern_evaluation.ipynb
```

## Cómo Usar

### Requisitos Previos

```bash
# Instalar Jupyter
pip install jupyter jupyterlab

# Instalar el proyecto en modo desarrollo
cd backend
pip install -e .
```

### Ejecutar Notebooks

```bash
# Opción 1: Jupyter Lab (recomendado)
jupyter lab

# Opción 2: Jupyter Notebook clásico
jupyter notebook

# Opción 3: VS Code
# Abrir el archivo .ipynb directamente en VS Code
```

## Descripción de Notebooks

### 01_exploratory/
- **parser_testing.ipynb**: Pruebas interactivas del parser de pseudocódigo
- **ast_visualization.ipynb**: Visualización de árboles sintácticos
- **grammar_experiments.ipynb**: Experimentos con la gramática Lark

### 02_complexity_analysis/
- **big_o_examples.ipynb**: Ejemplos de análisis Big O, Omega y Theta
- **recurrence_solver.ipynb**: Resolución de ecuaciones de recurrencia
- **complexity_comparison.ipynb**: Comparación de complejidades

### 03_pattern_detection/
- **pattern_signatures.ipynb**: Firmas de patrones algorítmicos
- **scoring_calibration.ipynb**: Calibración del sistema de scoring
- **pattern_evaluation.ipynb**: Evaluación de detección de patrones

## Configuración del Kernel

Para que los notebooks funcionen correctamente, asegúrate de que el kernel de Python tenga acceso al módulo `app`:

```python
import sys
sys.path.insert(0, '../')  # Añadir el directorio backend al path
```

## Convenciones

1. Cada notebook debe ser autocontenido (se puede ejecutar de inicio a fin)
2. Incluir celdas markdown explicativas
3. Limpiar outputs antes de hacer commit
4. Usar nombres descriptivos para variables