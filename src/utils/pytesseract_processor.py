import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import Union, Optional
import tempfile
import os
import gc

logger = logging.getLogger(__name__)


class PytesseractProcessor:
    """
    OCR processor using Tesseract to extract text from scanned documents.
    Simpler and more lightweight alternative to EasyOCR.
    """

    def __init__(self, languages: str = 'eng+por', config: str = '--psm 3'):
        """
        Initialize the Tesseract OCR processor.

        Args:
            languages: Languages for recognition ('eng+por' for English+Portuguese)
            config: Tesseract configuration string (PSM = Page Segmentation Mode)
        """
        self.languages = languages
        self.config = config

        # Try to import and configure pytesseract
        try:
            import pytesseract
            from PIL import Image
            self.pytesseract = pytesseract
            self.Image = Image
            self._available = True

            # Test if tesseract is available
            try:
                pytesseract.get_tesseract_version()
                logger.info(f"Tesseract OCR initialized with languages: {languages}")
            except Exception as e:
                logger.error(f"Tesseract not found: {e}")
                self._available = False

        except ImportError:
            logger.error("pytesseract not installed. Install with: pip install pytesseract")
            self._available = False
            self.pytesseract = None
            self.Image = None

    def extract_text_from_pdf(self, pdf_path: Union[str, Path], max_pages: Optional[int] = None) -> str:
        """
        Extract text from PDF using OCR with Tesseract.

        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to process (None = all pages)

        Returns:
            Text extracted via OCR
        """
        if not self.is_available():
            logger.error("Tesseract OCR not available")
            return ""

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return ""

        try:
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)

            # Determine pages to process
            pages_to_process = min(total_pages, max_pages) if max_pages else total_pages

            logger.info(
                f"Starting Tesseract OCR on '{pdf_path.name}' - Processing {pages_to_process}/{total_pages} pages")

            all_text = []

            for page_num in range(pages_to_process):
                try:
                    page_text = self._process_single_page(doc, page_num, pdf_path.name)
                    if page_text.strip():
                        all_text.append(page_text)

                    # Force garbage collection every 5 pages to manage memory
                    if (page_num + 1) % 5 == 0:
                        gc.collect()

                except Exception as e:
                    logger.warning(f"Failed to process page {page_num + 1} of '{pdf_path.name}': {e}")
                    continue

            doc.close()

            result_text = "\n\n".join(all_text)
            logger.info(f"Tesseract OCR completed for '{pdf_path.name}' - {len(result_text)} characters extracted")

            return result_text

        except Exception as e:
            logger.error(f"Error during Tesseract OCR of '{pdf_path}': {e}")
            return ""

    def _process_single_page(self, doc, page_num: int, filename: str) -> str:
        """
        Process a single page with Tesseract OCR.

        Args:
            doc: PyMuPDF document object
            page_num: Page number to process
            filename: Filename for logging

        Returns:
            Extracted text from the page
        """
        page = doc[page_num]

        # Create high-quality image (300 DPI equivalent)
        matrix = fitz.Matrix(2.0, 2.0)  # 2x scale = ~300 DPI
        pix = page.get_pixmap(matrix=matrix)

        # Use context manager for temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            image_path = temp_file.name

        try:
            # Save the image
            pix.save(image_path)

            # Free pixmap memory immediately
            pix = None

            # Perform OCR with Tesseract
            page_text = self._extract_text_from_image(image_path)

            logger.debug(f"Page {page_num + 1} of '{filename}': {len(page_text)} characters extracted")

            return page_text

        finally:
            # Always clean up the temporary file
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError as e:
                    logger.warning(f"Could not remove temporary file {image_path}: {e}")

    def _extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from an image using Tesseract OCR.

        Args:
            image_path: Path to the image

        Returns:
            Extracted text
        """
        try:
            # Load image
            image = self.Image.open(image_path)

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')

            # Extract text using Tesseract
            text = self.pytesseract.image_to_string(
                image,
                lang=self.languages,
                config=self.config
            )

            # Clean up the text
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from image '{image_path}': {e}")
            return ""

    def is_available(self) -> bool:
        """
        Check if Tesseract OCR is available.

        Returns:
            True if Tesseract is installed and functional
        """
        return self._available

    def extract_text_from_image_file(self, image_path: Union[str, Path]) -> str:
        """
        Extract text directly from an image file using Tesseract.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text
        """
        if not self.is_available():
            logger.error("Tesseract OCR not available")
            return ""

        image_path = Path(image_path)

        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return ""

        try:
            logger.info(f"Starting Tesseract OCR on image '{image_path.name}'")
            text = self._extract_text_from_image(str(image_path))
            logger.info(f"Tesseract OCR completed for '{image_path.name}' - {len(text)} characters extracted")
            return text
        except Exception as e:
            logger.error(f"Error during Tesseract OCR of image '{image_path}': {e}")
            return ""


def validate_tesseract_dependencies() -> dict:
    """
    Validate Tesseract OCR dependencies.

    Returns:
        Dict with dependencies status
    """
    status = {
        'pytesseract_available': False,
        'tesseract_executable': False,
        'pymupdf_available': False,
        'pillow_available': False
    }

    # Check pytesseract
    try:
        import pytesseract
        status['pytesseract_available'] = True

        # Check if tesseract executable is available
        try:
            pytesseract.get_tesseract_version()
            status['tesseract_executable'] = True
        except Exception:
            pass

    except ImportError:
        pass

    # Check PyMuPDF (for PDF->image conversion)
    try:
        import fitz
        status['pymupdf_available'] = True
    except ImportError:
        pass

    # Check Pillow (for image processing)
    try:
        from PIL import Image
        status['pillow_available'] = True
    except ImportError:
        pass

    return status