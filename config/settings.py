from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class ExtractorConfig:
    """Configuration for text extraction"""
    output_format: str = "json"  # "json" or "markdown"
    include_images: bool = False
    include_metadata: bool = True
    supported_extensions: List[str] = None

    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = ['.pdf']


# Global configuration
EXTRACTOR_CONFIG = ExtractorConfig()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# Create directories if they don't exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Debug: print paths for verification
if __name__ == "__main__":
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"INPUT_DIR: {INPUT_DIR}")
    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    print(f"INPUT_DIR exists: {INPUT_DIR.exists()}")
    print(f"Default output format: {EXTRACTOR_CONFIG.output_format}")
    print(f"Include metadata: {EXTRACTOR_CONFIG.include_metadata}")
    print(f"Supported extensions: {EXTRACTOR_CONFIG.supported_extensions}")