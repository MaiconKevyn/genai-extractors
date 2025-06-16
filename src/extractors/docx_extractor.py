import docx  # python-docx library
import zipfile
import tempfile
import os
from pathlib import Path
from typing import Union
from PIL import Image
from io import BytesIO

from .base_extractor import BaseExtractor, ExtractionResult


class DocxExtractor(BaseExtractor):
    """
    Extrai texto de arquivos .docx com sampling para arquivos grandes e OCR para imagens.
    Versão simplificada sem configurações complexas.
    """

    def __init__(self):
        super().__init__()

        # Configurações diretas e simples
        self.PARAGRAPH_LIMIT_FOR_SAMPLING = 180
        self.PARAGRAPHS_TO_SAMPLE = 90
        self.OCR_LANGUAGES = ['en', 'pt']
        self.OCR_USE_GPU = False

        # Componentes inicializados sob demanda
        self.ocr_processor = None

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extrai texto de DOCX seguindo mesmo padrão do PDF:
        1. Extração padrão → 2. Análise de qualidade → 3. OCR se necessário

        Args:
            input_path: Caminho para o arquivo DOCX

        Returns:
            ExtractionResult com conteúdo extraído
        """
        docx_path = Path(input_path)
        source_filename = docx_path.name

        # Validações básicas
        if not docx_path.exists():
            return self._create_error_result(source_filename, f"Arquivo não encontrado: {docx_path}")

        if docx_path.suffix.lower() != '.docx':
            return self._create_error_result(source_filename, f"Arquivo não é DOCX: {docx_path.suffix}")

        try:
            # ETAPA 1: Extração padrão de texto
            extracted_text = self._extract_standard_text(docx_path, source_filename)

            # ETAPA 2: Verifica se precisa de OCR usando heurística simples
            if self._needs_ocr(extracted_text):
                self.logger.info(f"Qualidade ruim detectada para '{source_filename}'. Aplicando OCR...")

                # ETAPA 3: Aplicar OCR
                ocr_text = self._apply_ocr_extraction(docx_path, source_filename)

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

    def _extract_standard_text(self, docx_path: Path, source_filename: str) -> str:
        """Extrai texto usando método padrão (python-docx)."""
        document = docx.Document(str(docx_path))
        paragraphs = document.paragraphs
        num_paragraphs = len(paragraphs)

        full_text_parts = []

        # Lógica de sampling para documentos grandes
        if num_paragraphs > self.PARAGRAPH_LIMIT_FOR_SAMPLING:
            self.logger.info(
                f"'{source_filename}' tem {num_paragraphs} parágrafos. "
                f"Fazendo sampling dos primeiros {self.PARAGRAPHS_TO_SAMPLE} e últimos {self.PARAGRAPHS_TO_SAMPLE}."
            )

            # Extrai primeiros parágrafos
            for i in range(min(self.PARAGRAPHS_TO_SAMPLE, len(paragraphs))):
                if paragraphs[i].text.strip():
                    full_text_parts.append(paragraphs[i].text)

            # Adiciona separador
            full_text_parts.append("\n\n... (conteúdo de parágrafos intermediários omitido) ...\n\n")

            # Extrai últimos parágrafos
            start_last_paragraphs = max(0, num_paragraphs - self.PARAGRAPHS_TO_SAMPLE)
            for i in range(start_last_paragraphs, num_paragraphs):
                if paragraphs[i].text.strip():
                    full_text_parts.append(paragraphs[i].text)

        else:
            self.logger.info(f"'{source_filename}' tem {num_paragraphs} parágrafos. Extraindo todo o conteúdo.")

            # Extrai texto de todos os parágrafos
            for para in paragraphs:
                if para.text.strip():
                    full_text_parts.append(para.text)

            # Extrai texto de todas as tabelas
            if document.tables:
                for table in document.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                full_text_parts.append(cell.text)

        return "\n\n".join(full_text_parts)

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

    def _apply_ocr_extraction(self, docx_path: Path, source_filename: str) -> str:
        """Aplica OCR para extrair texto de imagens no DOCX."""
        try:
            ocr_processor = self._get_ocr_processor()
            if not ocr_processor or not ocr_processor.is_available():
                self.logger.warning(f"OCR não disponível para '{source_filename}'. Instale com: pip install easyocr")
                return ""

            # Extrai imagens do DOCX e aplica OCR
            image_texts = []

            # DOCX é um arquivo ZIP - extrai imagens diretamente
            with zipfile.ZipFile(docx_path, 'r') as zip_file:
                media_files = [f for f in zip_file.namelist() if f.startswith('word/media/')]

                for media_file in media_files:
                    if any(media_file.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
                        try:
                            image_data = zip_file.read(media_file)

                            # Salva em arquivo temporário e aplica OCR
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
                            self.logger.warning(f"Falha ao processar imagem {media_file}: {e}")
                            continue

            result_text = "\n\n".join(image_texts)

            if result_text:
                self.logger.info(f"OCR extraiu {len(result_text)} caracteres de imagens em '{source_filename}'")
                return result_text
            else:
                self.logger.warning(f"Nenhum texto encontrado em imagens de '{source_filename}'")
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