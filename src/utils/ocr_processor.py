import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import Union, List, Optional
import tempfile
import os
import gc

logger = logging.getLogger(__name__)


class EasyOCRProcessor:
    """
    OCR processor using EasyOCR to extract text from scanned documents.
    Improved version with better memory management and configuration support.
    """

    def __init__(self, languages: List[str] = None, gpu: bool = False):
        """
        Initialize the OCR processor.

        Args:
            languages: List of languages for recognition (['en', 'pt'])
            gpu: Whether to use GPU (False by default for compatibility)
        """
        self.languages = languages or ['en', 'pt']
        self.gpu = gpu
        self._reader = None

        # Import configurations if available
        try:
            from config.settings import OCR_CONFIG
            self.confidence_threshold = OCR_CONFIG.confidence_threshold
            self.timeout_per_page = OCR_CONFIG.timeout_per_page
            self.dpi_scale = OCR_CONFIG.dpi_scale
        except ImportError:
            # Fallback configurations
            self.confidence_threshold = 0.5
            self.timeout_per_page = 30
            self.dpi_scale = 2.0

    def _get_reader(self):
        """Lazy loading of the EasyOCR reader."""
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(self.languages, gpu=self.gpu)
                logger.info(f"EasyOCR initialized with languages: {self.languages}")
            except ImportError:
                logger.error("EasyOCR not installed. Install with: pip install easyocr")
                raise ImportError("EasyOCR not available. Install with: pip install easyocr")
        return self._reader

    def extract_text_from_pdf(self, pdf_path: Union[str, Path], max_pages: Optional[int] = None) -> str:
        """
        Extract text from PDF using OCR with improved memory management.

        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to process (None = all pages)

        Returns:
            Text extracted via OCR
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return ""

        try:
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)

            # Determine pages to process
            pages_to_process = min(total_pages, max_pages) if max_pages else total_pages

            logger.info(f"Starting OCR on '{pdf_path.name}' - Processing {pages_to_process}/{total_pages} pages")

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
            logger.info(f"OCR completed for '{pdf_path.name}' - {len(result_text)} characters extracted")

            return result_text

        except Exception as e:
            logger.error(f"Error during OCR of '{pdf_path}': {e}")
            return ""

    def _process_single_page(self, doc, page_num: int, filename: str) -> str:
        """
        Process a single page with proper resource management.

        Args:
            doc: PyMuPDF document object
            page_num: Page number to process
            filename: Filename for logging

        Returns:
            Extracted text from the page
        """
        page = doc[page_num]

        # Create high-quality image with configurable DPI
        matrix = fitz.Matrix(self.dpi_scale, self.dpi_scale)
        pix = page.get_pixmap(matrix=matrix)

        # Use context manager for temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            image_path = temp_file.name

        try:
            # Save the image
            pix.save(image_path)

            # Free pixmap memory immediately
            pix = None

            # Perform OCR
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
        Extract text from an image using EasyOCR.

        Args:
            image_path: Path to the image

        Returns:
            Extracted text
        """
        try:
            reader = self._get_reader()

            # EasyOCR returns a list of [bbox, text, confidence]
            results = reader.readtext(image_path)

            # Extract only the text, filtering by minimum confidence
            texts = []
            for (bbox, text, confidence) in results:
                if confidence > self.confidence_threshold:
                    texts.append(text)

            return " ".join(texts)

        except Exception as e:
            logger.error(f"Error extracting text from image '{image_path}': {e}")
            return ""

    def is_available(self) -> bool:
        """
        Check if EasyOCR is available.

        Returns:
            True if EasyOCR is installed and functional
        """
        try:
            import easyocr
            return True
        except ImportError:
            return False

    def extract_text_from_image_file(self, image_path: Union[str, Path]) -> str:
        """
        Extract text directly from an image file.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text
        """
        image_path = Path(image_path)

        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return ""

        try:
            logger.info(f"Starting OCR on image '{image_path.name}'")
            text = self._extract_text_from_image(str(image_path))
            logger.info(f"OCR completed for '{image_path.name}' - {len(text)} characters extracted")
            return text
        except Exception as e:
            logger.error(f"Error during OCR of image '{image_path}': {e}")
            return ""


def validate_ocr_dependencies() -> dict:
    """
    Validate OCR dependencies.

    Returns:
        Dict with dependencies status
    """
    status = {
        'easyocr_available': False,
        'pymupdf_available': False,
        'opencv_available': False,
        'torch_available': False
    }

    # Check EasyOCR
    try:
        import easyocr
        status['easyocr_available'] = True
    except ImportError:
        pass

    # Check PyMuPDF (for PDF->image conversion)
    try:
        import fitz
        status['pymupdf_available'] = True
    except ImportError:
        pass

    # Check OpenCV (optional, for preprocessing)
    try:
        import cv2
        status['opencv_available'] = True
    except ImportError:
        pass

    # Check PyTorch (required by EasyOCR)
    try:
        import torch
        status['torch_available'] = True
    except ImportError:
        pass

    return status