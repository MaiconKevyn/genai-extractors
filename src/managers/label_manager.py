"""
Label Manager for Document Classification

This module extracts document labels (domain and category) based on folder structure
and updates metadata in extracted JSON files.

Classes:
    LabelManager: Manages label extraction and metadata updates
"""

import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DocumentLabels:
    """
    Data structure for document labels.

    Attributes:
        domain (str): Domain category (e.g., 'TAX_AND_BANKING')
        category (str): Specific category (e.g., 'W2_FORM')
        domain_description (str): Description of the domain
        category_description (str): Description of the category
    """
    domain: str
    category: str
    domain_description: str
    category_description: str


class LabelManager:
    """
    Manages document labels based on folder structure.

    Extracts domain and category labels from file paths and updates
    metadata in extracted JSON files.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize LabelManager with configuration.

        Args:
            config_path: Path to domain_and_class_structure.json
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # Default config path
        if config_path is None:
            config_path = Path(__file__).parent.parent / "utils" / "domain_and_class_structure.json"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Dict[str, str]]:
        """Load domain and category configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.logger.info(f"Loaded {len(config)} domains with {sum(len(cats) for cats in config.values())} categories")
        return config

    def extract_labels_from_path(self, file_path: Path) -> Optional[DocumentLabels]:
        """
        Extract domain and category labels from file path.

        Expected path structure: .../domain/category/filename.ext

        Args:
            file_path: Path to the document file

        Returns:
            DocumentLabels if valid structure, None otherwise
        """
        try:
            # Get the parts of the path
            parts = file_path.parts

            # Find domain and category from path
            # Look for pattern: .../domain/category/filename
            if len(parts) < 3:
                self.logger.warning(f"Path too short to extract labels: {file_path}")
                return None

            # Extract domain and category (last 2 directories before filename)
            category = parts[-2]  # Parent directory
            domain = parts[-3]  # Grandparent directory

            # Validate against configuration
            if domain not in self.config:
                self.logger.warning(f"Unknown domain '{domain}' in path: {file_path}")
                return None

            if category not in self.config[domain]:
                self.logger.warning(f"Unknown category '{category}' in domain '{domain}': {file_path}")
                return None

            # Create labels with descriptions
            domain_categories = self.config[domain]
            domain_description = f"Domain containing {len(domain_categories)} document categories"
            category_description = domain_categories[category]

            labels = DocumentLabels(
                domain=domain,
                category=category,
                domain_description=domain_description,
                category_description=category_description
            )

            self.logger.debug(f"Extracted labels for {file_path.name}: {domain}/{category}")
            return labels

        except Exception as e:
            self.logger.error(f"Error extracting labels from {file_path}: {e}")
            return None

    def update_extracted_metadata(self, extracted_json_path: Path, labels: DocumentLabels) -> bool:
        """
        Update metadata in extracted JSON file with labels.

        Args:
            extracted_json_path: Path to the extracted JSON file
            labels: Document labels to add

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            if not extracted_json_path.exists():
                self.logger.error(f"Extracted file not found: {extracted_json_path}")
                return False

            # Read existing JSON
            with open(extracted_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Add labels to extraction_info
            if "extraction_info" not in data:
                data["extraction_info"] = {}

            data["extraction_info"]["labels"] = {
                "domain": labels.domain,
                "category": labels.category,
                "domain_description": labels.domain_description,
                "category_description": labels.category_description
            }

            # Write updated JSON
            with open(extracted_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Updated labels in {extracted_json_path.name}: {labels.domain}/{labels.category}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating metadata in {extracted_json_path}: {e}")
            return False

    def process_extracted_file(self, raw_file_path: Path, extracted_file_path: Path) -> bool:
        """
        Extract labels from raw file path and update extracted file metadata.

        Args:
            raw_file_path: Original file path in data/raw structure
            extracted_file_path: Corresponding JSON file in data/extracted

        Returns:
            bool: True if processing successful, False otherwise
        """
        # Extract labels from raw file path
        labels = self.extract_labels_from_path(raw_file_path)
        if not labels:
            return False

        # Update extracted file metadata
        return self.update_extracted_metadata(extracted_file_path, labels)

    def get_supported_domains(self) -> list[str]:
        """Get list of supported domains."""
        return list(self.config.keys())

    def get_domain_categories(self, domain: str) -> Dict[str, str]:
        """
        Get categories for a specific domain.

        Args:
            domain: Domain name

        Returns:
            Dict mapping category names to descriptions
        """
        return self.config.get(domain, {})

    def validate_structure(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate if file path follows expected structure.

        Args:
            file_path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        labels = self.extract_labels_from_path(file_path)
        if labels:
            return True, "Valid structure"
        else:
            return False, "Invalid domain/category structure"


# Convenience function for quick label extraction
def extract_labels(file_path: Path, config_path: Optional[Path] = None) -> Optional[DocumentLabels]:
    """
    Quick function to extract labels from a file path.

    Args:
        file_path: Path to the document file
        config_path: Optional path to configuration file

    Returns:
        DocumentLabels if successful, None otherwise
    """
    manager = LabelManager(config_path)
    return manager.extract_labels_from_path(file_path)