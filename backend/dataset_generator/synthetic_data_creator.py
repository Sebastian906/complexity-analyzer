"""
Synthetic Data Creator - Creador de Datasets Sintéticos Balanceados

Crea datasets balanceados para:
- Training de modelos ML
- Validación de detectores
- Benchmarking
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

from dataset_generator.algorithm_generator import (
    AlgorithmGenerator,
    AlgorithmTemplate,
    GenerationConfig
)
from dataset_generator.complexity_labeler import ComplexityLabeler, ComplexityLabel

class DatasetSplit(str, Enum):
    """Tipos de splits para datasets"""
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"

@dataclass
class SyntheticSample:
    """Muestra individual del dataset"""
    algorithm_name: str
    code: str
    category: str
    label: ComplexityLabel
    split: DatasetSplit
    metadata: Dict = field(default_factory=dict)

@dataclass
class SyntheticDataset:
    """Dataset sintético completo"""
    samples: List[SyntheticSample]
    metadata: Dict = field(default_factory=dict)
    
    def __len__(self) -> int:
        """Número total de muestras"""
        return len(self.samples)
    
    def get_split(self, split: DatasetSplit) -> List[SyntheticSample]:
        """
        Obtiene muestras de un split específico
        
        Args:
            split: Split deseado
        
        Returns:
            Lista de muestras del split
        """
        return [s for s in self.samples if s.split == split]
    
    def get_by_pattern(self, pattern: str) -> List[SyntheticSample]:
        """
        Obtiene muestras de un patrón específico
        
        Args:
            pattern: Patrón algorítmico
        
        Returns:
            Lista de muestras del patrón
        """
        return [s for s in self.samples if s.label.primary_pattern == pattern]
    
    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas del dataset
        
        Returns:
            Diccionario con estadísticas
        """
        total = len(self.samples)
        
        # Distribución por split
        splits = {}
        for split in DatasetSplit:
            count = len(self.get_split(split))
            splits[split.value] = {
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0
            }
        
        # Distribución por patrón
        patterns = {}
        for sample in self.samples:
            pattern = sample.label.primary_pattern
            patterns[pattern] = patterns.get(pattern, 0) + 1
        
        # Distribución por complejidad
        complexities = {}
        for sample in self.samples:
            big_o = sample.label.big_o
            complexities[big_o] = complexities.get(big_o, 0) + 1
        
        return {
            "total_samples": total,
            "splits": splits,
            "patterns": patterns,
            "complexities": complexities,
        }
    
    def to_dict_list(self) -> List[Dict]:
        """
        Convierte dataset a lista de diccionarios
        
        Returns:
            Lista de diccionarios con todas las muestras
        """
        return [
            {
                "algorithm_name": s.algorithm_name,
                "code": s.code,
                "category": s.category,
                "split": s.split.value,
                "label": s.label.to_dict(),
                "metadata": s.metadata,
            }
            for s in self.samples
        ]

