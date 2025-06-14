import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import Union

# Import the base class and the unified result
from .base_extractor import BaseExtractor, ExtractionResult


class PDFTextExtractor(BaseExtractor):
    """Extracts the full text from a PDF file, with special rules for long files."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Constant to define the page limit
        self.PAGE_LIMIT_FOR_SAMPLING = 10
        self.PAGES_TO_SAMPLE = 5

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts text from a PDF. If the PDF has more than 10 pages,
        extracts only the first 5 and the last 5. Otherwise, extracts all pages.
        """
        pdf_path = Path(input_path)
        source_filename = pdf_path.name

        if not pdf_path.exists():
            return self._create_error_result(source_filename, f"File not found: {pdf_path}")

        if pdf_path.suffix.lower() != '.pdf':
            return self._create_error_result(source_filename, f"File is not a PDF: {pdf_path.suffix}")

        try:
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)
            page_texts = []

            # IMPLEMENTATION OF THE NEW RULE
            if total_pages > self.PAGE_LIMIT_FOR_SAMPLING:
                self.logger.info(
                    f"'{source_filename}' has {total_pages} pages. "
                    f"Extracting the first {self.PAGES_TO_SAMPLE} and the last {self.PAGES_TO_SAMPLE}."
                )

                # Extracts the first 5 pages (indices 0 to 4)
                for i in range(self.PAGES_TO_SAMPLE):
                    page_texts.append(doc[i].get_text("text").strip())

                # Adds a separator to indicate skipped content
                page_texts.append("\n\n... (content from intermediate pages omitted) ...\n\n")

                # Extracts the last 5 pages
                start_last_pages = total_pages - self.PAGES_TO_SAMPLE
                for i in range(start_last_pages, total_pages):
                    page_texts.append(doc[i].get_text("text").strip())

            else:
                # Old logic for files with 10 pages or less
                self.logger.info(f"'{source_filename}' has {total_pages} pages. Extracting all content.")
                page_texts = [page.get_text("text").strip() for page in doc]

            # Joins all collected text into a single string
            full_content = "\n\n".join(filter(None, page_texts))

            doc.close()
            self.logger.info(f"Extraction from '{source_filename}' completed successfully.")

            return ExtractionResult(
                source_file=source_filename,
                content=full_content,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, str(e))

    def _create_error_result(self, source_file: str, error_message: str) -> ExtractionResult:
        """Creates a standardized error result."""
        self.logger.error(f"Error in file '{source_file}': {error_message}")
        return ExtractionResult(
            source_file=source_file,
            content=None,
            success=False,
            error_message=error_message
        )
