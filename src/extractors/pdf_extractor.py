import fitz  # PyMuPDF
from pathlib import Path
from typing import Union

from .base_extractor import BaseExtractor, ExtractionResult


class PDFTextExtractor(BaseExtractor):
    """
    Extrai texto completo de arquivos PDF com regras para arquivos grandes.
    Aplica OCR automaticamente quando qualidade do texto é ruim.
    Versão simplificada sem configurações complexas.
    """

    def __init__(self):
        super().__init__()

        # Configurações diretas e simples
        self.PAGE_LIMIT_FOR_SAMPLING = 10
        self.PAGES_TO_SAMPLE = 5
        self.OCR_MAX_PAGES = 20
        self.OCR_LANGUAGES = ['en', 'pt']
        self.OCR_USE_GPU = False

        # Componentes inicializados sob demanda
        self.ocr_processor = None

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extrai texto de PDF com aplicação inteligente de OCR.
        Processo: 1. Extração padrão → 2. Análise de qualidade → 3. OCR se necessário

        Args:
            input_path: Caminho para o arquivo PDF

        Returns:
            ExtractionResult com conteúdo extraído
        """
        pdf_path = Path(input_path)
        source_filename = pdf_path.name

        # Validações básicas
        if not pdf_path.exists():
            return self._create_error_result(source_filename, f"Arquivo não encontrado: {pdf_path}")

        if pdf_path.suffix.lower() != '.pdf':
            return self._create_error_result(source_filename, f"Arquivo não é PDF: {pdf_path.suffix}")

        try:
            # ETAPA 1: Extração padrão de texto
            extracted_text = self._extract_standard_text(pdf_path, source_filename)

            # ETAPA 2: Verifica se precisa de OCR usando heurística simples
            if self._needs_ocr(extracted_text):
                self.logger.info(f"Qualidade ruim detectada para '{source_filename}'. Aplicando OCR...")

                # ETAPA 3: Aplicar OCR
                ocr_text = self._apply_ocr_extraction(pdf_path, source_filename)

                if ocr_text and len(ocr_text.strip()) > len(extracted_text.strip()):
                    self.logger.info(f"OCR melhorou qualidade do texto para '{source_filename}'")
                    extracted_text = ocr_text
                else:
                    self.logger.warning(f"OCR não melhorou qualidade para '{source_filename}', mantendo original")

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

        # Lógica de sampling para arquivos grandes
        if total_pages > self.PAGE_LIMIT_FOR_SAMPLING:
            self.logger.info(
                f"'{source_filename}' tem {total_pages} páginas. "
                f"Extraindo as primeiras {self.PAGES_TO_SAMPLE} e últimas {self.PAGES_TO_SAMPLE}."
            )

            # Extrai primeiras páginas
            for i in range(self.PAGES_TO_SAMPLE):
                page_texts.append(doc[i].get_text("text").strip())

            # Adiciona separador
            page_texts.append("\n\n... (conteúdo de páginas intermediárias omitido) ...\n\n")

            # Extrai últimas páginas
            start_last_pages = total_pages - self.PAGES_TO_SAMPLE
            for i in range(start_last_pages, total_pages):
                page_texts.append(doc[i].get_text("text").strip())

        else:
            # Lógica para arquivos pequenos
            self.logger.info(f"'{source_filename}' tem {total_pages} páginas. Extraindo todo o conteúdo.")
            page_texts = [page.get_text("text").strip() for page in doc]

        doc.close()
        return "\n\n".join(filter(None, page_texts))

    def _needs_ocr(self, text: str) -> bool:
        """
        Verifica se o texto extraído precisa de OCR usando heurística simples.

        Args:
            text: Texto extraído

        Returns:
            bool: True se precisar de OCR
        """
        try:
            from ..utils.text_quality import needs_ocr
            return needs_ocr(text)
        except ImportError:
            # Fallback simples se o módulo não estiver disponível
            return not text or len(text.strip()) < 50

    def _apply_ocr_extraction(self, pdf_path: Path, source_filename: str) -> str:
        """Aplica OCR para extrair texto do PDF."""
        try:
            ocr_processor = self._get_ocr_processor()
            if not ocr_processor or not ocr_processor.is_available():
                self.logger.warning(f"OCR não disponível para '{source_filename}'. Instale com: pip install easyocr")
                return ""

            # Verifica limite de páginas para OCR
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)
            doc.close()

            if total_pages > self.OCR_MAX_PAGES:
                self.logger.warning(
                    f"'{source_filename}' tem {total_pages} páginas, excedendo limite de OCR de "
                    f"{self.OCR_MAX_PAGES}. Aplicando OCR apenas nas primeiras {self.OCR_MAX_PAGES} páginas."
                )

            # Aplica OCR com limite de páginas
            ocr_text = ocr_processor.extract_text_from_pdf(pdf_path, max_pages=self.OCR_MAX_PAGES)

            if ocr_text.strip():
                self.logger.info(f"OCR extraiu {len(ocr_text)} caracteres de '{source_filename}'")
                return ocr_text
            else:
                self.logger.warning(f"OCR retornou texto vazio para '{source_filename}'")
                return ""

        except Exception as e:
            self.logger.error(f"OCR falhou para '{source_filename}': {e}")
            return ""

    def _get_ocr_processor(self):
        """Inicialização lazy do processador OCR."""
        if self.ocr_processor is None:
            try:
                from ..utils.ocr_processor import EasyOCRProcessor
                self.ocr_processor = EasyOCRProcessor(
                    languages=self.OCR_LANGUAGES,
                    gpu=self.OCR_USE_GPU
                )
            except ImportError:
                self.logger.warning("EasyOCRProcessor não disponível. Instale com: pip install easyocr")
                self.ocr_processor = None
        return self.ocr_processor