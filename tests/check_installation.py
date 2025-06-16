#!/usr/bin/env python3
"""
Script rápido para verificar se todas as dependências estão instaladas corretamente.
"""

import sys
import subprocess
from pathlib import Path


def check_python_packages():
    """Verifica se os pacotes Python estão instalados."""
    print("🐍 Verificando pacotes Python...")

    packages = {
        'pytesseract': 'OCR com Tesseract',
        'PIL': 'Processamento de imagens (Pillow)',
        'fitz': 'Processamento de PDF (PyMuPDF)',
        'docx': 'Processamento de DOCX (python-docx)',
        'pandas': 'Processamento de dados (CSV/Excel)',
        'openpyxl': 'Processamento de Excel'
    }

    installed = {}

    for package, description in packages.items():
        try:
            if package == 'PIL':
                from PIL import Image
            elif package == 'fitz':
                import fitz
            elif package == 'docx':
                import docx
            else:
                __import__(package)

            installed[package] = True
            print(f"   ✅ {package} - {description}")

        except ImportError:
            installed[package] = False
            print(f"   ❌ {package} - {description} (pip install {package})")

    return installed


def check_tesseract_executable():
    """Verifica se o executável do Tesseract está disponível."""
    print("\n🔍 Verificando executável Tesseract...")

    try:
        # Tenta executar tesseract --version
        result = subprocess.run(['tesseract', '--version'],
                                capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   ✅ Tesseract encontrado: {version_line}")

            # Verifica idiomas disponíveis
            lang_result = subprocess.run(['tesseract', '--list-langs'],
                                         capture_output=True, text=True, timeout=10)

            if lang_result.returncode == 0:
                languages = lang_result.stdout.strip().split('\n')[1:]  # Remove primeira linha
                print(f"   📋 Idiomas disponíveis: {', '.join(languages[:10])}")

                if 'eng' in languages and 'por' in languages:
                    print(f"   ✅ Idiomas necessários (eng, por) disponíveis")
                    return True
                else:
                    print(f"   ⚠️  Idiomas eng/por podem não estar disponíveis")
                    return True
            else:
                print(f"   ⚠️  Não foi possível listar idiomas")
                return True
        else:
            print(f"   ❌ Tesseract não funciona: {result.stderr}")
            return False

    except FileNotFoundError:
        print(f"   ❌ Tesseract não encontrado no PATH")
        print(f"   💡 Instale com:")
        print(f"      Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-por")
        print(f"      macOS: brew install tesseract")
        print(f"      Windows: baixe de https://github.com/UB-Mannheim/tesseract/wiki")
        return False

    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout ao executar Tesseract")
        return False

    except Exception as e:
        print(f"   ❌ Erro inesperado: {e}")
        return False


def test_ocr_functionality():
    """Testa funcionalidade básica do OCR."""
    print("\n🧪 Testando funcionalidade OCR...")

    try:
        from src.utils.pytesseract_processor import PytesseractProcessor

        processor = PytesseractProcessor()

        if processor.is_available():
            print(f"   ✅ PytesseractProcessor inicializado com sucesso")
            print(f"   📋 Configuração: languages='{processor.languages}', config='{processor.config}'")
            return True
        else:
            print(f"   ❌ PytesseractProcessor não está disponível")
            return False

    except ImportError as e:
        print(f"   ❌ Erro ao importar PytesseractProcessor: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erro inesperado: {e}")
        return False


def check_project_structure():
    """Verifica se a estrutura do projeto está correta."""
    print("\n📁 Verificando estrutura do projeto...")

    required_paths = [
        'src/extractors',
        'src/utils',
        'src/managers',
        'config',
        'data/input',
        'data/output'
    ]

    all_good = True

    for path_str in required_paths:
        path = Path(path_str)
        if path.exists():
            print(f"   ✅ {path_str}")
        else:
            print(f"   ❌ {path_str} não encontrado")
            all_good = False

    return all_good


def print_installation_commands():
    """Imprime comandos de instalação para dependências faltantes."""
    print("\n📦 Comandos de instalação:")
    print("=" * 50)

    print("\n🐍 Pacotes Python:")
    print("pip install pytesseract Pillow PyMuPDF python-docx pandas openpyxl")

    print("\n🔧 Tesseract OCR:")
    print("# Ubuntu/Debian:")
    print("sudo apt update")
    print("sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-por")
    print("")
    print("# macOS:")
    print("brew install tesseract")
    print("")
    print("# Windows:")
    print("# Baixe de: https://github.com/UB-Mannheim/tesseract/wiki")


def main():
    """Executa todas as verificações."""
    print("🔍 Verificação de Dependências do Sistema de Extração")
    print("=" * 60)

    # Executar verificações
    python_ok = check_python_packages()
    tesseract_ok = check_tesseract_executable()
    ocr_ok = test_ocr_functionality()
    structure_ok = check_project_structure()

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DAS VERIFICAÇÕES")
    print("=" * 60)

    checks = [
        ("Pacotes Python", all(python_ok.values())),
        ("Tesseract Executável", tesseract_ok),
        ("Funcionalidade OCR", ocr_ok),
        ("Estrutura do Projeto", structure_ok)
    ]

    passed = 0
    for check_name, result in checks:
        status = "✅ OK" if result else "❌ FALHA"
        print(f"{status} - {check_name}")
        if result:
            passed += 1

    print(f"\n🎯 Resultado: {passed}/{len(checks)} verificações passaram")

    if passed == len(checks):
        print("\n🎉 Sistema completamente configurado!")
        print("✅ Pode executar: python pipelinerunner.py")
    else:
        print("\n⚠️  Algumas dependências estão faltando")
        print_installation_commands()

        print(f"\n💡 Após instalar dependências:")
        print(f"   1. Execute novamente: python check_installation.py")
        print(f"   2. Quando tudo estiver ✅, execute: python pipelinerunner.py")

    return passed == len(checks)


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Verificação cancelada")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erro durante verificação: {e}")
        sys.exit(1)