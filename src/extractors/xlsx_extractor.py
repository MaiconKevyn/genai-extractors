import openpyxl
import logging
from pathlib import Path
from typing import Union

# Imports the base class and unified result
from .base_extractor import BaseExtractor, ExtractionResult


class XlsxExtractor(BaseExtractor):
    """Extracts text from .xlsx files, with sampling for large files based on rows."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Constants for sampling logic (same pattern as CSV)
        self.ROW_LIMIT_FOR_SAMPLING = 1000  # Same as CSV
        self.ROWS_TO_SAMPLE = 500  # Same as CSV

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extracts text from a .xlsx. If the file has more than 1000 rows,
        extracts only the first 500 and the last 500 from each sheet.
        """
        xlsx_path = Path(input_path)
        source_filename = xlsx_path.name

        if not xlsx_path.exists():
            return self._create_error_result(source_filename, f"File not found: {xlsx_path}")

        if xlsx_path.suffix.lower() not in ['.xlsx', '.xlsm']:
            return self._create_error_result(source_filename, f"File is not a .xlsx/.xlsm: {xlsx_path.suffix}")

        try:
            # Open Excel file
            workbook = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
            sheet_names = workbook.sheetnames

            if not sheet_names:
                return self._create_error_result(source_filename, "XLSX file has no sheets")

            all_sheets_text = []

            # Process each sheet (similar to processing multiple tables in DOCX)
            for sheet_name in sheet_names:
                try:
                    sheet = workbook[sheet_name]
                    sheet_text = self._extract_sheet_text(sheet, sheet_name, source_filename)
                    if sheet_text.strip():
                        all_sheets_text.append(f"=== SHEET: {sheet_name} ===\n{sheet_text}")
                except Exception as e:
                    self.logger.warning(f"Error processing sheet '{sheet_name}' in '{source_filename}': {e}")
                    continue

            workbook.close()

            # Combine all sheets (same pattern as combining text parts)
            full_content = "\n\n".join(all_sheets_text)

            if not full_content.strip():
                return self._create_error_result(source_filename, "No content extracted from XLSX file")

            self.logger.info(f"Extraction of '{source_filename}' completed successfully.")

            return ExtractionResult(
                source_file=source_filename,
                content=full_content,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, f"Error processing file: {e}")

    def _extract_sheet_text(self, sheet, sheet_name: str, source_filename: str) -> str:
        """Extract text from a single sheet with sampling logic."""
        # Get all rows with data
        all_rows = []
        for row in sheet.iter_rows(values_only=True):
            # Skip completely empty rows
            if any(cell is not None and str(cell).strip() for cell in row):
                all_rows.append(row)

        num_rows = len(all_rows)

        if num_rows == 0:
            return ""

        full_text_parts = []

        # Sampling logic for large sheets (same pattern as CSV/DOCX)
        if num_rows > self.ROW_LIMIT_FOR_SAMPLING:
            self.logger.info(
                f"Sheet '{sheet_name}' in '{source_filename}' has {num_rows} rows. "
                f"Sampling the first {self.ROWS_TO_SAMPLE} and the last {self.ROWS_TO_SAMPLE}."
            )

            # Extract header (first row)
            if all_rows:
                header_row = " | ".join(str(cell) if cell is not None else "" for cell in all_rows[0])
                full_text_parts.append(f"HEADERS: {header_row}")

            # Extract first rows
            for i in range(1, min(self.ROWS_TO_SAMPLE + 1, len(all_rows))):
                row_text = " | ".join(str(cell) if cell is not None else "" for cell in all_rows[i])
                if row_text.strip():
                    full_text_parts.append(f"Row {i}: {row_text}")

            # Add separator
            full_text_parts.append("... (content of intermediate rows omitted) ...")

            # Extract last rows
            start_last_rows = max(1, num_rows - self.ROWS_TO_SAMPLE)
            for i in range(start_last_rows, num_rows):
                row_text = " | ".join(str(cell) if cell is not None else "" for cell in all_rows[i])
                if row_text.strip():
                    full_text_parts.append(f"Row {i}: {row_text}")

        else:
            # Default logic for small sheets (same pattern as others)
            self.logger.info(
                f"Sheet '{sheet_name}' in '{source_filename}' has {num_rows} rows. Extracting all content.")

            # Extract header
            if all_rows:
                header_row = " | ".join(str(cell) if cell is not None else "" for cell in all_rows[0])
                full_text_parts.append(f"HEADERS: {header_row}")

            # Extract all data rows
            for i, row in enumerate(all_rows[1:], 1):
                row_text = " | ".join(str(cell) if cell is not None else "" for cell in row)
                if row_text.strip():
                    full_text_parts.append(f"Row {i}: {row_text}")

        return "\n".join(full_text_parts)

    def _create_error_result(self, source_file: str, error_message: str) -> ExtractionResult:
        """Creates a standardized error result."""
        self.logger.error(f"Error in file '{source_file}': {error_message}")
        return ExtractionResult(
            source_file=source_file,
            content=None,
            success=False,
            error_message=error_message
        )