# Módulo Generador de Datasets

Sistema de generación de datasets sintéticos de algoritmos etiquetados, diseñado para facilitar el entrenamiento de modelos de machine learning, validación del sistema de detección de patrones y benchmarking de análisis.

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Componentes](#componentes)
4. [Uso](#uso)
5. [API Reference](#api-reference)
6. [Formatos de Exportación](#formatos-de-exportación)
7. [Ejemplos](#ejemplos)
8. [Testing](#testing)
9. [Integración con el Sistema](#integración-con-el-sistema)

---

## Descripción General

El módulo `dataset_generator` genera colecciones de algoritmos en pseudocódigo con sus complejidades y patrones etiquetados automáticamente. Esto permite construir datasets reproducibles y balanceados sin intervención manual.

### Casos de Uso Principales

| Caso de Uso | Descripción |
|-------------|-------------|
| **Validación de detectores** | Verificar que los detectores de patrones funcionan correctamente con ejemplos controlados |
| **Benchmarking** | Medir el rendimiento y precisión del sistema de análisis |
| **Testing exhaustivo** | Generar variaciones sistemáticas de algoritmos para tests |
| **Entrenamiento ML** | Preparar datasets para futuros modelos de clasificación de algoritmos |

### Funcionalidades

- Generación de variaciones sintéticas sobre plantillas de algoritmos conocidos
- Etiquetado automático de complejidades temporal y espacial
- Creación de datasets balanceados por patrón algorítmico
- Exportación en múltiples formatos para machine learning
- Validación de calidad del dataset generado

---

## Arquitectura

```
dataset_generator/
├── __init__.py                  # Exports principales
├── algorithm_generator.py       # Generador de variaciones de algoritmos
├── complexity_labeler.py        # Etiquetador automático de complejidades
├── synthetic_data_creator.py    # Creador de datasets sintéticos balanceados
└── dataset_exporter.py          # Exportador en múltiples formatos
```

**Archivos principales:**

- [algorithm_generator.py](../dataset_generator/algorithm_generator.py) - Generador de plantillas y variaciones
- [complexity_labeler.py](../dataset_generator/complexity_labeler.py) - Etiquetado automático
- [synthetic_data_creator.py](../dataset_generator/synthetic_data_creator.py) - Orquestador de datasets
- [dataset_exporter.py](../dataset_generator/dataset_exporter.py) - Exportación a formatos ML

**Flujo de datos:**

```
Plantillas de algoritmos
        |
        v
AlgorithmGenerator
(genera variaciones)
        |
        v
ComplexityLabeler
(etiqueta automáticamente)
        |
        v
SyntheticDataCreator
(balancea y organiza)
        |
        v
DatasetExporter
(CSV, JSON, Pickle)
```

---

## Componentes

### 1. AlgorithmGenerator - Generador de Algoritmos

Genera variaciones de algoritmos a partir de plantillas base. Cada plantilla define la estructura lógica de un tipo de algoritmo, y el generador produce variantes con diferentes nombres de variables, tamaños de entrada y constantes.

**Archivo:** [algorithm_generator.py](../dataset_generator/algorithm_generator.py)

**Plantillas predefinidas incluidas:**

| Categoría | Algoritmos |
|-----------|-----------|
| Ordenamiento | Bubble Sort, Insertion Sort, Selection Sort, Quick Sort, Merge Sort |
| Búsqueda | Búsqueda Lineal, Búsqueda Binaria |
| Recursión | Factorial, Fibonacci, Torres de Hanói |
| Divide y Vencerás | Merge Sort, Binary Search, Strassen |
| Programación Dinámica | Knapsack, LCS, Edit Distance, Coin Change |
| Greedy | Prim, Kruskal, Huffman |
| Backtracking | N-Reinas, Sudoku |
| Grafos | BFS, DFS, Dijkstra, Floyd-Warshall |

**Configuración de generación:**

```python
@dataclass
class GenerationConfig:
    num_variations: int = 10       # Variaciones por plantilla
    randomize_names: bool = True   # Aleatorizar nombres de variables
    add_noise: bool = False        # Agregar sentencias irrelevantes
    max_depth: int = 5             # Profundidad máxima de anidación
    min_lines: int = 5             # Mínimo de líneas por algoritmo
    max_lines: int = 50            # Máximo de líneas por algoritmo
```

### 2. ComplexityLabeler - Etiquetador de Complejidades

Analiza cada algoritmo generado y le asigna automáticamente etiquetas de complejidad usando los módulos de análisis del sistema principal.

**Archivo:** [complexity_labeler.py](../dataset_generator/complexity_labeler.py)

**Etiquetas generadas:**

```python
@dataclass
class ComplexityLabel:
    algorithm_name: str
    big_o: str              # Complejidad temporal peor caso
    omega: str              # Complejidad temporal mejor caso
    theta: Optional[str]    # Complejidad ajustada (si existe)
    space_complexity: str   # Complejidad espacial
    pattern: str            # Patrón algorítmico principal
    confidence: float       # Confianza del etiquetado (0.0 a 1.0)
    recurrence: Optional[str]  # Ecuación de recurrencia (si aplica)
```

El etiquetador usa directamente el `AnalyzerEngine` y el `PatternDetector` del sistema, garantizando que las etiquetas sean consistentes con lo que el sistema produce en producción.

Integración con servicios: la generación y exportación de datasets puede integrarse con las utilidades de exportación e infraestructura (por ejemplo, los exportadores en `infrastructure/export/` o el `ExportService` en la capa de servicios) para automatizar la persistencia y distribución de los datasets.

### 3. SyntheticDataCreator - Creador de Datos Sintéticos

Orquesta la generación y balanceo del dataset completo. Se asegura de que cada clase (patrón algorítmico) esté representada con suficientes ejemplos.

**Archivo:** [synthetic_data_creator.py](../dataset_generator/synthetic_data_creator.py)

**Dataset generado:**

```python
@dataclass
class SyntheticDataset:
    entries: List[Dict]         # Lista de registros del dataset
    metadata: Dict[str, Any]    # Metadatos del dataset
    label_distribution: Dict    # Distribución de etiquetas
    generation_config: Dict     # Configuración usada
    created_at: str             # Fecha de creación
    total_samples: int

@dataclass
class DatasetSplit:
    train: SyntheticDataset
    validation: SyntheticDataset
    test: SyntheticDataset
    split_ratios: Dict          # Proporciones usadas (ej: 70/15/15)
```

### 4. DatasetExporter - Exportador de Datasets

Exporta el dataset en formatos compatibles con frameworks de machine learning.

**Archivo:** [dataset_exporter.py](../dataset_generator/dataset_exporter.py)

**Formatos soportados:**

| Formato | Extensión | Uso |
|---------|-----------|-----|
| CSV | .csv | Análisis, pandas, sklearn |
| JSON | .json | APIs, almacenamiento flexible |
| Pickle | .pkl | Python nativo, preserva tipos |
| JSONL | .jsonl | Streaming, datasets grandes |

---

## Uso

### Generación Básica

```python
from dataset_generator import SyntheticDataCreator

creator = SyntheticDataCreator()

# Crear dataset balanceado
dataset = creator.create_balanced_dataset(
    patterns=['divide_conquer', 'dynamic_programming', 'greedy'],
    samples_per_pattern=50
)

print(f"Total de muestras: {dataset.total_samples}")
print(f"Distribución: {dataset.label_distribution}")
```

### Exportación

```python
from dataset_generator import DatasetExporter, ExportFormat

exporter = DatasetExporter()

# Exportar a CSV
exporter.export_to_csv(dataset, 'training_data.csv')

# Exportar a JSON
exporter.export_to_json(dataset, 'training_data.json')

# Helper function
from dataset_generator import export_dataset
export_dataset(dataset, 'data.csv', format=ExportFormat.CSV)
```

### División Train/Validation/Test

```python
from dataset_generator import SyntheticDataCreator

creator = SyntheticDataCreator()
dataset = creator.create_balanced_dataset(
    patterns=['brute_force', 'recursive', 'dynamic_programming'],
    samples_per_pattern=100
)

# Dividir dataset
split = creator.split_dataset(
    dataset,
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15
)

print(f"Train: {split.train.total_samples} muestras")
print(f"Validation: {split.validation.total_samples} muestras")
print(f"Test: {split.test.total_samples} muestras")
```

### Generación de Variaciones

```python
from dataset_generator import AlgorithmGenerator, GenerationConfig

config = GenerationConfig(
    num_variations=20,
    randomize_names=True,
    add_noise=False,
    max_depth=4
)

generator = AlgorithmGenerator(config)
variations = generator.generate_variations('merge_sort')

for i, code in enumerate(variations):
    print(f"Variación {i+1}:")
    print(code[:100])
```

### Etiquetado Manual

```python
from dataset_generator import ComplexityLabeler, label_algorithm

code = """
algorithm bubbleSort(A[n])
begin
    for i <- 1 to n-1 do
        for j <- 1 to n-i do
            if (A[j] > A[j+1]) then
                call swap(A, j, j+1)
            end
        end
    end
end
"""

label = label_algorithm(code)
print(f"Big O: {label.big_o}")
print(f"Patrón: {label.pattern}")
print(f"Confianza: {label.confidence:.2%}")
```

---

## API Reference

### AlgorithmGenerator

```python
class AlgorithmGenerator:
    def __init__(self, config: Optional[GenerationConfig] = None)
    
    def generate_variations(
        self,
        algorithm_name: str,
        count: Optional[int] = None
    ) -> List[str]
    
    def generate_from_template(
        self,
        template: AlgorithmTemplate
    ) -> List[str]
    
    def list_available_templates(self) -> List[str]
    
    def add_template(self, template: AlgorithmTemplate) -> None
```

### ComplexityLabeler

```python
class ComplexityLabeler:
    def label(
        self,
        code: str,
        algorithm_name: Optional[str] = None
    ) -> ComplexityLabel
    
    def label_batch(
        self,
        codes: List[str]
    ) -> List[ComplexityLabel]
    
    def validate_label(
        self,
        code: str,
        expected_label: ComplexityLabel
    ) -> bool
```

### SyntheticDataCreator

```python
class SyntheticDataCreator:
    def create_balanced_dataset(
        self,
        patterns: List[str],
        samples_per_pattern: int = 50
    ) -> SyntheticDataset
    
    def create_full_dataset(
        self,
        total_samples: int = 1000
    ) -> SyntheticDataset
    
    def split_dataset(
        self,
        dataset: SyntheticDataset,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        shuffle: bool = True,
        random_seed: Optional[int] = None
    ) -> DatasetSplit
    
    def validate_dataset(
        self,
        dataset: SyntheticDataset
    ) -> Dict[str, Any]
```

### DatasetExporter

```python
class DatasetExporter:
    def export_to_csv(
        self,
        dataset: SyntheticDataset,
        output_path: str
    ) -> None
    
    def export_to_json(
        self,
        dataset: SyntheticDataset,
        output_path: str
    ) -> None
    
    def export_split(
        self,
        split: DatasetSplit,
        output_dir: str
    ) -> Dict[str, str]
```

### Funciones Helper

```python
# Generar variaciones de un algoritmo
from dataset_generator import generate_algorithm_variations
variations = generate_algorithm_variations('fibonacci', count=10)

# Etiquetar un algoritmo
from dataset_generator import label_algorithm
label = label_algorithm(code)

# Crear dataset balanceado
from dataset_generator import create_balanced_dataset
dataset = create_balanced_dataset(patterns=['brute_force', 'recursive'])

# Exportar dataset
from dataset_generator import export_dataset, ExportFormat
export_dataset(dataset, 'output.json', ExportFormat.JSON)
```

---

## Formatos de Exportación

### Formato CSV

Cada fila es un algoritmo. Las columnas incluyen el código, las etiquetas y metadatos:

```
algorithm_name, code, big_o, omega, theta, space_complexity, pattern, confidence, recurrence
bubbleSort_v1, "algorithm bubbleSort...", O(n^2), Omega(n^2), Theta(n^2), O(1), brute_force, 0.89,
mergeSort_v1, "algorithm mergeSort...", O(n log n), Omega(n log n), Theta(n log n), O(n), divide_and_conquer, 0.95, T(n)=2T(n/2)+O(n)
```

### Formato JSON

Cada entrada es un objeto con toda la información del algoritmo:

```json
{
  "dataset_version": "1.0",
  "created_at": "2025-01-15T10:30:00",
  "total_samples": 500,
  "label_distribution": {
    "brute_force": 100,
    "divide_and_conquer": 100,
    "dynamic_programming": 100,
    "greedy": 100,
    "recursive": 100
  },
  "entries": [
    {
      "id": "entry_001",
      "algorithm_name": "bubbleSort_v1",
      "code": "algorithm bubbleSort(A[n])\nbegin\n...",
      "labels": {
        "big_o": "O(n^2)",
        "omega": "Omega(n^2)",
        "theta": "Theta(n^2)",
        "space_complexity": "O(1)",
        "pattern": "brute_force",
        "confidence": 0.89
      },
      "metadata": {
        "lines_of_code": 12,
        "nesting_depth": 2,
        "has_recursion": false,
        "num_loops": 2
      }
    }
  ]
}
```

---

## Ejemplos

### Ejemplo 1: Dataset para Clasificación de Patrones

```python
from dataset_generator import SyntheticDataCreator, DatasetExporter, ExportFormat

# Crear dataset
creator = SyntheticDataCreator()
dataset = creator.create_balanced_dataset(
    patterns=[
        'brute_force',
        'recursive',
        'divide_and_conquer',
        'dynamic_programming',
        'greedy',
        'backtracking'
    ],
    samples_per_pattern=100
)

print(f"Dataset creado: {dataset.total_samples} muestras")
print(f"Distribución: {dataset.label_distribution}")

# Validar calidad
validation = creator.validate_dataset(dataset)
print(f"Calidad: {validation['quality_score']:.2%}")
print(f"Alertas: {validation['warnings']}")

# Dividir y exportar
split = creator.split_dataset(dataset, random_seed=42)

exporter = DatasetExporter()
paths = exporter.export_split(split, output_dir='data/ml_dataset/')

print(f"Train exportado a: {paths['train']}")
print(f"Validation exportado a: {paths['validation']}")
print(f"Test exportado a: {paths['test']}")
```

### Ejemplo 2: Generación de Variaciones para Testing

```python
from dataset_generator import AlgorithmGenerator, GenerationConfig, ComplexityLabeler

# Configurar generador
config = GenerationConfig(
    num_variations=15,
    randomize_names=True,
    max_depth=3
)
generator = AlgorithmGenerator(config)
labeler = ComplexityLabeler()

# Generar y etiquetar
variations = generator.generate_variations('quick_sort')

for code in variations:
    label = labeler.label(code)
    print(f"Big O: {label.big_o} | Patrón: {label.pattern} | Confianza: {label.confidence:.2%}")
```

---

## Testing

### Ejecutar Tests

```bash
# Tests del módulo dataset_generator
pytest tests/unit/test_dataset_generator.py -v

# Tests en notebooks
jupyter nbconvert --to notebook --execute notebooks/09_dataset_generation/synthetic_algorithms.ipynb
```

### Notebooks Relacionados

| Notebook | Descripción |
|----------|-------------|
| `notebooks/09_dataset_generation/synthetic_algorithms.ipynb` | Generación de algoritmos sintéticos |
| `notebooks/09_dataset_generation/labeling_process.ipynb` | Proceso de etiquetado |
| `notebooks/09_dataset_generation/dataset_validation.ipynb` | Validación del dataset |

---

## Integración con el Sistema

El módulo usa directamente los módulos principales del sistema para garantizar que las etiquetas sean precisas:

```python
from app.core.parser import parse_pseudocode
from app.core.analyzer.analyzer_engine import AnalyzerEngine
from app.core.patterns import PatternDetector

# El labeler usa los mismos módulos que el sistema en producción
class ComplexityLabeler:
    def __init__(self):
        self.engine = AnalyzerEngine()
        self.detector = PatternDetector()
    
    def label(self, code: str) -> ComplexityLabel:
        ast = parse_pseudocode(code)
        complexity = self.engine.analyze(ast)
        patterns = self.detector.detect(ast)
        return ComplexityLabel(...)
```

Esto garantiza que las etiquetas del dataset son exactamente las mismas que el sistema produciría en producción, evitando discrepancias entre el dataset y el comportamiento real.

---

## Próximos Pasos

1. Agregar soporte para algoritmos en Python además de pseudocódigo
2. Implementar generación adversarial de casos límite
3. Integrar con herramientas de data augmentation para ML
4. Agregar métricas de diversidad del dataset
5. Publicar datasets pre-generados para la comunidad

---

## Referencias

- **Scikit-learn:** Para uso del dataset en tareas de clasificación
- **Pandas:** Para manipulación de datasets en formato CSV
- **Módulo de Análisis:** Ver [ANALYZER.md](ANALYZER.md)
- **Módulo de Patrones:** Ver [PATTERNS.md](PATTERNS.md)

---