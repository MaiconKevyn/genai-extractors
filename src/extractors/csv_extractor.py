"""
CSV Data Extraction Module

This module provides optimized text extraction capabilities for CSV (Comma-Separated Values)
files with intelligent character-based sampling for large datasets.

Classes:
    CSVTextExtractor: Streamlined class for high-performance CSV text extraction

"""

import csv
from pathlib import Path
from typing import Union
from .base_extractor import BaseExtractor, ExtractionResult

class CSVTextExtractor(BaseExtractor):
    """
    This class provides a simplified, high-speed approach to extracting text content
    from CSV files. It uses character-based sampling instead of complex row analysis,
    achieving superior performance characteristics suitable for high-volume data
    processing workflows and analytics pipelines.

    Attributes:
        MAX_TOTAL_CHARACTERS (int): Maximum character limit for extracted content.
            Files exceeding this limit will be intelligently sampled to maintain
            this size constraint while preserving content representativeness.

    """

    MAX_TOTAL_CHARACTERS = 30000  # Approximate size limit (~10 pages)

    def __init__(self):
        """ Initialize the CSV extractor configuration. """
        super().__init__()

    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extract text content from CSV files with streamlined character-based processing.

        Args:
            input_path (Union[str, Path]): Path to the CSV file to process.
                Accepts both string paths and Path objects for maximum flexibility.
                Must point to an existing, readable CSV file.

        Returns:
            ExtractionResult: Streamlined result object containing:
                - source_file: Original filename for tracking
                - content: Extracted text content with consistent size (None if failed)
                - success: Boolean extraction status
                - error_message: Detailed error information if extraction failed

        Raises:
            No exceptions are raised. All errors are caught and returned
            as failed ExtractionResult objects with descriptive error messages.

        """
        csv_path = Path(input_path)
        source_filename = csv_path.name

        if not csv_path.exists():
            return self._create_error_result(source_filename, f"File not found: {csv_path}")

        if csv_path.suffix.lower() != '.csv':
            return self._create_error_result(source_filename, f"File is not CSV: {csv_path.suffix}")

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                lines = [' '.join(row).strip() for row in reader if any(row)]

            full_text = "\n".join(lines)

            # Check if the total character count exceeds the limit
            if len(full_text) <= self.MAX_TOTAL_CHARACTERS:
                # No sampling needed, return full text
                sampled_text = full_text
            else:
                # Content is too large, sample the text
                sampled_text = self._sample_text(lines)

            return ExtractionResult(
                source_file=source_filename,
                content=sampled_text,
                success=True
            )

        except Exception as e:
            return self._create_error_result(source_filename, str(e))

    def _sample_text(self, lines: list[str]) -> str:
        """
        Extract text content from CSV files with streamlined character-based processing.

        Args:
            lines (List[str]): Complete list of processed text lines from CSV

        Returns:
            str: Sampled content with clear boundary preservation and sampling indicator.
                Total character count will not exceed MAX_TOTAL_CHARACTERS.


        """
        half_limit = self.MAX_TOTAL_CHARACTERS // 2
        start, end = [], []

        # Collect lines from the start until half limit is reached
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

        # Combine start and end with ellipsis in the middle
        return "\n".join(start + ["..."] + end)