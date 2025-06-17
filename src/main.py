"""
Document Extraction System Main Application

This module implements the main interface for document extraction operations.
Uses the existing architecture (FileTypeManager + Extractors) in a direct and efficient manner.
"""

import logging
from pathlib import Path

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_directories():
    """
    Configure input and output directories using project settings.

    Returns:
        tuple: (input_dir, output_dir) as Path objects
    """
    from config.settings import INPUT_DIR, OUTPUT_DIR

    # Ensure directories exist
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    return INPUT_DIR, OUTPUT_DIR


def get_files_to_process(input_dir, manager):
    """
    Identify supported files in the input directory.

    Args:
        input_dir (Path): Input directory path
        manager (FileTypeManager): File type manager instance

    Returns:
        list: List of supported files ready for processing
    """
    if not input_dir.exists():
        logging.warning(f"Input directory does not exist: {input_dir}")
        return []

    # List all files in directory
    all_files = [f for f in input_dir.iterdir() if f.is_file()]

    # Filter only supported files
    supported_files = [f for f in all_files if manager.is_supported(f)]

    # Log statistics
    logging.info(f"Found {len(all_files)} files, {len(supported_files)} supported")

    return supported_files


def process_documents(files, manager, output_dir):
    """
    Process document list using FileTypeManager.

    Args:
        files (list): List of files to process
        manager (FileTypeManager): File type manager instance
        output_dir (Path): Output directory path

    Returns:
        dict: Processing statistics containing success and failure counts
    """
    results = {'success': 0, 'failed': 0}

    for file_path in files:
        logging.info(f"Processing: {file_path.name}")

        try:
            success = manager.process_file(file_path, output_dir)

            if success:
                results['success'] += 1
                logging.info(f"SUCCESS: {file_path.name}")
            else:
                results['failed'] += 1
                logging.error(f"FAILED: {file_path.name}")

        except Exception as e:
            results['failed'] += 1
            logging.error(f"ERROR: {file_path.name} - {e}")

    return results


def main():
    """
    Main application function.

    Coordinates the complete extraction workflow:
    1. Configure directories
    2. Initialize file manager
    3. Identify files to process
    4. Execute extraction
    5. Display results
    """
    logging.info("Starting Document Extraction System")

    try:
        # 1. Configure directories
        input_dir, output_dir = setup_directories()
        logging.info(f"Input directory: {input_dir}")
        logging.info(f"Output directory: {output_dir}")

        # 2. Initialize manager (auto-registers available extractors)
        from src.managers.file_manager import FileTypeManager
        manager = FileTypeManager()

        # Check if extractors are available
        supported_extensions = manager.get_supported_extensions()
        if not supported_extensions:
            logging.error("No extractors available. Check dependencies installation.")
            return False

        logging.info(f"Supported extensions: {', '.join(supported_extensions)}")

        # 3. Identify files to process
        files_to_process = get_files_to_process(input_dir, manager)

        if not files_to_process:
            logging.warning("No supported files found")
            logging.info(f"Place files in: {input_dir}")
            return True

        # 4. Process documents
        logging.info(f"Processing {len(files_to_process)} files...")
        results = process_documents(files_to_process, manager, output_dir)

        # 5. Display results
        total = results['success'] + results['failed']
        logging.info("Processing completed")
        logging.info(f"Total: {total} | Success: {results['success']} | Failed: {results['failed']}")
        logging.info(f"Results saved to: {output_dir}")

        return results['failed'] == 0  # Return True if no failures occurred

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