from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class ExtractorConfig:
    """Configuration for text extraction"""
    output_format: str = "json"  # "json" or "markdown"
    include_images: bool = False
    include_metadata: bool = True
    supported_extensions: List[str] = None

    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = ['.pdf', '.docx', '.xlsx', '.csv']


@dataclass
class OCRConfig:
    """Configuration for OCR processing with EasyOCR"""
    # EasyOCR configuration
    enabled: bool = True
    languages: List[str] = None  # ['en', 'pt'] por padrão
    use_gpu: bool = False  # GPU disabled por padrão para compatibilidade
    confidence_threshold: float = 0.5  # Confiança mínima para aceitar texto

    # Image preprocessing
    dpi_scale: float = 2.0  # Multiplicador de DPI (2x = melhor qualidade)
    enhance_image: bool = True  # Aplica melhorias na imagem antes do OCR

    # Performance
    max_pages_for_ocr: int = 20  # Máximo de páginas para fazer OCR
    timeout_per_page: int = 30  # Timeout em segundos por página

    # Fallback behavior
    use_ocr_fallback: bool = True  # Se ativa OCR automaticamente
    save_debug_images: bool = False  # Para debug, salva imagens processadas

    def __post_init__(self):
        if self.languages is None:
            self.languages = ['en', 'pt']  # Inglês + Português


# Global configurations
EXTRACTOR_CONFIG = ExtractorConfig()
OCR_CONFIG = OCRConfig()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# OCR specific paths
OCR_DEBUG_DIR = DATA_DIR / "ocr_debug"  # Para salvar imagens de debug
TEMP_DIR = DATA_DIR / "temp"  # Para arquivos temporários

# Create directories if they don't exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OCR_DEBUG_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def validate_ocr_dependencies() -> dict:
    """
    Valida se as dependências OCR estão disponíveis (EasyOCR).

    Returns:
        Dict com status de cada dependência
    """
    import importlib

    status = {
        'easyocr_installed': False,
        'pymupdf_available': False,
        'opencv_available': False,
        'torch_available': False  # EasyOCR precisa do PyTorch
    }

    # Verifica EasyOCR
    try:
        importlib.import_module('easyocr')
        status['easyocr_installed'] = True
    except ImportError:
        status['easyocr_installed'] = False

    # Verifica PyMuPDF (para conversão PDF->imagem)
    try:
        importlib.import_module('fitz')
        status['pymupdf_available'] = True
    except ImportError:
        status['pymupdf_available'] = False

    # Verifica OpenCV (opcional para preprocessing)
    try:
        importlib.import_module('cv2')
        status['opencv_available'] = True
    except ImportError:
        status['opencv_available'] = False

    # Verifica PyTorch (necessário para EasyOCR)
    try:
        importlib.import_module('torch')
        status['torch_available'] = True
    except ImportError:
        status['torch_available'] = False

    return status


def setup_ocr_environment():
    """
    Configura ambiente OCR e valida dependências EasyOCR.
    Deve ser chamada na inicialização da aplicação.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("🔧 Setting up EasyOCR environment...")

    # Valida dependências
    deps = validate_ocr_dependencies()

    logger.info(f"📋 EasyOCR Dependencies Status:")
    for dep, status in deps.items():
        status_icon = "✅" if status else "❌"
        logger.info(f"   {status_icon} {dep}: {status}")

    # Warnings para dependências faltantes
    missing_deps = [dep for dep, status in deps.items() if not status]

    if missing_deps:
        logger.warning(f"⚠️  Missing OCR dependencies: {', '.join(missing_deps)}")
        logger.warning("📥 Install with: pip install easyocr torch")

        if not deps['easyocr_installed']:
            logger.warning("📥 Install EasyOCR: pip install easyocr")
        if not deps['torch_available']:
            logger.warning("📥 Install PyTorch: pip install torch")

    # Ajusta configuração se OCR não estiver disponível
    critical_deps = ['easyocr_installed', 'pymupdf_available', 'torch_available']
    if not all(deps[dep] for dep in critical_deps):
        global OCR_CONFIG
        OCR_CONFIG.enabled = False
        logger.warning("🚫 OCR disabled due to missing critical dependencies")
    else:
        logger.info("✅ EasyOCR environment ready!")

    return deps


if __name__ == "__main__":
    # Teste das configurações
    print("🧪 Testing EasyOCR configuration...")

    deps = setup_ocr_environment()
    print(f"\n📊 Dependencies: {deps}")

    print(f"\n⚙️  OCR Config:")
    print(f"   Enabled: {OCR_CONFIG.enabled}")
    print(f"   Languages: {OCR_CONFIG.languages}")
    print(f"   Use GPU: {OCR_CONFIG.use_gpu}")
    print(f"   Confidence Threshold: {OCR_CONFIG.confidence_threshold}")