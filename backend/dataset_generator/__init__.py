"""
Dataset Generator Module - Generación de Datasets Sintéticos

Genera datasets de algoritmos etiquetados para:
- Entrenamiento de modelos ML (futuro)
- Validación de detectores de patrones
- Benchmarking de análisis
- Testing exhaustivo

Componentes:
    - AlgorithmGenerator: Genera variaciones sintéticas de algoritmos
    - ComplexityLabeler: Etiqueta automáticamente complejidades
    - SyntheticDataCreator: Crea datos sintéticos balanceados
    - DatasetExporter: Exporta en formatos ML (CSV, JSON, pickle)

Example:
    >>> from dataset_generator import SyntheticDataCreator
    >>> 
    >>> creator = SyntheticDataCreator()
    >>> dataset = creator.create_balanced_dataset(
    ...     patterns=['divide_conquer', 'dynamic_programming'],
    ...     samples_per_pattern=100
    ... )
    >>> 
    >>> # Exportar
    >>> from dataset_generator import DatasetExporter
    >>> exporter = DatasetExporter()
    >>> exporter.export_to_csv(dataset, 'training_data.csv')
"""

from .algorithm_generator import (
    AlgorithmGenerator,
    AlgorithmTemplate,
    GenerationConfig,
    generate_algorithm_variations
)

from .complexity_labeler import (
    ComplexityLabeler,
    ComplexityLabel,
    label_algorithm
)

from .synthetic_data_creator import (
    SyntheticDataCreator,
    SyntheticDataset,
    DatasetSplit,
    create_balanced_dataset
)

from .dataset_exporter import (
    DatasetExporter,
    ExportFormat,
    export_dataset
)

__all__ = [
    # Algorithm Generator
    "AlgorithmGenerator",
    "AlgorithmTemplate",
    "GenerationConfig",
    "generate_algorithm_variations",
    
    # Complexity Labeler
    "ComplexityLabeler",
    "ComplexityLabel",
    "label_algorithm",
    
    # Synthetic Data Creator
    "SyntheticDataCreator",
    "SyntheticDataset",
    "DatasetSplit",
    "create_balanced_dataset",
    
    # Dataset Exporter
    "DatasetExporter",
    "ExportFormat",
    "export_dataset",
]