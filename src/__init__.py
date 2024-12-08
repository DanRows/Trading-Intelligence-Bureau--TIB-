"""
Trading Intelligence Bureau (TIB)
--------------------------------
Sistema de análisis y trading algorítmico.
"""

from pathlib import Path

# Definir rutas base
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = Path(__file__).parent
DATA_PATH = SRC_PATH / "data"
CONFIG_PATH = SRC_PATH / "config"
MODELS_PATH = SRC_PATH / "models"
RESULTS_PATH = PROJECT_ROOT / "results"

# Crear directorios necesarios
RESULTS_PATH.mkdir(parents=True, exist_ok=True)

__version__ = "0.1.0" 