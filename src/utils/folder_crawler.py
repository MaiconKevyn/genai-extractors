"""
Simplified Folder Creator

Creates folder structure for raw and extracted directories
based on domain_and_class_structure.json configuration.
Only creates new folders if they don't exist.
"""

import json
import logging
from pathlib import Path
from typing import Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get project root directory."""
    # This file is in src/utils/, so project root is 2 levels up
    return Path(__file__).parent.parent.parent


def load_config() -> Dict[str, Dict[str, str]]:
    """Load domain and category configuration from JSON file."""
    config_path = Path(__file__).parent / "domain_and_class_structure.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    logger.info(f"Loaded {len(config)} domains with {sum(len(cats) for cats in config.values())} total categories")
    return config


def create_folder_structure(base_dir: Path, config: Dict[str, Dict[str, str]]) -> int:
    """
    Create folder structure based on configuration.
    Only creates folders that don't exist.

    Args:
        base_dir: Base directory (data/raw or data/extracted)
        config: Domain and category configuration

    Returns:
        int: Number of new folders created
    """
    logger.info(f"Checking folder structure in: {base_dir}")

    # Ensure base directory exists
    base_dir.mkdir(parents=True, exist_ok=True)

    folders_created = 0

    for domain_name, categories in config.items():
        # Create domain folder if it doesn't exist
        domain_path = base_dir / domain_name
        if not domain_path.exists():
            domain_path.mkdir()
            logger.info(f"Created domain folder: {domain_name}")

        for category_name in categories.keys():
            # Create category folder if it doesn't exist
            category_path = domain_path / category_name
            if not category_path.exists():
                category_path.mkdir()
                folders_created += 1
                logger.info(f"Created category folder: {domain_name}/{category_name}")

    if folders_created == 0:
        logger.info("All folders already exist - no changes needed")
    else:
        logger.info(f"Created {folders_created} new folders in {base_dir}")

    return folders_created


def create_all_folders() -> None:
    """Create complete folder structure for raw and extracted directories."""
    # Get project root
    project_root = get_project_root()

    # Define paths
    raw_dir = project_root / "data" / "raw"
    extracted_dir = project_root / "data" / "extracted"

    logger.info(f"Project root: {project_root}")

    # Load configuration
    config = load_config()

    # Create structures and count new folders
    raw_folders_created = create_folder_structure(raw_dir, config)
    extracted_folders_created = create_folder_structure(extracted_dir, config)

    # Summary
    total_domains = len(config)
    total_categories = sum(len(categories) for categories in config.values())
    total_created = raw_folders_created + extracted_folders_created

    if total_created > 0:
        logger.info(f"""
NEW FOLDERS CREATED:
   • Raw folders: {raw_folders_created}
   • Extracted folders: {extracted_folders_created}
   • Total new folders: {total_created}

CURRENT STRUCTURE:
   • {total_domains} domains
   • {total_categories} categories per directory
   • Raw documents: {raw_dir}
   • Processed results: {extracted_dir}
""")
    else:
        logger.info(f"""
FOLDER STRUCTURE UP TO DATE:
   • {total_domains} domains
   • {total_categories} categories
   • No new folders needed
""")


if __name__ == "__main__":
    """Simple command-line interface - only supports create."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1].lower() != "create":
        print(f"Unknown command: {sys.argv[1]}")
        print("Usage: python src/utils/folder_crawler.py [create]")
        print("Note: 'create' is the default action")
        sys.exit(1)

    try:
        create_all_folders()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)