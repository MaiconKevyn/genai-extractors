# src/extractors/base_extractor.py
"""
BaseExtractor melhorado com injeção de dependências.
Remove acoplamento forte com configurações globais.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Union, Optional, Dict, Any
from abc import ABC, abstractmethod


@dataclass
class ExtractionResult:
    """
    Unified data structure for extraction results.
    Contains the full content of the file as a single string.
    """
    source_file: str
    content: Optional[str]
    success: bool
    error_message: Optional[str] = None


@dataclass
class ExtractorConfig:
    """
    Configuration object that can be injected into extractors.
    Remove dependência de imports globais.
    """
    # Sampling configuration
    page_limit_for_sampling: int = 10
    pages_to_sample: int = 5
    paragraph_limit_for_sampling: int = 180
    paragraphs_to_sample: int = 90
    row_limit_for_sampling: int = 1000
    rows_to_sample: int = 500

    # OCR configuration
    ocr_enabled: bool = True
    ocr_languages: list = None
    ocr_use_gpu: bool = False
    ocr_confidence_threshold: float = 0.5
    ocr_max_pages: int = 20

    # Quality thresholds
    quality_min_text_length: int = 50
    quality_max_replacement_chars: int = 5
    quality_min_word_count: int = 10
    quality_ocr_threshold_score: float = 60.0

    def __post_init__(self):
        if self.ocr_languages is None:
            self.ocr_languages = ['en', 'pt']


class BaseExtractor(ABC):
    """
    Base class melhorada com injeção de dependências.
    Remove acoplamento forte com módulos específicos.
    """

    def __init__(self,
                 config: Optional[ExtractorConfig] = None,
                 quality_analyzer=None,
                 ocr_processor=None,
                 logger=None):
        """
        Initialize with dependency injection.

        Args:
            config: Configuration object (optional)
            quality_analyzer: Text quality analyzer (optional)
            ocr_processor: OCR processor (optional)
            logger: Logger instance (optional)
        """
        # Use default config if none provided
        self.config = config or ExtractorConfig()

        # Inject dependencies or use defaults
        self.quality_analyzer = quality_analyzer
        self.ocr_processor = ocr_processor

        # Setup logger (dependency injection or default)
        if logger:
            self.logger = logger
        else:
            import logging
            self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts the content of a file and returns an ExtractionResult object.
        This method must be implemented by each extractor.
        """
        pass

    def _lazy_init_quality_analyzer(self):
        """
        Lazy initialization of quality analyzer if not injected.
        Evita import circular e permite injeção.
        """
        if self.quality_analyzer is None:
            try:
                from ..utils.text_quality import TextQualityAnalyzer
                # Pass config as dict to avoid coupling
                quality_config = {
                    'min_text_length': self.config.quality_min_text_length,
                    'max_replacement_chars': self.config.quality_max_replacement_chars,
                    'min_word_count': self.config.quality_min_word_count,
                    'ocr_threshold_score': self.config.quality_ocr_threshold_score
                }
                self.quality_analyzer = TextQualityAnalyzer(quality_config)
            except ImportError:
                self.logger.warning("TextQualityAnalyzer not available")
                self.quality_analyzer = None
        return self.quality_analyzer

    def _lazy_init_ocr_processor(self):
        """
        Lazy initialization of OCR processor if not injected.
        Evita import circular e permite injeção.
        """
        if self.ocr_processor is None and self.config.ocr_enabled:
            try:
                from ..utils.ocr_processor import EasyOCRProcessor
                self.ocr_processor = EasyOCRProcessor(
                    languages=self.config.ocr_languages,
                    gpu=self.config.ocr_use_gpu
                )
            except ImportError:
                self.logger.warning("EasyOCRProcessor not available")
                self.ocr_processor = None
        return self.ocr_processor

    def save_as_json(self, result: ExtractionResult, output_path: Union[str, Path]) -> bool:
        """
        Saves the content of an ExtractionResult to a JSON file.
        """
        import json

        output_path = Path(output_path)

        if not result.success:
            self.logger.error(
                f"Cannot save a result with error for '{result.source_file}'. Reason: {result.error_message}")
            return False

        try:
            # Ensure the output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            data_to_save = {
                "source_file": result.source_file,
                "content": result.content
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Result from '{result.source_file}' saved at: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving JSON to '{output_path}': {e}")
            return False

    def extract_and_save(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        """
        Runs the complete process: extracts the content and saves it as JSON.
        This method orchestrates the call to 'extract' and 'save_as_json'.
        """
        result = self.extract(input_path)
        return self.save_as_json(result, output_path)

    def _create_error_result(self, source_file: str, error_message: str) -> ExtractionResult:
        """Helper method to create standardized error results."""
        self.logger.error(f"Error in file '{source_file}': {error_message}")
        return ExtractionResult(
            source_file=source_file,
            content=None,
            success=False,
            error_message=error_message
        )