from pathlib import Path

# Diretórios do Projeto
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EXTRACTED_DIR = DATA_DIR / "extracted"
CONFIG_DIR = PROJECT_ROOT / "src" / "utils"

# CONFIGURAÇÕES DE LOGGING

LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'verbose': False}

# FUNÇÕES UTILITÁRIAS
def ensure_directories():
    """Cria diretórios necessários se não existirem."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

def get_config_path() -> Path:
    """Retorna caminho para domain_and_class_structure.json."""
    return CONFIG_DIR / "domain_and_class_structure.json"