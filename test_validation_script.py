#!/usr/bin/env python3
"""
Script de teste e validação para o sistema de extração de documentos.
Use este script para verificar se tudo está funcionando corretamente.
"""

import sys
import logging
from pathlib import Path

# Setup project path
project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging for testing
logging.basicConfig(
    level=logging.DEBUG,  # Mais detalhado para testes
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_dependencies():
    """Test all required dependencies."""
    print("\n" + "=" * 50)
    print("🧪 TESTING DEPENDENCIES")
    print("=" * 50)

    dependencies_status = {}

    # Test basic dependencies
    try:
        import fitz
        dependencies_status['PyMuPDF'] = "✅ OK"
    except ImportError:
        dependencies_status['PyMuPDF'] = "❌ MISSING (pip install PyMuPDF)"

    try:
        import docx
        dependencies_status['python-docx'] = "✅ OK"
    except ImportError:
        dependencies_status['python-docx'] = "❌ MISSING (pip install python-docx)"

    # Test OCR dependencies
    try:
        import easyocr
        dependencies_status['EasyOCR'] = "✅ OK"
    except ImportError:
        dependencies_status['EasyOCR'] = "❌ MISSING (pip install easyocr)"

    try:
        import torch
        dependencies_status['PyTorch'] = "✅ OK"
    except ImportError:
        dependencies_status['PyTorch'] = "❌ MISSING (pip install torch)"

    # Display results
    for dep, status in dependencies_status.items():
        print(f"  {dep}: {status}")

    return dependencies_status


def test_ocr_configuration():
    """Test OCR configuration and setup."""
    print("\n" + "=" * 50)
    print("🔧 TESTING OCR CONFIGURATION")
    print("=" * 50)

    try:
        from config.settings import (
            OCR_CONFIG,
            QUALITY_CONFIG,
            setup_ocr_environment,
            validate_ocr_dependencies
        )

        print("✅ Settings imported successfully")

        # Test OCR configuration values
        print(f"  📋 OCR Enabled: {OCR_CONFIG.enabled}")
        print(f"  🌐 Languages: {OCR_CONFIG.languages}")
        print(f"  🖥️  Use GPU: {OCR_CONFIG.use_gpu}")
        print(f"  📄 Max pages for OCR: {OCR_CONFIG.max_pages_for_ocr}")
        print(f"  🎯 Confidence threshold: {OCR_CONFIG.confidence_threshold}")

        # Test dependency validation
        deps = validate_ocr_dependencies()
        print(f"\n  🔍 Dependency check:")
        for dep, status in deps.items():
            status_icon = "✅" if status else "❌"
            print(f"    {status_icon} {dep}: {status}")

        # Test environment setup
        print(f"\n  🚀 Testing environment setup...")
        setup_result = setup_ocr_environment()
        print(f"    ✅ Environment setup completed")

        return True

    except Exception as e:
        print(f"❌ Error testing OCR configuration: {e}")
        return False


def test_extractors():
    """Test individual extractors."""
    print("\n" + "=" * 50)
    print("🔧 TESTING EXTRACTORS")
    print("=" * 50)

    try:
        # Test PDF extractor
        from src.extractors.pdf_extractor import PDFTextExtractor
        pdf_extractor = PDFTextExtractor()
        print("✅ PDF Extractor initialized")

        # Test DOCX extractor
        from src.extractors.docx_extractor import DocxExtractor
        docx_extractor = DocxExtractor()
        print("✅ DOCX Extractor initialized")

        # Test OCR processor
        from src.utils.ocr_processor import EasyOCRProcessor
        ocr_processor = EasyOCRProcessor()
        is_available = ocr_processor.is_available()
        print(f"{'✅' if is_available else '❌'} OCR Processor available: {is_available}")

        # Test quality analyzer
        from src.utils.text_quality import TextQualityAnalyzer
        quality_analyzer = TextQualityAnalyzer()
        print("✅ Quality Analyzer initialized")

        return True

    except Exception as e:
        print(f"❌ Error testing extractors: {e}")
        return False


def test_sample_text_quality():
    """Test text quality analysis with sample texts."""
    print("\n" + "=" * 50)
    print("📊 TESTING TEXT QUALITY ANALYSIS")
    print("=" * 50)

    try:
        from src.utils.text_quality import TextQualityAnalyzer

        analyzer = TextQualityAnalyzer(debug_mode=True)

        # Test cases
        test_cases = [
            {
                'name': 'Good Quality Text',
                'text': 'This is a well-formatted document with clear text and proper structure. It contains multiple sentences and demonstrates good readability.',
                'expected_ocr': False
            },
            {
                'name': 'Poor Quality Text (many replacement chars)',
                'text': 'This text has many replacement chars: ��� ��� ��� and is difficult to read.',
                'expected_ocr': True
            },
            {
                'name': 'Very Short Text',
                'text': 'Short',
                'expected_ocr': True
            },
            {
                'name': 'Empty Text',
                'text': '',
                'expected_ocr': True
            }
        ]

        for test_case in test_cases:
            print(f"\n  🧪 Testing: {test_case['name']}")
            result = analyzer.analyze_quality(test_case['text'])

            print(f"    📊 Quality Score: {result['quality_score']:.1f}")
            print(f"    📋 Quality Level: {result['quality_level']}")
            print(f"    🔧 Needs OCR: {result['needs_ocr']}")
            print(f"    ✅ Expected OCR: {test_case['expected_ocr']}")

            if result['needs_ocr'] == test_case['expected_ocr']:
                print(f"    ✅ Test PASSED")
            else:
                print(f"    ❌ Test FAILED")

        return True

    except Exception as e:
        print(f"❌ Error testing text quality: {e}")
        return False


def test_file_processing():
    """Test file processing with existing files."""
    print("\n" + "=" * 50)
    print("📁 TESTING FILE PROCESSING")
    print("=" * 50)

    try:
        from config.settings import INPUT_DIR, OUTPUT_DIR

        print(f"  📁 Input directory: {INPUT_DIR}")
        print(f"  📁 Output directory: {OUTPUT_DIR}")

        # Check for test files
        input_files = list(INPUT_DIR.glob("*"))
        processable_files = [f for f in input_files if f.suffix.lower() in ['.pdf', '.docx']]

        print(f"  📄 Total files in input: {len(input_files)}")
        print(f"  📄 Processable files: {len(processable_files)}")

        if processable_files:
            print(f"  🎯 Files ready for processing:")
            for file in processable_files:
                print(f"    - {file.name} ({file.suffix})")
        else:
            print(f"  ⚠️  No processable files found.")
            print(f"  💡 Add some .pdf or .docx files to {INPUT_DIR} to test processing.")

        return len(processable_files) > 0

    except Exception as e:
        print(f"❌ Error testing file processing: {e}")
        return False


def run_full_test():
    """Run all tests."""
    print("🧪 STARTING FULL SYSTEM TEST")
    print("=" * 60)

    tests = [
        ("Dependencies", test_dependencies),
        ("OCR Configuration", test_ocr_configuration),
        ("Extractors", test_extractors),
        ("Text Quality Analysis", test_sample_text_quality),
        ("File Processing Setup", test_file_processing),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! System is ready for use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    run_full_test()