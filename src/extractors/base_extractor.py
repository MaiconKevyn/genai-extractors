"""
Base Extractor Module for Document Processing Pipeline

This module provides the base class and data structures for document extractors.

Classes:
    ExtractionResult: Data structure for extraction results
    BaseExtractor: Abstract base class for all document extractors
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Union, Optional
from abc import ABC, abstractmethod


@dataclass
class ExtractionResult:
    """
    Data structure for extraction results.

    Attributes:
        source_file (str): Original filename
        content (Optional[str]): Extracted text content, None if extraction failed
        success (bool): Whether extraction completed successfully
        error_message (Optional[str]): Error description if success=False
    """
    source_file: str
    content: Optional[str]
    success: bool
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.success and not self.content:
            self.success = False
            self.error_message = "Empty content despite success status"


class BaseExtractor(ABC):
    """
    Abstract base class for all document extractors.

    Provides shared functionality for logging, file validation, result persistence,
    and error handling.

    Abstract Methods:
        extract: Must be implemented by all concrete extractors
    """
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract(self, input_path: Union[str, Path]) -> ExtractionResult:
        """
        Extract content from a file.

        Args:
            input_path: Path to the document file

        Returns:
            ExtractionResult: Result containing extracted content or error info
        """

    def _extract_labels_from_path(self, file_path: Path) -> Optional[dict]:
        """
        Extract domain and category labels from file path structure.

        Args:
            file_path: Path to the document file

        Returns:
            dict with labels or None if invalid structure
        """
        try:
            # Load config
            config_path = Path(__file__).parent.parent / "utils" / "domain_and_class_structure.json"
            if not config_path.exists():
                return None

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Extract domain and category from path
            parts = file_path.parts
            if len(parts) < 3:
                return None

            category = parts[-2]  # Parent directory
            domain = parts[-3]  # Grandparent directory

            # Validate against configuration
            if domain not in config or category not in config[domain]:
                return None

            # Return labels
            return {
                "domain": domain,
                "category": category,
            }

        except Exception as e:
            self.logger.debug(f"Could not extract labels from {file_path}: {e}")
            return None

    def save_as_json(self, result: ExtractionResult, output_path: Union[str, Path],
                     source_path: Union[str, Path] = None) -> bool:
        """
        Save extraction result to JSON file.

        Args:
            result: The extraction result to save
            output_path: Target file path for JSON output

        Returns:
            bool: True if file was saved successfully, False otherwise
        """
        output_path = Path(output_path)

        if not result.success:
            self.logger.error(
                f"Cannot save result with error for '{result.source_file}'. "
                f"Reason: {result.error_message}"
            )
            return False

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Simple and clean JSON structure
            data_to_save = {
                "source_file": result.source_file,
                "content": result.content,
                "extraction_info": {
                    "success": result.success,
                    "content_length": len(result.content) if result.content else 0
                }
            }

            # Try to add labels automatically
            if source_path:
                labels = self._extract_labels_from_path(Path(source_path))
                if labels:
                    data_to_save["extraction_info"]["labels"] = labels
                    self.logger.info(f"Added labels: {labels['domain']}/{labels['category']}")

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Result saved: {output_path} ({len(result.content)} characters)")
            return True

        except Exception as e:
            self.logger.error(f"Error saving JSON to '{output_path}': {e}")
            return False

    def extract_and_save(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        """
        Extract content and save result to JSON.

        Args:
            input_path: Path to the input document
            output_path: Path for the JSON output file

        Returns:
            bool: True if extraction and save completed successfully
        """
        input_path = Path(input_path)
        self.logger.info(f"Starting extraction: {Path(input_path).name}")

        result = self.extract(input_path)

        if result.success:
            return self.save_as_json(result, output_path, source_path=input_path)
        else:
            self.logger.error(f"Extraction failed: {result.error_message}")
            return False

    def _create_error_result(self, source_file: str, error_message: str) -> ExtractionResult:
        """
        Create standardized error result.

        Args:
            source_file: Name of the source file that failed
            error_message: Error description

        Returns:
            ExtractionResult: Error result
        """
        self.logger.error(f"Error in file '{source_file}': {error_message}")
        return ExtractionResult(
            source_file=source_file,
            content=None,
            success=False,
            error_message=error_message
        )

    def _validate_file(self, file_path: Path, expected_extension: str) -> Optional[str]:
        """
        Perform standard file validation checks.

        Args:
            file_path: Path to the file to validate
            expected_extension: Expected file extension (e.g., '.pdf')

        Returns:
            Optional[str]: None if valid, error message if invalid
        """
        if not file_path.exists():
            return f"File not found: {file_path}"

        if file_path.suffix.lower() != expected_extension.lower():
            return f"File is not {expected_extension}: {file_path.suffix}"

        if file_path.stat().st_size == 0:
            return f"File is empty: {file_path}"

        return None

