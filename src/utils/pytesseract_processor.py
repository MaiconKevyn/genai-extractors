# src/utils/pytesseract_processor.py
"""
Processador de OCR utilizando pytesseract.
Requer que o Tesseract OCR esteja instalado no sistema.
"""
import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import Union, List, Optional
import tempfile
import os
import gc

# O Pytesseract requer a biblioteca Pillow para manipulação de imagens
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


class PytesseractProcessor:
    """
    Processador de OCR usando Pytesseract para extrair texto.
    Uma alternativa "drop-in" para o EasyOCRProcessor.
    """

    def __init__(self, languages: str = 'eng+por', gpu: bool = False):
        """
        Inicializa o processador.

        Args:
            languages: String de idiomas para o Tesseract (ex: 'eng+por' para inglês e português).
            gpu: Ignorado. Tesseract usa principalmente CPU.
        """
        self.languages = languages
        # Adicionar validação de instalação do Tesseract se necessário
        if not self.is_available():
            logger.error("Tesseract não parece estar instalado ou no PATH do sistema.")
            raise ImportError("Tesseract não encontrado.")
        logger.info(f"PytesseractProcessor inicializado com os idiomas: {self.languages}")

    def extract_text_from_pdf(self, pdf_path: Union[str, Path], max_pages: Optional[int] = None) -> str:
        """
        Extrai texto de PDF usando OCR, reutilizando a lógica de conversão para imagem.
        A estrutura deste método é idêntica à do EasyOCRProcessor.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.error(f"PDF não encontrado: {pdf_path}")
            return ""

        try:
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)
            pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
            logger.info(
                f"Iniciando OCR com Pytesseract em '{pdf_path.name}' - Processando {pages_to_process}/{total_pages} páginas")

            all_text = []
            for page_num in range(pages_to_process):
                # A lógica de processar página a página é a mesma
                page_text = self._process_single_page(doc, page_num, pdf_path.name)
                if page_text.strip():
                    all_text.append(page_text)
                if (page_num + 1) % 5 == 0:
                    gc.collect()

            doc.close()
            result_text = "\n\n".join(all_text)
            logger.info(f"OCR com Pytesseract concluído para '{pdf_path.name}'")
            return result_text
        except Exception as e:
            logger.error(f"Erro durante OCR com Pytesseract em '{pdf_path}': {e}")
            return ""

    def _process_single_page(self, doc, page_num: int, filename: str) -> str:
        """
        Processa uma única página, idêntico ao método no EasyOCRProcessor.
        """
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # Aumenta a resolução para melhor OCR

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            image_path = temp_file.name

        try:
            pix.save(image_path)
            pix = None  # Libera memória

            # A ÚNICA MUDANÇA REAL ESTÁ AQUI
            page_text = self._extract_text_from_image(image_path)

            logger.debug(
                f"Página {page_num + 1} de '{filename}': {len(page_text)} caracteres extraídos com Pytesseract")
            return page_text
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)

    def _extract_text_from_image(self, image_path: str) -> str:
        """
        Extrai texto de uma imagem usando Pytesseract.
        Esta é a principal substituição da lógica.
        """
        try:
            # Substitui a chamada do EasyOCR por esta linha
            return pytesseract.image_to_string(Image.open(image_path), lang=self.languages)
        except Exception as e:
            logger.error(f"Erro do Pytesseract ao extrair texto da imagem '{image_path}': {e}")
            return ""

    def extract_text_from_image_file(self, image_path: Union[str, Path]) -> str:
        """Extrai texto diretamente de um arquivo de imagem."""
        return self._extract_text_from_image(str(image_path))

    def is_available(self) -> bool:
        """Verifica se o comando do Tesseract está disponível."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except pytesseract.TesseractNotFoundError:
            return False