import logging
from pathlib import Path

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_project_directories():
    """Get project directories for organized structure."""
    project_root = Path(__file__).parent.parent  # Sobe um nível: src/ → root/
    raw_dir = project_root / "data" / "raw"
    extracted_dir = project_root / "data" / "extracted"

    # Create extracted directory if it doesn't exist
    extracted_dir.mkdir(parents=True, exist_ok=True)

    return raw_dir, extracted_dir

def discover_files_to_process(raw_dir, manager):
    """
    Discover all files in the organized structure.

    Returns:
        List of tuples: (input_path, output_path)
    """
    if not raw_dir.exists():
        logging.warning(f"Raw directory does not exist: {raw_dir}")
        return []

    files_to_process = []
    supported_extensions = set(manager.get_supported_extensions())

    # Scan organized structure: domain/category/files
    for domain_dir in raw_dir.iterdir():
        if not domain_dir.is_dir():
            continue

        for category_dir in domain_dir.iterdir():
            if not category_dir.is_dir():
                continue

            for file_path in category_dir.iterdir():
                if (file_path.is_file() and
                    file_path.suffix.lower() in supported_extensions):

                    # Calculate output path maintaining structure
                    relative_path = file_path.relative_to(raw_dir)
                    output_path = raw_dir.parent / "extracted" / relative_path.with_suffix('.json')

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

        logging.info(f"Processing: {domain}/{category}/{input_path.name}")

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file is supported
            if not manager.is_supported(input_path):
                logging.warning(f"Unsupported file type: {input_path.suffix}")
                results['failed'] += 1
                continue

            # Process file using manager (which creates extractor internally)
            success = manager.process_file(input_path, output_path.parent)

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
        from src.utils.folder_crawler import create_all_folders
        create_all_folders()
    except Exception as e:
        logging.warning(f"Could not update folder structure: {e}")

    try:
        # 1. Setup directories
        raw_dir, extracted_dir = get_project_directories()
        logging.info(f"Raw directory: {raw_dir}")
        logging.info(f"Extracted directory: {extracted_dir}")

        # 2. Initialize manager
        from src.managers.file_manager import FileTypeManager
        manager = FileTypeManager()

        # Check if extractors are available
        supported_extensions = manager.get_supported_extensions()
        if not supported_extensions:
            logging.error("No extractors available. Check dependencies installation.")
            return False

        logging.info(f"Supported extensions: {', '.join(supported_extensions)}")

        # 3. Discover files in organized structure
        files_to_process = discover_files_to_process(raw_dir, manager)

        if not files_to_process:
            logging.warning("No files found in organized structure")
            logging.info("Place files in: data/raw/DOMAIN/CATEGORY/")
            logging.info("Example: data/raw/TAX_AND_BANKING/W2_FORM/document.pdf")
            return True

        # 4. Process files maintaining structure
        logging.info(f"Processing {len(files_to_process)} files...")
        results = process_organized_files(files_to_process, manager)

        # 5. Display results
        total = results['success'] + results['failed']
        logging.info("Processing completed")
        logging.info(f"Total: {total} | Success: {results['success']} | Failed: {results['failed']}")
        logging.info(f"Results saved to: {extracted_dir}")

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