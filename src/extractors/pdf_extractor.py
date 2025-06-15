import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import Union

# Import the base class and the unified result
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
        # Constant to define the page limit
        self.PAGE_LIMIT_FOR_SAMPLING = 10
        self.PAGES_TO_SAMPLE = 5
        self.quality_analyzer = TextQualityAnalyzer()
        self.ocr_processor = None  # Lazy loading

    def _get_ocr_processor(self) -> EasyOCRProcessor:
        """Lazy loading do OCR processor."""
        if self.ocr_processor is None:
            try:
                # Importa configurações do OCR
                from config.settings import OCR_CONFIG
                self.ocr_processor = EasyOCRProcessor(
                    languages=OCR_CONFIG.languages,
                    gpu=OCR_CONFIG.use_gpu
                )
            except ImportError:
                self.logger.warning("⚠️  OCR config not found, using defaults")
                self.ocr_processor = EasyOCRProcessor(languages=['en', 'pt'])
        return self.ocr_processor

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts text from a PDF. If the PDF has more than 10 pages,
        extracts only the first 5 and the last 5. Otherwise, extracts all pages.
        Automatically applies OCR if text quality is poor.
        """
        pdf_path = Path(input_path)
        source_filename = pdf_path.name

        if not pdf_path.exists():
            return self._create_error_result(source_filename, f"File not found: {pdf_path}")

        if pdf_path.suffix.lower() != '.pdf':
            return self._create_error_result(source_filename, f"File is not a PDF: {pdf_path.suffix}")

        try:
            # STEP 1: Extração de texto padrão
            extracted_text = self._extract_standard_text(pdf_path, source_filename)

            # STEP 2: Análise de qualidade
            quality_report = self.quality_analyzer.analyze_quality(extracted_text)

            # STEP 3: Decide se aplica OCR
            if quality_report['needs_ocr']:
                self.logger.info(f"🔍 Poor quality detected for '{source_filename}'. Applying OCR...")
                ocr_text = self._apply_ocr_extraction(pdf_path, source_filename)

                if ocr_text and len(ocr_text.strip()) > len(extracted_text.strip()):
                    self.logger.info(f"✅ OCR improved text quality for '{source_filename}'")
                    extracted_text = ocr_text
                else:
                    self.logger.warning(f"⚠️  OCR did not improve quality for '{source_filename}'")

            # STEP 4: Log final da qualidade
            final_quality = self.quality_analyzer.analyze_quality(extracted_text)
            self.logger.info(
                f"📊 Final quality for '{source_filename}': {final_quality['quality_level']} (score: {final_quality['quality_score']:.1f})")

            return ExtractionResult(
                source_file=source_filename,
                content=extracted_text,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, str(e))

    def _extract_standard_text(self, pdf_path: Path, source_filename: str) -> str:
        """Extrai texto usando método padrão (PyMuPDF)."""
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        page_texts = []

        # Lógica de sampling para arquivos grandes (mantida do código original)
        if total_pages > self.PAGE_LIMIT_FOR_SAMPLING:
            self.logger.info(
                f"'{source_filename}' has {total_pages} pages. "
                f"Extracting the first {self.PAGES_TO_SAMPLE} and the last {self.PAGES_TO_SAMPLE}."
            )

            # Extrai as primeiras páginas
            for i in range(self.PAGES_TO_SAMPLE):
                page_texts.append(doc[i].get_text("text").strip())

            # Adiciona separador
            page_texts.append("\n\n... (content from intermediate pages omitted) ...\n\n")

            # Extrai as últimas páginas
            start_last_pages = total_pages - self.PAGES_TO_SAMPLE
            for i in range(start_last_pages, total_pages):
                page_texts.append(doc[i].get_text("text").strip())

        else:
            # Lógica para arquivos pequenos
            self.logger.info(f"'{source_filename}' has {total_pages} pages. Extracting all content.")
            page_texts = [page.get_text("text").strip() for page in doc]

        doc.close()
        return "\n\n".join(filter(None, page_texts))

    def _apply_ocr_extraction(self, pdf_path: Path, source_filename: str) -> str:
        """Aplica OCR para extrair texto do PDF."""
        try:
            # Verifica se OCR está disponível
            ocr_processor = self._get_ocr_processor()
            if not ocr_processor.is_available():
                self.logger.warning(f"⚠️  OCR not available for '{source_filename}'. Install with: pip install easyocr")
                return ""

            # Aplica OCR
            ocr_text = ocr_processor.extract_text_from_pdf(pdf_path)

            if ocr_text.strip():
                self.logger.info(f"✅ OCR extracted {len(ocr_text)} characters from '{source_filename}'")
                return ocr_text
            else:
                self.logger.warning(f"⚠️  OCR returned empty text for '{source_filename}'")
                return ""

        except ImportError as e:
            self.logger.warning(f"⚠️  OCR dependencies missing for '{source_filename}': {e}")
            return ""
        except Exception as e:
            self.logger.error(f"❌ OCR failed for '{source_filename}': {e}")
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