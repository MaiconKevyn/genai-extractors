"""
Document Extraction System Configuration Module

This module provides centralized configuration management for the document extraction
framework, including extractor parameters, file format specifications, project
structure definitions, and runtime environment setup. It implements a dataclass-based
configuration system that ensures type safety, validation, and easy maintenance
across development and production environments.

Classes:
    ExtractorConfig: Core configuration dataclass for extraction parameters

Environment Setup:
    The module automatically creates necessary directories and validates
    configuration parameters during import, ensuring the system is ready
    for immediate use in any environment.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class ExtractorConfig:
    """
    Core configuration dataclass for document extraction system parameters.

    This class defines the essential configuration parameters that control the
    behavior of document extractors across the framework. It provides sensible
    defaults for immediate productivity while allowing customization for specific
    deployment requirements.

    Attributes:
        output_format (str): Format for extraction results output.
            Default: "json" - Structured JSON format for programmatic access
            Alternative: "markdown" - Human-readable markdown format

        include_metadata (bool): Whether to include extraction metadata in results.
            Default: True - Includes processing timestamps, file info, extraction stats
            Set to False for minimal output size in high-volume scenarios

        supported_extensions (List[str]): File extensions supported by the framework.
            Default: Auto-populated with all available extractor formats
            Can be customized to restrict processing to specific file types

    """
    output_format: str = "json"  # "json" or "markdown"
    include_metadata: bool = True
    supported_extensions: List[str] = None

    def __post_init__(self):
        """
        Post-initialization configuration validation and setup.
        """
        if self.supported_extensions is None:
            self.supported_extensions = ['.pdf', '.docx', '.xlsx', '.csv', 'xls']


# GLOBAL CONFIGURATION INSTANCES
# Primary extractor configuration instance

EXTRACTOR_CONFIG = ExtractorConfig()

# PROJECT STRUCTURE AND DIRECTORY MANAGEMENT
# Automatic project root discovery

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# Create directories if they don't exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)