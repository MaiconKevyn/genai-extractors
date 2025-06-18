"""
Microsoft Excel Data Extraction Module

This module provides specialized text extraction capabilities for Microsoft Excel
files (.xlsx, .xlsm, .xls formats).

Classes:
    XLSXTextExtractor: Main class for Excel text extraction with multi-sheet support

"""

import openpyxl  # For .xlsx, .xlsm
import xlrd      # For .xls
from pathlib import Path
from typing import Union

from .base_extractor import BaseExtractor, ExtractionResult


class XLSXTextExtractor(BaseExtractor):
    """
    Text extractor for Microsoft Excel workbooks.

    Extracts text content from Excel files by choosing the appropriate library
    based on file extension (.xls uses xlrd, others use openpyxl).
    Applies basic character-based sampling when content exceeds the limit.


    Attributes:
        MAX_TOTAL_CHARACTERS (int): Character limit for content extraction.
            Workbooks exceeding this limit will be intelligently sampled to maintain
            consistent output size and processing performance across all formats.

    """

    MAX_TOTAL_CHARACTERS = 30000  # Limit text to ~10 pages

    def __init__(self):
        super().__init__()

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
       Extract text content from Excel workbooks with universal format support. (.xlsx, .xlsm, .xls)

        Args:
            input_path: Path to Excel file

        Returns:
            ExtractionResult: Contains extracted text or error inf
        """
        excel_path = Path(input_path)
        source_filename = excel_path.name

        if not excel_path.exists():
            return self._create_error_result(source_filename, f"File not found: {excel_path}")

        suffix = excel_path.suffix.lower()
        if suffix not in ['.xlsx', '.xls', '.xlsm']:
            return self._create_error_result(source_filename, f"Unsupported Excel file type: {suffix}")

        # Determine the extraction method based on file type
        try:
            if suffix == '.xls':
                lines = self._extract_xls(excel_path)
            else:
                lines = self._extract_xlsx(excel_path)

            full_text = "\n".join(lines)

            if len(full_text) <= self.MAX_TOTAL_CHARACTERS:
                sampled_text = full_text
            else:
                sampled_text = self._sample_text(lines)

            return ExtractionResult(
                source_file=source_filename,
                content=sampled_text,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, str(e))

    def _extract_xlsx(self, path: Path) -> list[str]:
        """Extracts content from .xlsx/.xlsm using openpyxl."""
        wb = openpyxl.load_workbook(path, read_only=True)
        lines = []
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                line = ' '.join(str(cell) for cell in row if cell is not None).strip()
                if line:
                    lines.append(line)
        return lines

    def _extract_xls(self, path: Path) -> list[str]:
        """
        Extracts content from .xls using xlrd.

        Args:
            path (Path): Path to the .xlsx or .xlsm file

        Returns:
            List[str]: List of processed text lines from all sheets
        """
        wb = xlrd.open_workbook(path)
        lines = []
        for sheet in wb.sheets():
            for row_idx in range(sheet.nrows):
                row = sheet.row_values(row_idx)
                line = ' '.join(str(cell) for cell in row if cell != "").strip()
                if line:
                    lines.append(line)
        return lines

    def _sample_text(self, lines: list[str]) -> str:
        """
        Returns sampled text (start and end) if content is too large.

        Args:
            lines (List[str]): Complete list of processed text lines from all sheets

        Returns:
            str: Sampled content with clear boundary preservation and sampling indicator.
        """
        # Limit the total characters to half the maximum limit
        half_limit = self.MAX_TOTAL_CHARACTERS // 2
        start, end = [], []

        # Collect lines from the start until half  limit is reached
        char_count = 0
        for line in lines:
            if char_count + len(line) > half_limit:
                break
            start.append(line)
            char_count += len(line)

        # Collect lines from the end until half limit is reached
        char_count = 0
        for line in reversed(lines):
            if char_count + len(line) > half_limit:
                break
            end.insert(0, line)
            char_count += len(line)

        # Combine start and end with an ellipsis in the middle
        return "\n".join(start + ["..."] + end)