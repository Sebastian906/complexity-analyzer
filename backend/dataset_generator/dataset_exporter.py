"""
Dataset Exporter - Exportador de Datasets a Formatos ML

Exporta datasets sintéticos a formatos comunes para ML:
- CSV: Para análisis en pandas
- JSON: Para integración con sistemas
- Pickle: Para uso directo en Python
"""

import csv
import json
import pickle
from pathlib import Path
from typing import Optional
from enum import Enum

from dataset_generator.synthetic_data_creator import SyntheticDataset

class ExportFormat(str, Enum):
    """Formatos de exportación soportados"""
    CSV = "csv"
    JSON = "json"
    PICKLE = "pickle"
    JSONL = "jsonl"  # JSON Lines

class DatasetExporter:
    """Exportador de datasets a múltiples formatos"""
    
    def __init__(self, output_dir: Path = None):
        """
        Inicializa el exportador
        
        Args:
            output_dir: Directorio de salida (default: data/datasets/)
        """
        self.output_dir = output_dir or Path("data/datasets")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        dataset: SyntheticDataset,
        format: ExportFormat,
        filename: Optional[str] = None
    ) -> Path:
        """
        Exporta dataset al formato especificado
        
        Args:
            dataset: Dataset a exportar
            format: Formato de exportación
            filename: Nombre del archivo (sin extensión)
        
        Returns:
            Path al archivo exportado
        """
        filename = filename or "synthetic_dataset"
        
        if format == ExportFormat.CSV:
            return self.export_to_csv(dataset, filename)
        elif format == ExportFormat.JSON:
            return self.export_to_json(dataset, filename)
        elif format == ExportFormat.PICKLE:
            return self.export_to_pickle(dataset, filename)
        elif format == ExportFormat.JSONL:
            return self.export_to_jsonl(dataset, filename)
        else:
            raise ValueError(f"Formato no soportado: {format}")
    
    def export_to_csv(
        self,
        dataset: SyntheticDataset,
        filename: str = "dataset"
    ) -> Path:
        """
        Exporta a CSV
        
        Args:
            dataset: Dataset
            filename: Nombre base del archivo
        
        Returns:
            Path al archivo CSV
        """
        filepath = self.output_dir / f"{filename}.csv"
        
        # Preparar datos
        rows = []
        
        for sample in dataset.samples:
            row = {
                "algorithm_name": sample.algorithm_name,
                "code": sample.code,
                "category": sample.category,
                "split": sample.split.value,
                # Labels
                "big_o": sample.label.big_o,
                "omega": sample.label.omega,
                "theta": sample.label.theta,
                "space_complexity": sample.label.space_complexity,
                "primary_pattern": sample.label.primary_pattern,
                "primary_pattern_confidence": sample.label.primary_pattern_confidence,
                "structures": ",".join(sample.label.structures),
                "is_recursive": sample.label.is_recursive,
                "is_iterative": sample.label.is_iterative,
            }
            
            rows.append(row)
        
        # Escribir CSV
        with filepath.open('w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        print(f"✓ Dataset exportado a CSV: {filepath}")
        return filepath
    
    def export_to_json(
        self,
        dataset: SyntheticDataset,
        filename: str = "dataset"
    ) -> Path:
        """
        Exporta a JSON
        
        Args:
            dataset: Dataset
            filename: Nombre base del archivo
        
        Returns:
            Path al archivo JSON
        """
        filepath = self.output_dir / f"{filename}.json"
        
        # Preparar datos
        data = {
            "metadata": dataset.metadata,
            "statistics": dataset.get_statistics(),
            "samples": dataset.to_dict_list(),
        }
        
        # Escribir JSON
        with filepath.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Dataset exportado a JSON: {filepath}")
        return filepath
    
    def export_to_jsonl(
        self,
        dataset: SyntheticDataset,
        filename: str = "dataset"
    ) -> Path:
        """
        Exporta a JSON Lines (una muestra por línea)
        
        Args:
            dataset: Dataset
            filename: Nombre base del archivo
        
        Returns:
            Path al archivo JSONL
        """
        filepath = self.output_dir / f"{filename}.jsonl"
        
        # Escribir JSONL
        with filepath.open('w', encoding='utf-8') as f:
            for sample_dict in dataset.to_dict_list():
                f.write(json.dumps(sample_dict, ensure_ascii=False) + '\n')
        
        print(f"✓ Dataset exportado a JSONL: {filepath}")
        return filepath
    
    def export_to_pickle(
        self,
        dataset: SyntheticDataset,
        filename: str = "dataset"
    ) -> Path:
        """
        Exporta a Pickle (formato nativo Python)
        
        Args:
            dataset: Dataset
            filename: Nombre base del archivo
        
        Returns:
            Path al archivo pickle
        """
        filepath = self.output_dir / f"{filename}.pkl"
        
        # Escribir pickle
        with filepath.open('wb') as f:
            pickle.dump(dataset, f)
        
        print(f"✓ Dataset exportado a Pickle: {filepath}")
        return filepath
    
    def export_splits_separately(
        self,
        dataset: SyntheticDataset,
        format: ExportFormat,
        base_filename: str = "dataset"
    ) -> dict:
        """
        Exporta cada split (train/val/test) a archivos separados
        
        Args:
            dataset: Dataset
            format: Formato de exportación
            base_filename: Nombre base para los archivos
        
        Returns:
            Dict con {split: filepath}
        """
        from dataset_generator.synthetic_data_creator import DatasetSplit
        
        filepaths = {}
        
        for split in DatasetSplit:
            # Crear dataset temporal con solo ese split
            samples = dataset.get_split(split)
            
            if not samples:
                continue
            
            split_dataset = SyntheticDataset(
                samples=samples,
                metadata={
                    **dataset.metadata,
                    "split": split.value,
                }
            )
            
            # Exportar
            filename = f"{base_filename}_{split.value}"
            filepath = self.export(split_dataset, format, filename)
            filepaths[split.value] = filepath
        
        return filepaths

def export_dataset(
    dataset: SyntheticDataset,
    format: ExportFormat,
    output_path: Optional[Path] = None,
    filename: str = "dataset"
) -> Path:
    """
    Helper function para exportar dataset
    
    Args:
        dataset: Dataset a exportar
        format: Formato
        output_path: Directorio de salida
        filename: Nombre del archivo
    
    Returns:
        Path al archivo exportado
    """
    exporter = DatasetExporter(output_dir=output_path)
    return exporter.export(dataset, format, filename)