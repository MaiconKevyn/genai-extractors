import docx  # Imports the python-docx library
import logging
from pathlib import Path
from typing import Union
import zipfile
import tempfile
import os
from PIL import Image
from io import BytesIO

# Imports the base class and unified result
from .base_extractor import BaseExtractor, ExtractionResult
from ..utils.text_quality import TextQualityAnalyzer
from ..utils.ocr_processor import EasyOCRProcessor


class DocxExtractor(BaseExtractor):
    """Extracts text from .docx, with sampling for large files and OCR for images when needed."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Import OCR configuration (same pattern as PDF extractor)
        try:
            from config.settings import OCR_CONFIG
            self.ocr_config = OCR_CONFIG
        except ImportError:
            self.logger.warning("OCR configuration not found, using defaults")

            class DefaultOCRConfig:
                enabled = True
                languages = ['en', 'pt']
                use_gpu = False

            self.ocr_config = DefaultOCRConfig()

        # Constants for sampling logic
        self.PARAGRAPH_LIMIT_FOR_SAMPLING = 180
        self.PARAGRAPHS_TO_SAMPLE = 90

        # OCR components (same as PDF extractor)
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
        Extracts text from a .docx. Same pattern as PDF extractor:
        1. Standard extraction, 2. Quality analysis, 3. OCR if needed
        """
        docx_path = Path(input_path)
        source_filename = docx_path.name

        if not docx_path.exists():
            return self._create_error_result(source_filename, f"File not found: {docx_path}")

        if docx_path.suffix.lower() != '.docx':
            return self._create_error_result(source_filename, f"File is not a .docx: {docx_path.suffix}")

        try:
            # STEP 1: Standard text extraction (same as before)
            extracted_text = self._extract_standard_text(docx_path, source_filename)

            # STEP 2: Quality analysis (same as PDF)
            quality_report = self.quality_analyzer.analyze_quality(extracted_text)

            # STEP 3: Decide whether to apply OCR (same logic as PDF)
            if quality_report['needs_ocr'] and self.ocr_config.enabled:
                ocr_text = self._apply_ocr_extraction(docx_path, source_filename)

                if ocr_text and len(ocr_text.strip()) > len(extracted_text.strip()):
                    self.logger.info(f"OCR improved text quality for '{source_filename}'")
                    extracted_text = ocr_text
                else:
                    self.logger.warning(f"OCR did not improve quality for '{source_filename}', keeping original")

            return ExtractionResult(
                source_file=source_filename,
                content=extracted_text,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, str(e))

    def _extract_standard_text(self, docx_path: Path, source_filename: str) -> str:
        """Extracts text using standard method (same as before)."""
        document = docx.Document(str(docx_path))
        paragraphs = document.paragraphs
        num_paragraphs = len(paragraphs)

        full_text_parts = []

        # Sampling logic for large documents (unchanged)
        if num_paragraphs > self.PARAGRAPH_LIMIT_FOR_SAMPLING:
            self.logger.info(
                f"'{source_filename}' has {num_paragraphs} paragraphs. "
                f"Sampling the first {self.PARAGRAPHS_TO_SAMPLE} and the last {self.PARAGRAPHS_TO_SAMPLE}."
            )

            # Extract first paragraphs
            for i in range(min(self.PARAGRAPHS_TO_SAMPLE, len(paragraphs))):
                if paragraphs[i].text.strip():
                    full_text_parts.append(paragraphs[i].text)

            # Add separator
            full_text_parts.append("\n\n... (content of intermediate paragraphs omitted) ...\n\n")

            # Extract last paragraphs
            start_last_paragraphs = max(0, num_paragraphs - self.PARAGRAPHS_TO_SAMPLE)
            for i in range(start_last_paragraphs, num_paragraphs):
                if paragraphs[i].text.strip():
                    full_text_parts.append(paragraphs[i].text)

        else:
            self.logger.info(f"'{source_filename}' has {num_paragraphs} paragraphs. Extracting all content.")
            # Extract text from all paragraphs
            for para in paragraphs:
                if para.text.strip():
                    full_text_parts.append(para.text)

            # Extract text from all tables
            if document.tables:
                for table in document.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                full_text_parts.append(cell.text)

        return "\n\n".join(full_text_parts)

    def _apply_ocr_extraction(self, docx_path: Path, source_filename: str) -> str:
        """Applies OCR to extract text from images in DOCX."""
        try:
            ocr_processor = self._get_ocr_processor()
            if not ocr_processor.is_available():
                self.logger.warning(f"OCR not available for '{source_filename}'. Install with: pip install easyocr")
                return ""

            # Extract images from DOCX and apply OCR
            image_texts = []

            # DOCX is a ZIP file - extract images directly
            with zipfile.ZipFile(docx_path, 'r') as zip_file:
                media_files = [f for f in zip_file.namelist() if f.startswith('word/media/')]

                for media_file in media_files:
                    if any(media_file.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
                        try:
                            image_data = zip_file.read(media_file)

                            # Save to temp file and apply OCR
                            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                                image = Image.open(BytesIO(image_data))
                                if image.mode in ('RGBA', 'LA', 'P'):
                                    image = image.convert('RGB')
                                image.save(temp_file.name, 'PNG')
                                temp_path = temp_file.name

                            try:
                                text = ocr_processor.extract_text_from_image_file(temp_path)
                                if text.strip():
                                    image_texts.append(text)
                            finally:
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)

                        except Exception as e:
                            self.logger.warning(f"Failed to process image {media_file}: {e}")
                            continue

            result_text = "\n\n".join(image_texts)

            if result_text:
                self.logger.info(f"OCR extracted {len(result_text)} characters from images in '{source_filename}'")
                return result_text
            else:
                self.logger.warning(f"No text found in images of '{source_filename}'")
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