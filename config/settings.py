from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class ExtractorConfig:
    """
    Configuration for document extraction system.

    Attributes:
        output_format (str): Output format ("json" or "markdown")
        include_metadata (bool): Whether to include extraction metadata
        supported_extensions (List[str]): File extensions supported by extractors
    """
    output_format: str = "json"  # "json" or "markdown"
    include_metadata: bool = True
    supported_extensions: List[str] = None

    def __post_init__(self):
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