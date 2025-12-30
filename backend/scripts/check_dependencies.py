"""
Script para verificar compatibilidad de dependencias con Python 3.14

Ejecutar antes de instalar las dependencias para detectar problemas.
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verifica que estemos usando Python 3.14+"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 14:
        print("ADVERTENCIA: Se recomienda Python 3.14+")
        return False
    
    print("Python 3.14+ detectado")
    return True


def check_pip_version():
    """Verifica versión de pip"""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True
    )
    print(f"{result.stdout.strip()}")
    return result.returncode == 0


def install_dependencies(requirements_file: str, dry_run: bool = True):
    """
    Intenta instalar dependencias (dry-run por defecto)
    
    Args:
        requirements_file: Archivo requirements.txt
        dry_run: Si True, solo simula la instalación
    """
    print(f"\n{'Verificando' if dry_run else 'Instalando'} dependencias de {requirements_file}...")
    
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        requirements_file,
    ]
    
    if dry_run:
        cmd.append("--dry-run")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"{'Verificación' if dry_run else 'Instalación'} exitosa")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error en {'verificación' if dry_run else 'instalación'}:")
        print(e.stderr)
        return False


def main():
    """Función principal"""
    print("VERIFICADOR DE DEPENDENCIAS - Complexity Analyzer")
    print()
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    print()
    
    # Verificar pip
    if not check_pip_version():
        print("pip no está disponible")
        sys.exit(1)
    
    # Verificar archivos requirements
    requirements_files = [
        "requirements.txt",
        "requirements-dev.txt"
    ]
    
    for req_file in requirements_files:
        req_path = Path(req_file)
        if not req_path.exists():
            print(f"No se encontró {req_file}")
            continue
        
        success = install_dependencies(req_file, dry_run=True)
        
        if not success:
            print(f"Hay problemas potenciales con {req_file}")
    
    print("Verificación completada")
    print("\nPara instalar las dependencias:")
    print("  pip install -r requirements.txt")
    print("  pip install -r requirements-dev.txt")

if __name__ == "__main__":
    main()