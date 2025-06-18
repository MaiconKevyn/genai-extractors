import json
import logging
from pathlib import Path
from typing import Union, Optional
from abc import ABC, abstractmethod
from config.settings import get_config_path

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
    def extract(self, input_path: Union[str, Path]) -> Optional[str]:
        """
        Extract content from a file.

        Args:
            input_path: Path to the document file

        Returns:
            Optional[str]: Extracted text content if successful, None if extraction failed.
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
            config_path = get_config_path
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

    def save_as_json(self, content: str, source_filename: str, output_path: Union[str, Path],
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

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build JSON structure
            data_to_save = {
                "source_file": source_filename,
                "content": content,
                "extraction_info": {
                    "success": True,
                    "content_length": len(content)
                }
            }

            # Add labels if available
            if source_path:
                labels = self._extract_labels_from_path(Path(source_path))
                if labels:
                    data_to_save["extraction_info"]["labels"] = labels
                    self.logger.info(f"Added labels: {labels['domain']}/{labels['category']}")

            # Save to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Result saved: {output_path} ({len(content)} characters)")
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

        content = self.extract(input_path)

        if content is not None:
            # If successfully extracted, save it
            return self.save_as_json(content, input_path.name, output_path, source_path=input_path)
        else:
            # If failed, the error was already logged in extract()
            self.logger.error(f"Extraction failed for: {input_path.name}")
            return False

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
