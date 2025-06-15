# src/utils/ocr_handler.py

import logging
import io
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import fitz  # PyMuPDF
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Resultado de uma operação OCR."""
    success: bool
    text: str
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    method_used: str = "pytesseract"
    error_message: Optional[str] = None
    pages_processed: int = 0


class TesseractOCRHandler:
    """
    Handler para OCR usando Tesseract via pytesseract.
    Versão básica que será expandida gradualmente.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o handler OCR.

        Args:
            config: Configurações OCR (vem do settings.py)
        """
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Validação de dependências
        self.dependencies_ok = self._check_dependencies()

        if not self.dependencies_ok:
            self.logger.error("❌ OCR dependencies not available. Install: pip install pytesseract pillow")

    def _get_default_config(self) -> Dict[str, Any]:
        """Configurações padrão caso não sejam fornecidas."""
        return {
            'enabled': True,
            'language': 'eng+por',
            'dpi_scale': 2.0,
            'timeout_per_page': 30,
            'max_pages_for_ocr': 20,
            'tesseract_cmd': 'tesseract',
            'custom_config': '--oem 3 --psm 6'
        }

    def _check_dependencies(self) -> bool:
        """Verifica se as dependências OCR estão disponíveis."""
        try:
            import pytesseract
            from PIL import Image
            return True
        except ImportError as e:
            self.logger.error(f"Missing OCR dependencies: {e}")
            return False

    def is_available(self) -> bool:
        """Retorna True se OCR estiver disponível."""
        return self.dependencies_ok and self.config.get('enabled', True)

    def extract_text_from_pdf(self, pdf_path: Union[str, Path], page_limit: Optional[int] = None) -> OCRResult:
        """
        Extrai texto de um PDF usando OCR.

        Args:
            pdf_path: Caminho para o PDF
            page_limit: Limite de páginas a processar (None = todas)

        Returns:
            OCRResult com o texto extraído
        """
        if not self.is_available():
            return OCRResult(
                success=False,
                text="",
                error_message="OCR not available - missing dependencies",
                method_used="none"
            )

        try:
            import pytesseract
            from PIL import Image
            import time

            start_time = time.time()

            self.logger.info(f"🔍 Starting OCR extraction for '{Path(pdf_path).name}'")

            # Abre o PDF
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)

            # Determina quantas páginas processar
            max_pages = page_limit or self.config.get('max_pages_for_ocr', 20)
            pages_to_process = min(total_pages, max_pages)

            if total_pages > max_pages:
                self.logger.warning(f"⚠️  PDF has {total_pages} pages, processing only {pages_to_process}")

            extracted_texts = []

            # Processa cada página
            for page_num in range(pages_to_process):
                try:
                    self.logger.info(f"🔍 Processing page {page_num + 1}/{pages_to_process}")

                    # Converte página para imagem
                    page = doc[page_num]

                    # Aplica escala DPI para melhor qualidade
                    scale = self.config.get('dpi_scale', 2.0)
                    matrix = fitz.Matrix(scale, scale)
                    pix = page.get_pixmap(matrix=matrix)

                    # Converte para PIL Image
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))

                    # Executa OCR
                    ocr_config = self.config.get('custom_config', '--oem 3 --psm 6')
                    pytesseract.pytesseract.tesseract_cmd = self.config.get('tesseract_cmd', 'tesseract')

                    page_text = pytesseract.image_to_string(
                        image,
                        lang=self.config.get('language', 'eng'),
                        config=ocr_config,
                        timeout=self.config.get('timeout_per_page', 30)
                    )

                    if page_text.strip():
                        extracted_texts.append(f"--- PAGE {page_num + 1} ---\n{page_text.strip()}")
                        self.logger.info(f"✅ Page {page_num + 1}: extracted {len(page_text.strip())} chars")
                    else:
                        self.logger.warning(f"⚠️  Page {page_num + 1}: no text extracted")

                except Exception as e:
                    self.logger.error(f"❌ Error processing page {page_num + 1}: {e}")
                    extracted_texts.append(f"--- PAGE {page_num + 1} ---\n[OCR ERROR: {str(e)}]")

            doc.close()

            # Combina todo o texto
            full_text = "\n\n".join(extracted_texts)
            processing_time = time.time() - start_time

            self.logger.info(f"✅ OCR completed: {len(full_text)} chars in {processing_time:.1f}s")

            return OCRResult(
                success=True,
                text=full_text,
                processing_time=processing_time,
                method_used="pytesseract",
                pages_processed=pages_to_process
            )

        except Exception as e:
            error_msg = f"OCR extraction failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")

            return OCRResult(
                success=False,
                text="",
                error_message=error_msg,
                method_used="pytesseract"
            )

    def extract_text_from_image(self, image_path: Union[str, Path]) -> OCRResult:
        """
        Extrai texto de uma imagem usando OCR.

        Args:
            image_path: Caminho para a imagem

        Returns:
            OCRResult com o texto extraído
        """
        if not self.is_available():
            return OCRResult(
                success=False,
                text="",
                error_message="OCR not available - missing dependencies",
                method_used="none"
            )

        try:
            import pytesseract
            from PIL import Image
            import time

            start_time = time.time()

            self.logger.info(f"🔍 Starting OCR for image '{Path(image_path).name}'")

            # Carrega a imagem
            image = Image.open(image_path)

            # Executa OCR
            ocr_config = self.config.get('custom_config', '--oem 3 --psm 6')
            pytesseract.pytesseract.tesseract_cmd = self.config.get('tesseract_cmd', 'tesseract')

            text = pytesseract.image_to_string(
                image,
                lang=self.config.get('language', 'eng'),
                config=ocr_config,
                timeout=self.config.get('timeout_per_page', 30)
            )

            processing_time = time.time() - start_time

            self.logger.info(f"✅ Image OCR completed: {len(text)} chars in {processing_time:.1f}s")

            return OCRResult(
                success=True,
                text=text,
                processing_time=processing_time,
                method_used="pytesseract",
                pages_processed=1
            )

        except Exception as e:
            error_msg = f"Image OCR failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")

            return OCRResult(
                success=False,
                text="",
                error_message=error_msg,
                method_used="pytesseract"
            )

    def test_ocr_availability(self) -> Dict[str, Any]:
        """
        Testa se OCR está funcionando corretamente.

        Returns:
            Dict com status de disponibilidade e teste
        """
        result = {
            'dependencies_ok': self.dependencies_ok,
            'config_valid': bool(self.config),
            'tesseract_working': False,
            'test_text': "",
            'error_message': None
        }

        if not self.is_available():
            result['error_message'] = "OCR dependencies not available"
            return result

        try:
            import pytesseract
            from PIL import Image
            import numpy as np

            # Cria uma imagem de teste simples
            test_image = Image.new('RGB', (200, 50), color='white')

            # Adiciona texto de teste usando drawing (muito básico)
            # Em produção, seria melhor usar uma imagem real de teste

            # Testa OCR
            pytesseract.pytesseract.tesseract_cmd = self.config.get('tesseract_cmd', 'tesseract')
            test_text = pytesseract.image_to_string(
                test_image,
                lang='eng',
                config='--psm 6',
                timeout=10
            )

            result['tesseract_working'] = True
            result['test_text'] = test_text.strip()

            self.logger.info("✅ OCR test passed")

        except Exception as e:
            result['error_message'] = str(e)
            self.logger.error(f"❌ OCR test failed: {e}")

        return result


# 🧪 Função para teste rápido
def quick_ocr_test():
    """Teste rápido da funcionalidade OCR."""
    print("🧪 Testing OCR Handler...")

    # Configuração básica
    config = {
        'enabled': True,
        'language': 'eng+por',
        'dpi_scale': 2.0,
        'tesseract_cmd': 'tesseract'
    }

    # Cria handler
    ocr_handler = TesseractOCRHandler(config)

    # Testa disponibilidade
    test_result = ocr_handler.test_ocr_availability()

    print(f"📊 OCR Test Results:")
    for key, value in test_result.items():
        print(f"   {key}: {value}")

    print(f"\n✅ OCR Available: {ocr_handler.is_available()}")

    return ocr_handler


if __name__ == "__main__":
    quick_ocr_test()