import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import Union, List, Optional
import tempfile
import os

logger = logging.getLogger(__name__)


class EasyOCRProcessor:
    """
    Processador OCR usando EasyOCR para extrair texto de documentos escaneados.
    Mantém interface simples e modular conforme padrões do projeto.
    """

    def __init__(self, languages: List[str] = None, gpu: bool = False):
        """
        Inicializa o processador OCR.

        Args:
            languages: Lista de idiomas para reconhecimento (['en', 'pt'])
            gpu: Se deve usar GPU (False por padrão para compatibilidade)
        """
        self.languages = languages or ['en', 'pt']
        self.gpu = gpu
        self._reader = None

    def _get_reader(self):
        """Lazy loading do EasyOCR reader."""
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(self.languages, gpu=self.gpu)
                logger.info(f"✅ EasyOCR initialized with languages: {self.languages}")
            except ImportError:
                logger.error("❌ EasyOCR not installed. Install with: pip install easyocr")
                raise ImportError("EasyOCR not available. Install with: pip install easyocr")
        return self._reader

    def extract_text_from_pdf(self, pdf_path: Union[str, Path]) -> str:
        """
        Extrai texto de PDF usando OCR.

        Args:
            pdf_path: Caminho para o arquivo PDF

        Returns:
            Texto extraído via OCR
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF não encontrado: {pdf_path}")
            return ""

        try:
            # Abre o PDF e converte páginas em imagens
            doc = fitz.open(str(pdf_path))
            all_text = []

            logger.info(f"🔍 Iniciando OCR em '{pdf_path.name}' ({len(doc)} páginas)")

            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

                # Salva a imagem temporária corretamente
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    image_path = temp_file.name
                    pix.save(image_path)

                try:
                    # Faz o OCR
                    page_text = self._extract_text_from_image(image_path)
                    if page_text.strip():
                        all_text.append(page_text)
                finally:
                    # Limpa o arquivo depois
                    if os.path.exists(image_path):
                        os.remove(image_path)

            doc.close()

            result_text = "\n\n".join(all_text)
            logger.info(f"✅ OCR concluído para '{pdf_path.name}' - {len(result_text)} caracteres extraídos")

            return result_text

        except Exception as e:
            logger.error(f"❌ Erro durante OCR de '{pdf_path}': {e}")
            return ""

    def _extract_text_from_image(self, image_path: str) -> str:
        """
        Extrai texto de uma imagem usando EasyOCR.

        Args:
            image_path: Caminho para a imagem

        Returns:
            Texto extraído
        """
        try:
            reader = self._get_reader()

            # EasyOCR retorna lista de [bbox, text, confidence]
            results = reader.readtext(image_path)

            # Extrai apenas o texto, filtrando por confiança mínima
            texts = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Filtro de confiança mínima
                    texts.append(text)

            return " ".join(texts)

        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto da imagem '{image_path}': {e}")
            return ""

    def is_available(self) -> bool:
        """
        Verifica se o EasyOCR está disponível.

        Returns:
            True se EasyOCR estiver instalado e funcional
        """
        try:
            import easyocr
            return True
        except ImportError:
            return False


def validate_ocr_dependencies() -> dict:
    """
    Valida dependências do OCR (substitui a função do settings.py).

    Returns:
        Dict com status das dependências
    """
    status = {
        'easyocr_available': False,
        'pymupdf_available': False,
        'opencv_available': False  # EasyOCR pode usar OpenCV para preprocessing
    }

    # Verifica EasyOCR
    try:
        import easyocr
        status['easyocr_available'] = True
    except ImportError:
        pass

    # Verifica PyMuPDF (para conversão PDF->imagem)
    try:
        import fitz
        status['pymupdf_available'] = True
    except ImportError:
        pass

    # Verifica OpenCV (opcional, para preprocessing)
    try:
        import cv2
        status['opencv_available'] = True
    except ImportError:
        pass

    return status