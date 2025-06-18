import logging
from pathlib import Path

from config.settings import RAW_DIR, EXTRACTED_DIR, LOGGING_CONFIG, ensure_directories
from src.utils.folder_crawler import create_folders
from src.managers.file_manager import FileTypeManager

# Basic logging configuration
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format']
)

def discover_files_to_process(manager):
    """
    Discover all files in the organized structure.

    Returns:
        List of tuples: (input_path, output_path)
    """
    if not RAW_DIR.exists():
        logging.warning(f"Raw directory does not exist: {RAW_DIR}")
        return []

    files_to_process = []
    supported_extensions = set(manager.get_supported_extensions())

    # Scan organized structure: domain/category/files
    for domain_dir in RAW_DIR.iterdir():
        if not domain_dir.is_dir():
            continue

        for category_dir in domain_dir.iterdir():
            if not category_dir.is_dir():
                continue

            for file_path in category_dir.iterdir():
                if (file_path.is_file() and
                        file_path.suffix.lower() in supported_extensions):
                    # Calculate output path maintaining structure
                    relative_path = file_path.relative_to(RAW_DIR)
                    output_path = EXTRACTED_DIR / relative_path.with_suffix('.json')

                    files_to_process.append((file_path, output_path))

    logging.info(f"Found {len(files_to_process)} files to process")
    return files_to_process


def process_organized_files(files_to_process, manager):
    """
    Process files maintaining the organized structure.

    Args:
        files_to_process: List of (input_path, output_path) tuples
        manager: FileTypeManager instance

    Returns:
        dict: Processing statistics
    """
    results = {'success': 0, 'failed': 0}

    for input_path, output_path in files_to_process:
        # Extract domain/category for logging
        parts = input_path.parts
        domain = parts[-3] if len(parts) >= 3 else "unknown"
        category = parts[-2] if len(parts) >= 2 else "unknown"

        logging.info(f"{'='*60}")
        logging.info(f"Processing: {domain}/{category}/{input_path.name}")
        logging.info(f"{'='*60}")

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file is supported
            if not manager.is_supported(input_path):
                logging.warning(f"Unsupported file type: {input_path.suffix}")
                results['failed'] += 1
                continue

            extractor = manager._create_extractor(input_path)

            if extractor is None:
                logging.warning(f"Could not create extractor for: {input_path.suffix}")
                results['failed'] += 1
                continue

            # Usar extract_and_save diretamente com o caminho exato
            success = extractor.extract_and_save(input_path, output_path)

            if success:
                results['success'] += 1
                logging.info(f"SUCCESS: {input_path.name} → {domain}/{category}")
            else:
                results['failed'] += 1
                logging.error(f"FAILED: {input_path.name}")

        except Exception as e:
            results['failed'] += 1
            logging.error(f"ERROR: {input_path.name} - {e}")

    return results


def main():
    logging.info("Starting Document Extraction System")

    try:
        ensure_directories()  # Usa função do settings
        create_folders()
    except Exception as e:
        logging.warning(f"Could not update folder structure: {e}")

    try:
        # 1. Setup directories
        logging.info(f"Raw directory: {RAW_DIR}")
        logging.info(f"Extracted directory: {EXTRACTED_DIR}")

        # 2. Initialize manager
        manager = FileTypeManager()

        # Check if extractors are available
        supported_extensions = manager.get_supported_extensions()
        if not supported_extensions:
            logging.error("No extractors available. Check dependencies installation.")
            return False

        logging.info(f"Supported extensions: {', '.join(supported_extensions)}")

        # 3. Discover files in organized structure
        files_to_process = discover_files_to_process(manager)

        if not files_to_process:
            logging.warning("No files found in organized structure")
            logging.info(f"Place files in: {RAW_DIR}/DOMAIN/CATEGORY/")
            return True

        # 4. Process files maintaining structure
        logging.info(f"Processing {len(files_to_process)} files...")
        results = process_organized_files(files_to_process, manager)

        # 5. Display results
        total = results['success'] + results['failed']
        logging.info(f"{'='*60}")
        logging.info("Processing completed")
        logging.info(f"Total: {total} | Success: {results['success']} | Failed: {results['failed']}")
        logging.info(f"Results saved to: {EXTRACTED_DIR}")
        logging.info(f"{'='*60}")

        return results['failed'] == 0

    except Exception as e:
        logging.error(f"Critical error: {e}")
        return False


if __name__ == "__main__":
    import sys

    try:
        success = main()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        sys.exit(1)