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
    """Configuration for OCR processing with Tesseract"""
    # Tesseract configuration
    enabled: bool = True
    languages: str = 'eng+por'  # Tesseract language codes (eng+por for English+Portuguese)
    config: str = '--psm 3'  # Page Segmentation Mode: 3 = Fully automatic page segmentation

    # Image preprocessing
    dpi_scale: float = 2.0  # Multiplicador de DPI (2x = melhor qualidade, ~300 DPI)

    # Performance
    max_pages_for_ocr: int = 20  # Máximo de páginas para fazer OCR
    timeout_per_page: int = 30  # Timeout em segundos por página

    # Fallback behavior
    use_ocr_fallback: bool = True  # Se ativa OCR automaticamente
    save_debug_images: bool = False  # Para debug, salva imagens processadas


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
    Valida se as dependências OCR estão disponíveis (Tesseract).

    Returns:
        Dict com status de cada dependência
    """
    import importlib

    status = {
        'pytesseract_installed': False,
        'tesseract_executable': False,
        'pymupdf_available': False,
        'pillow_available': False
    }

    # Verifica pytesseract
    try:
        pytesseract = importlib.import_module('pytesseract')
        status['pytesseract_installed'] = True

        # Verifica se o executável do Tesseract está disponível
        try:
            pytesseract.get_tesseract_version()
            status['tesseract_executable'] = True
        except Exception:
            status['tesseract_executable'] = False

    except ImportError:
        status['pytesseract_installed'] = False

    # Verifica PyMuPDF (para conversão PDF->imagem)
    try:
        importlib.import_module('fitz')
        status['pymupdf_available'] = True
    except ImportError:
        status['pymupdf_available'] = False

    # Verifica Pillow (para processamento de imagens)
    try:
        importlib.import_module('PIL')
        status['pillow_available'] = True
    except ImportError:
        status['pillow_available'] = False

    return status


def setup_ocr_environment():
    """
    Configura ambiente OCR e valida dependências Tesseract.
    Deve ser chamada na inicialização da aplicação.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("🔧 Setting up Tesseract OCR environment...")

    # Valida dependências
    deps = validate_ocr_dependencies()

    logger.info(f"📋 Tesseract Dependencies Status:")
    for dep, status in deps.items():
        status_icon = "✅" if status else "❌"
        logger.info(f"   {status_icon} {dep}: {status}")

    # Warnings para dependências faltantes
    missing_deps = [dep for dep, status in deps.items() if not status]

    if missing_deps:
        logger.warning(f"⚠️  Missing OCR dependencies: {', '.join(missing_deps)}")

        if not deps['pytesseract_installed']:
            logger.warning("📥 Install pytesseract: pip install pytesseract")
        if not deps['tesseract_executable']:
            logger.warning("📥 Install Tesseract executable:")
            logger.warning("   • Ubuntu/Debian: sudo apt install tesseract-ocr")
            logger.warning("   • macOS: brew install tesseract")
            logger.warning("   • Windows: Download from GitHub releases")
        if not deps['pillow_available']:
            logger.warning("📥 Install Pillow: pip install Pillow")

    # Ajusta configuração se OCR não estiver disponível
    critical_deps = ['pytesseract_installed', 'tesseract_executable', 'pymupdf_available', 'pillow_available']
    if not all(deps[dep] for dep in critical_deps):
        global OCR_CONFIG
        OCR_CONFIG.enabled = False
        logger.warning("🚫 OCR disabled due to missing critical dependencies")
    else:
        logger.info("✅ Tesseract OCR environment ready!")

    return deps


if __name__ == "__main__":
    # Teste das configurações
    print("🧪 Testing Tesseract OCR configuration...")

    deps = setup_ocr_environment()
    print(f"\n📊 Dependencies: {deps}")

    print(f"\n⚙️  OCR Config:")
    print(f"   Enabled: {OCR_CONFIG.enabled}")
    print(f"   Languages: {OCR_CONFIG.languages}")
    print(f"   Config: {OCR_CONFIG.config}")
    print(f"   DPI Scale: {OCR_CONFIG.dpi_scale}")