class SyntheticDataCreator:
    """Creador de datasets sintéticos balanceados"""
    
    def __init__(
        self,
        train_ratio: float = 0.7,
        validation_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: Optional[int] = None
    ):
        """
        Inicializa el creador
        
        Args:
            train_ratio: Proporción para training (0-1)
            validation_ratio: Proporción para validación (0-1)
            test_ratio: Proporción para test (0-1)
            seed: Seed para reproducibilidad
        """
        assert abs(train_ratio + validation_ratio + test_ratio - 1.0) < 0.01, \
            "Las proporciones deben sumar 1.0"
        
        self.train_ratio = train_ratio
        self.validation_ratio = validation_ratio
        self.test_ratio = test_ratio
        
        if seed is not None:
            random.seed(seed)
        
        self.generator = AlgorithmGenerator(GenerationConfig(seed=seed))
        self.labeler = ComplexityLabeler()
    
    def create_balanced_dataset(
        self,
        patterns: List[str],
        samples_per_pattern: int = 100
    ) -> SyntheticDataset:
        """
        Crea dataset balanceado con múltiples patrones
        
        Args:
            patterns: Lista de patrones a incluir
            samples_per_pattern: Muestras por patrón
        
        Returns:
            SyntheticDataset balanceado
        """
        all_samples = []
        
        for pattern in patterns:
            # Generar algoritmos para este patrón
            templates = self.generator.generate_from_pattern(
                pattern,
                count=samples_per_pattern
            )
            
            # Etiquetar cada algoritmo
            for template in templates:
                try:
                    label = self.labeler.label(template.code)
                    
                    # Asignar split aleatoriamente según proporciones
                    rand = random.random()
                    if rand < self.train_ratio:
                        split = DatasetSplit.TRAIN
                    elif rand < self.train_ratio + self.validation_ratio:
                        split = DatasetSplit.VALIDATION
                    else:
                        split = DatasetSplit.TEST
                    
                    sample = SyntheticSample(
                        algorithm_name=template.name,
                        code=template.code,
                        category=template.category,
                        label=label,
                        split=split,
                        metadata={
                            "expected_complexity": template.expected_complexity,
                            "expected_pattern": template.pattern,
                        }
                    )
                    
                    all_samples.append(sample)
                    
                except Exception as e:
                    # Skip muestras que fallan
                    print(f"Error labeling {template.name}: {e}")
                    continue
        
        # Shuffle final
        random.shuffle(all_samples)
        
        dataset = SyntheticDataset(
            samples=all_samples,
            metadata={
                "patterns": patterns,
                "samples_per_pattern": samples_per_pattern,
                "train_ratio": self.train_ratio,
                "validation_ratio": self.validation_ratio,
                "test_ratio": self.test_ratio,
            }
        )
        
        return dataset
    
    def create_from_templates(
        self,
        templates: List[AlgorithmTemplate],
        variations_per_template: int = 10
    ) -> SyntheticDataset:
        """
        Crea dataset desde templates específicos
        
        Args:
            templates: Lista de templates base
            variations_per_template: Variaciones por template
        
        Returns:
            SyntheticDataset
        """
        all_samples = []
        
        for template in templates:
            # Generar variaciones
            variations = self.generator.generate_variations(
                template,
                count=variations_per_template
            )
            
            # Incluir template original
            variations.append(template)
            
            # Etiquetar todas
            for var_template in variations:
                try:
                    label = self.labeler.label(var_template.code)
                    
                    # Asignar split
                    rand = random.random()
                    if rand < self.train_ratio:
                        split = DatasetSplit.TRAIN
                    elif rand < self.train_ratio + self.validation_ratio:
                        split = DatasetSplit.VALIDATION
                    else:
                        split = DatasetSplit.TEST
                    
                    sample = SyntheticSample(
                        algorithm_name=var_template.name,
                        code=var_template.code,
                        category=var_template.category,
                        label=label,
                        split=split,
                        metadata={
                            "base_template": template.name,
                        }
                    )
                    
                    all_samples.append(sample)
                    
                except Exception as e:
                    print(f"Error labeling {var_template.name}: {e}")
                    continue
        
        random.shuffle(all_samples)
        
        dataset = SyntheticDataset(
            samples=all_samples,
            metadata={
                "templates_count": len(templates),
                "variations_per_template": variations_per_template,
            }
        )
        
        return dataset

def create_balanced_dataset(
    patterns: List[str],
    samples_per_pattern: int = 100,
    seed: Optional[int] = None
) -> SyntheticDataset:
    """
    Helper function para crear dataset balanceado
    
    Args:
        patterns: Lista de patrones
        samples_per_pattern: Muestras por patrón
        seed: Seed para reproducibilidad
    
    Returns:
        SyntheticDataset
    """
    creator = SyntheticDataCreator(seed=seed)
    return creator.create_balanced_dataset(patterns, samples_per_pattern)