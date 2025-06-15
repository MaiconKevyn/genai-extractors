from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any


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
class QualityConfig:
    """Configuration for text quality analysis"""
    # Thresholds básicos
    min_text_length: int = 50
    max_replacement_chars: int = 5
    min_word_count: int = 10
    max_replacement_ratio: float = 0.01
    min_ascii_ratio: float = 0.8

    # OCR decision thresholds
    ocr_threshold_score: float = 60.0  # Score abaixo disso = OCR needed
    severe_quality_threshold: float = 30.0

    # Debug
    debug_mode: bool = False  # Ativa logs detalhados


@dataclass
class OCRConfig:
    """Configuration for OCR processing with Tesseract"""
    # Tesseract configuration
    enabled: bool = True
    tesseract_cmd: str = "tesseract"  # Path para tesseract executable
    language: str = "eng+por"  # Idiomas: inglês + português
    psm_mode: int = 6  # Page Segmentation Mode (6 = uniform block of text)
    oem_mode: int = 3  # OCR Engine Mode (3 = default, based on what is available)

    # Image preprocessing
    dpi_scale: float = 2.0  # Multiplicador de DPI (2x = melhor qualidade)
    contrast_enhance: bool = True
    noise_removal: bool = True

    # Performance
    max_pages_for_ocr: int = 20  # Máximo de páginas para fazer OCR
    timeout_per_page: int = 30  # Timeout em segundos por página

    # Fallback behavior
    use_ocr_fallback: bool = True  # Se ativa OCR automaticamente
    save_preprocessed_images: bool = False  # Para debug, salva imagens processadas

    # Custom tesseract options
    custom_config: str = "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ.,!?;:()\"\'-"


# Global configurations
EXTRACTOR_CONFIG = ExtractorConfig()
QUALITY_CONFIG = QualityConfig()
OCR_CONFIG = OCRConfig()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# 🆕 OCR specific paths
OCR_DEBUG_DIR = DATA_DIR / "ocr_debug"  # Para salvar imagens de debug
TEMP_DIR = DATA_DIR / "temp"  # Para arquivos temporários

# Create directories if they don't exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OCR_DEBUG_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def get_quality_config() -> Dict[str, Any]:
    """
    Retorna configurações de qualidade como dicionário para TextQualityAnalyzer.
    """
    return {
        'min_text_length': QUALITY_CONFIG.min_text_length,
        'max_replacement_chars': QUALITY_CONFIG.max_replacement_chars,
        'min_word_count': QUALITY_CONFIG.min_word_count,
        'max_replacement_ratio': QUALITY_CONFIG.max_replacement_ratio,
        'min_ascii_ratio': QUALITY_CONFIG.min_ascii_ratio,
        'ocr_threshold_score': QUALITY_CONFIG.ocr_threshold_score,
        'severe_quality_threshold': QUALITY_CONFIG.severe_quality_threshold
    }


def validate_ocr_dependencies() -> Dict[str, bool]:
    """
    Valida se as dependências OCR estão disponíveis.

    Returns:
        Dict com status de cada dependência
    """
    import subprocess
    import importlib

    status = {
        'tesseract_installed': False,
        'pytesseract_available': False,
        'pillow_available': False,
        'opencv_available': False
    }

    # Verifica Tesseract
    try:
        result = subprocess.run([OCR_CONFIG.tesseract_cmd, '--version'],
                                capture_output=True, text=True, timeout=5)
        status['tesseract_installed'] = result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        status['tesseract_installed'] = False

    # Verifica pytesseract
    try:
        importlib.import_module('pytesseract')
        status['pytesseract_available'] = True
    except ImportError:
        status['pytesseract_available'] = False

    # Verifica Pillow
    try:
        importlib.import_module('PIL')
        status['pillow_available'] = True
    except ImportError:
        status['pillow_available'] = False

    # Verifica OpenCV (opcional para preprocessing)
    try:
        importlib.import_module('cv2')
        status['opencv_available'] = True
    except ImportError:
        status['opencv_available'] = False

    return status


# 🆕 Configurações específicas por tipo de documento
DOCUMENT_TYPE_CONFIGS = {
    'academic_papers': QualityConfig(
        min_text_length=200,
        min_word_count=50,
        ocr_threshold_score=80,
        min_ascii_ratio=0.9
    ),
    'forms': QualityConfig(
        min_text_length=20,
        min_word_count=5,
        ocr_threshold_score=40,
        min_ascii_ratio=0.7
    ),
    'multilingual': QualityConfig(
        min_ascii_ratio=0.6,
        ocr_threshold_score=50,
        max_replacement_ratio=0.02
    )
}


def get_config_for_document_type(doc_type: str) -> QualityConfig:
    """
    Retorna configuração específica para tipo de documento.

    Args:
        doc_type: Tipo do documento ('academic_papers', 'forms', 'multilingual')

    Returns:
        QualityConfig específica ou padrão
    """
    return DOCUMENT_TYPE_CONFIGS.get(doc_type, QUALITY_CONFIG)


# 🆕 Função para setup inicial
def setup_ocr_environment():
    """
    Configura ambiente OCR e valida dependências.
    Deve ser chamada na inicialização da aplicação.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("🔧 Setting up OCR environment...")

    # Valida dependências
    deps = validate_ocr_dependencies()

    logger.info(f"📋 OCR Dependencies Status:")
    for dep, status in deps.items():
        status_icon = "✅" if status else "❌"
        logger.info(f"   {status_icon} {dep}: {status}")

    # Warnings para dependências faltantes
    missing_deps = [dep for dep, status in deps.items() if not status]

    if missing_deps:
        logger.warning(f"⚠️  Missing OCR dependencies: {', '.join(missing_deps)}")
        logger.warning("📥 Install with: pip install pytesseract pillow")

        if not deps['tesseract_installed']:
            logger.warning("📥 Install Tesseract from: https://github.com/tesseract-ocr/tesseract")

    # Ajusta configuração se OCR não estiver disponível
    if not all([deps['tesseract_installed'], deps['pytesseract_available']]):
        global OCR_CONFIG
        OCR_CONFIG.enabled = False
        logger.warning("🚫 OCR disabled due to missing dependencies")
    else:
        logger.info("✅ OCR environment ready!")

    return deps


if __name__ == "__main__":
    # Teste das configurações
    print("🧪 Testing OCR configuration...")

    deps = setup_ocr_environment()
    print(f"\n📊 Dependencies: {deps}")

    print(f"\n⚙️  OCR Config:")
    print(f"   Enabled: {OCR_CONFIG.enabled}")
    print(f"   Language: {OCR_CONFIG.language}")
    print(f"   DPI Scale: {OCR_CONFIG.dpi_scale}")

    print(f"\n⚙️  Quality Config:")
    quality_dict = get_quality_config()
    for key, value in quality_dict.items():
        print(f"   {key}: {value}")