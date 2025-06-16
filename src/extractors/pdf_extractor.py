import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import Union

from .base_extractor import BaseExtractor, ExtractionResult
from ..utils.text_quality import TextQualityAnalyzer
from ..utils.ocr_processor import EasyOCRProcessor


class PDFTextExtractor(BaseExtractor):
    """
    Extracts the full text from a PDF file, with special rules for long files.
    Automatically applies OCR when text quality is poor.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Import OCR configuration here to avoid circular imports
        try:
            from config.settings import OCR_CONFIG, QUALITY_CONFIG
            self.ocr_config = OCR_CONFIG
            self.PAGE_LIMIT_FOR_SAMPLING = 10
            self.PAGES_TO_SAMPLE = 5
        except ImportError:
            self.logger.warning("OCR configuration not found, using defaults")

            # Fallback configuration
            class DefaultOCRConfig:
                max_pages_for_ocr = 20
                enabled = True
                languages = ['en']
                use_gpu = False

            self.ocr_config = DefaultOCRConfig()

        self.quality_analyzer = TextQualityAnalyzer()
        self.ocr_processor = None  # Lazy loading

    def _get_ocr_processor(self) -> EasyOCRProcessor:
        """Lazy loading of the OCR processor with proper configuration."""
        if self.ocr_processor is None:
            self.ocr_processor = EasyOCRProcessor(
                languages=self.ocr_config.languages,
                gpu=self.ocr_config.use_gpu
            )
        return self.ocr_processor

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts text from a PDF with intelligent OCR application.
        """
        pdf_path = Path(input_path)
        source_filename = pdf_path.name

        if not pdf_path.exists():
            return self._create_error_result(source_filename, f"File not found: {pdf_path}")

        if pdf_path.suffix.lower() != '.pdf':
            return self._create_error_result(source_filename, f"File is not a PDF: {pdf_path.suffix}")

        try:
            # STEP 1: Standard text extraction
            extracted_text = self._extract_standard_text(pdf_path, source_filename)

            # STEP 2: Quality analysis
            quality_report = self.quality_analyzer.analyze_quality(extracted_text)

            # STEP 3: Decide whether to apply OCR
            if quality_report['needs_ocr'] and self.ocr_config.enabled:
                extracted_text = self._apply_intelligent_ocr(
                    pdf_path, source_filename, extracted_text, quality_report
                )

            return ExtractionResult(
                source_file=source_filename,
                content=extracted_text,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, str(e))

    def _apply_intelligent_ocr(self, pdf_path: Path, source_filename: str,
                               original_text: str, quality_report: dict) -> str:
        """
        Applies OCR intelligently, respecting configuration limits.
        """
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)

        # Respect max_pages_for_ocr configuration
        if total_pages > self.ocr_config.max_pages_for_ocr:
            self.logger.warning(
                f"'{source_filename}' has {total_pages} pages, exceeding OCR limit of "
                f"{self.ocr_config.max_pages_for_ocr}. Applying OCR to first "
                f"{self.ocr_config.max_pages_for_ocr} pages only."
            )

        doc.close()

        self.logger.info(f"Poor quality detected for '{source_filename}'. Applying OCR...")
        ocr_text = self._apply_ocr_extraction(pdf_path, source_filename)

        if ocr_text and len(ocr_text.strip()) > len(original_text.strip()):
            self.logger.info(f"OCR improved text quality for '{source_filename}'")
            return ocr_text
        else:
            self.logger.warning(f"OCR did not improve quality for '{source_filename}', keeping original")
            return original_text

    def _extract_standard_text(self, pdf_path: Path, source_filename: str) -> str:
        """Extracts text using standard method (PyMuPDF)."""
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        page_texts = []

        # Sampling logic for large files
        if total_pages > self.PAGE_LIMIT_FOR_SAMPLING:
            self.logger.info(
                f"'{source_filename}' has {total_pages} pages. "
                f"Extracting the first {self.PAGES_TO_SAMPLE} and the last {self.PAGES_TO_SAMPLE}."
            )

            # Extract first pages
            for i in range(self.PAGES_TO_SAMPLE):
                page_texts.append(doc[i].get_text("text").strip())

            # Add separator
            page_texts.append("\n\n... (content from intermediate pages omitted) ...\n\n")

            # Extract last pages
            start_last_pages = total_pages - self.PAGES_TO_SAMPLE
            for i in range(start_last_pages, total_pages):
                page_texts.append(doc[i].get_text("text").strip())

        else:
            # Logic for small files
            self.logger.info(f"'{source_filename}' has {total_pages} pages. Extracting all content.")
            page_texts = [page.get_text("text").strip() for page in doc]

        doc.close()
        return "\n\n".join(filter(None, page_texts))

    def _apply_ocr_extraction(self, pdf_path: Path, source_filename: str) -> str:
        """Applies OCR to extract text from the PDF."""
        try:
            ocr_processor = self._get_ocr_processor()
            if not ocr_processor.is_available():
                self.logger.warning(f"OCR not available for '{source_filename}'. Install with: pip install easyocr")
                return ""

            # Apply OCR with configuration limits
            ocr_text = ocr_processor.extract_text_from_pdf(
                pdf_path,
                max_pages=self.ocr_config.max_pages_for_ocr
            )

            if ocr_text.strip():
                self.logger.info(f"OCR extracted {len(ocr_text)} characters from '{source_filename}'")
                return ocr_text
            else:
                self.logger.warning(f"OCR returned empty text for '{source_filename}'")
                return ""

        except Exception as e:
            self.logger.error(f"OCR failed for '{source_filename}': {e}")
            return ""

    def _create_error_result(self, source_file: str, error_message: str) -> ExtractionResult:
        """Creates a standardized error result."""
        self.logger.error(f"Error in file '{source_file}': {error_message}")
        return ExtractionResult(
            source_file=source_file,
            content=None,
            success=False,
            error_message=error_message
        )