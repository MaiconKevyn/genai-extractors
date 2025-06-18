"""
Folder Crawler for Document Classification

Simple script to create folder structure and discover documents
based on src/utils/supported_domain_and_category.json configuration.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get project root directory (genai-extractors/)."""
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


def create_folder_structure(base_dir: Path, config: Dict[str, Dict[str, str]]) -> None:
    """
    Create folder structure based on configuration.

    Args:
        base_dir: Base directory (data/raw or data/extracted)
        config: Domain and category configuration
    """
    logger.info(f"Creating folder structure in: {base_dir}")

    # Ensure base directory exists
    base_dir.mkdir(parents=True, exist_ok=True)

    folders_created = 0

    for domain_name, categories in config.items():
        # Create domain folder
        domain_path = base_dir / domain_name
        domain_path.mkdir(exist_ok=True)

        for category_name in categories.keys():
            # Create category folder
            category_path = domain_path / category_name
            category_path.mkdir(exist_ok=True)
            folders_created += 1

            logger.debug(f"Created: {domain_name}/{category_name}")

    logger.info(f"Created {folders_created} category folders in {base_dir}")


def create_all_folders() -> None:
    """Create complete folder structure for raw and extracted directories."""
    # Get project root (genai-extractors/)
    project_root = get_project_root()

    # Define paths
    raw_dir = project_root / "data" / "raw"
    extracted_dir = project_root / "data" / "extracted"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Raw directory: {raw_dir}")
    logger.info(f"Extracted directory: {extracted_dir}")

    # Load configuration
    config = load_config()

    # Create structures
    create_folder_structure(raw_dir, config)
    create_folder_structure(extracted_dir, config)

    # Summary
    total_domains = len(config)
    total_categories = sum(len(categories) for categories in config.values())

    logger.info(f"""
FOLDER STRUCTURE CREATED:
   • {total_domains} domains
   • {total_categories} categories  
   • {total_categories * 2} total folders created (raw + extracted)

STRUCTURE:
   • Raw documents: {raw_dir}
   • Processed results: {extracted_dir}

NEXT STEPS:
   1. Place documents in data/raw/DOMAIN/CATEGORY/ folders
   2. Run document classification system
""")


def discover_documents(raw_dir: Path = None) -> List[Tuple[str, str, Path]]:
    """
    Discover all documents in the folder structure.

    Args:
        raw_dir: Raw directory path (defaults to data/raw)

    Returns:
        List of tuples: (domain, category, file_path)
    """
    if raw_dir is None:
        project_root = get_project_root()
        raw_dir = project_root / "data" / "raw"

    if not raw_dir.exists():
        logger.warning(f"Raw directory doesn't exist: {raw_dir}")
        return []

    # Load config to validate structure
    config = load_config()

    # Supported file extensions
    supported_extensions = {'.pdf', '.docx', '.xlsx', '.csv', '.xls'}

    documents = []

    # Crawl each domain
    for domain_name in config.keys():
        domain_path = raw_dir / domain_name

        if not domain_path.exists():
            logger.warning(f"Domain folder not found: {domain_path}")
            continue

        # Crawl each category
        for category_name in config[domain_name].keys():
            category_path = domain_path / category_name

            if not category_path.exists():
                logger.warning(f"Category folder not found: {category_path}")
                continue

            # Find documents in category
            for file_path in category_path.iterdir():
                if (file_path.is_file() and
                        file_path.suffix.lower() in supported_extensions):
                    documents.append((domain_name, category_name, file_path))
                    logger.debug(f"Found: {domain_name}/{category_name}/{file_path.name}")

    logger.info(f"Discovered {len(documents)} documents")
    return documents


def show_statistics(documents: List[Tuple[str, str, Path]]) -> None:
    """Show statistics about discovered documents."""
    if not documents:
        logger.info("No documents found")
        return

    # Count by domain
    domain_counts = {}
    # Count by extension
    extension_counts = {}

    for domain, category, file_path in documents:
        # Domain counts
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Extension counts
        ext = file_path.suffix.lower()
        extension_counts[ext] = extension_counts.get(ext, 0) + 1

    logger.info(f"""
DOCUMENT STATISTICS:
   • Total documents: {len(documents)}
   • Total domains with documents: {len(domain_counts)}

BY DOMAIN:""")

    for domain, count in sorted(domain_counts.items()):
        logger.info(f"   • {domain}: {count} documents")

    logger.info(f"""
BY FILE TYPE:""")
    for ext, count in sorted(extension_counts.items()):
        logger.info(f"   • {ext}: {count} files")


def validate_structure(raw_dir: Path = None) -> bool:
    """
    Validate that folder structure matches configuration.

    Returns:
        True if structure is valid, False otherwise
    """
    if raw_dir is None:
        project_root = get_project_root()
        raw_dir = project_root / "data" / "raw"

    config = load_config()
    errors = []

    if not raw_dir.exists():
        errors.append(f"Raw directory doesn't exist: {raw_dir}")
        return False

    # Check each domain and category
    for domain_name, categories in config.items():
        domain_path = raw_dir / domain_name

        if not domain_path.exists():
            errors.append(f"Missing domain folder: {domain_name}")
            continue

        for category_name in categories.keys():
            category_path = domain_path / category_name

            if not category_path.exists():
                errors.append(f"Missing category folder: {domain_name}/{category_name}")

    if errors:
        logger.error(f"Structure validation failed:")
        for error in errors:
            logger.error(f"   • {error}")
        return False
    else:
        logger.info("Folder structure is valid")
        return True


# Command-line interface
def main():
    """Main function for command-line usage."""
    import sys

    if len(sys.argv) < 2:
        print("""
Usage: python src/utils/folder_crawler.py <command>

Commands:
  create    - Create folder structure from configuration
  discover  - Discover documents in existing structure  
  validate  - Validate folder structure
  stats     - Show document statistics
        """)
        return

    command = sys.argv[1].lower()

    try:
        if command == "create":
            create_all_folders()

        elif command == "discover":
            documents = discover_documents()
            if documents:
                logger.info(f"Found {len(documents)} documents:")
                for domain, category, file_path in documents[:10]:  # Show first 10
                    logger.info(f"  • {domain}/{category}/{file_path.name}")
                if len(documents) > 10:
                    logger.info(f"  ... and {len(documents) - 10} more")

        elif command == "validate":
            is_valid = validate_structure()
            sys.exit(0 if is_valid else 1)

        elif command == "stats":
            documents = discover_documents()
            show_statistics(documents)

        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()