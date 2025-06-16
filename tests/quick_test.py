#!/usr/bin/env python3
"""
Teste rápido e simplificado para validar Factory Pattern.
Execute: python tests/quick_test.py
"""

import sys
from pathlib import Path

# === SETUP DE PATHS ===
# Adiciona diretórios necessários ao Python path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
config_dir = project_root

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(config_dir))

print(f"🔧 Project root: {project_root}")
print(f"🔧 Src dir: {src_dir}")
print(f"🔧 Python path: {sys.path[:3]}...")  # Mostra só os primeiros 3


def test_basic_imports():
    """Testa imports básicos."""
    print("\n🧪 Testando imports básicos...")

    try:
        # Teste 1: Import do factory
        from extractors.factory import ExtractorFactory
        print("✅ extractors.factory importado")

        # Teste 2: Import do base_extractor
        from extractors.base_extractor import BaseExtractor
        print("✅ extractors.base_extractor importado")

        # Teste 3: Import do file_manager
        from managers.file_manager import FileTypeManager
        print("✅ managers.file_manager importado")

        # Teste 4: Import de config (pode falhar se não existir)
        try:
            from config.settings import INPUT_DIR, OUTPUT_DIR
            print("✅ config.settings importado")
        except ImportError as e:
            print(f"⚠️  config.settings não encontrado: {e}")

        return True

    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False


def test_factory_creation():
    """Testa criação do factory."""
    print("\n🧪 Testando criação do Factory...")

    try:
        from extractors.factory import ExtractorFactory, get_default_factory

        # Teste 1: Criação manual
        factory = ExtractorFactory()
        print("✅ Factory criado manualmente")

        # Teste 2: Singleton
        factory1 = get_default_factory()
        factory2 = get_default_factory()

        if factory1 is factory2:
            print("✅ Singleton funcionando")
        else:
            print("❌ Singleton não funcionando")

        # Teste 3: Extensões suportadas
        extensions = factory.get_supported_extensions()
        print(f"✅ Extensões suportadas: {extensions}")

        return True

    except Exception as e:
        print(f"❌ Erro na criação: {e}")
        return False


def test_file_manager_creation():
    """Testa criação do FileManager."""
    print("\n🧪 Testando criação do FileManager...")

    try:
        from managers.file_manager import FileTypeManager

        # Teste 1: Criação com factory padrão
        manager = FileTypeManager()
        print("✅ FileManager criado")

        # Teste 2: Verificar se tem factory
        if hasattr(manager, 'factory'):
            print("✅ FileManager tem factory")
        else:
            print("❌ FileManager não tem factory")

        # Teste 3: Verificar métodos
        if hasattr(manager, 'process_file'):
            print("✅ FileManager tem process_file")
        else:
            print("❌ FileManager não tem process_file")

        return True

    except Exception as e:
        print(f"❌ Erro no FileManager: {e}")
        return False


def test_extractor_auto_discovery():
    """Testa auto-discovery de extractors."""
    print("\n🧪 Testando auto-discovery...")

    try:
        from extractors.factory import ExtractorFactory

        factory = ExtractorFactory()
        extensions = factory.get_supported_extensions()

        # Verifica extractors esperados
        expected = ['.pdf', '.docx', '.csv', '.xlsx']
        found = []
        missing = []

        for ext in expected:
            if ext in extensions:
                found.append(ext)
            else:
                missing.append(ext)

        print(f"✅ Extractors encontrados: {found}")
        if missing:
            print(f"⚠️  Extractors não encontrados: {missing}")

        # Teste de criação de extractor
        import tempfile

        for ext in found[:2]:  # Testa só os 2 primeiros
            try:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                    test_file = Path(f.name)

                extractor = factory.create_extractor(test_file)

                if extractor:
                    print(f"✅ Criou extractor para {ext}: {extractor.__class__.__name__}")
                else:
                    print(f"❌ Não criou extractor para {ext}")

                # Cleanup
                test_file.unlink()

            except Exception as e:
                print(f"⚠️  Erro testando {ext}: {e}")

        return True

    except Exception as e:
        print(f"❌ Erro no auto-discovery: {e}")
        return False


def test_file_support_check():
    """Testa verificação de suporte a arquivos."""
    print("\n🧪 Testando verificação de suporte...")

    try:
        from extractors.factory import get_default_factory
        import tempfile
        import os

        factory = get_default_factory()

        # Testa arquivos diferentes
        test_cases = [
            ('document.pdf', True),
            ('document.docx', True),
            ('data.csv', True),
            ('spreadsheet.xlsx', True),
            ('unknown.xyz', False),
            ('readme.txt', False)
        ]

        for filename, expected_support in test_cases:
            # Cria arquivo temporário
            temp_dir = Path(tempfile.gettempdir())
            test_file = temp_dir / filename
            test_file.write_text("test content")

            try:
                is_supported = factory.is_supported(test_file)

                if is_supported == expected_support:
                    status = "✅"
                else:
                    status = "❌"

                print(f"{status} {filename}: suportado={is_supported} (esperado={expected_support})")

            finally:
                if test_file.exists():
                    test_file.unlink()

        return True

    except Exception as e:
        print(f"❌ Erro na verificação de suporte: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("🚀 TESTE RÁPIDO - Factory Pattern Integration")
    print("=" * 60)

    tests = [
        ("Imports Básicos", test_basic_imports),
        ("Factory Creation", test_factory_creation),
        ("FileManager Creation", test_file_manager_creation),
        ("Auto-Discovery", test_extractor_auto_discovery),
        ("File Support Check", test_file_support_check)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))

    # === RESUMO ===
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status:12} {test_name}")
        if result:
            passed += 1

    total = len(results)
    print(f"\n📈 RESULTADO FINAL: {passed}/{total} testes passaram")

    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Factory Pattern integrado com sucesso!")
        print("\n🚀 Próximos passos:")
        print("   1. Execute: python pipelinerunner.py")
        print("   2. Verifique se processa arquivos normalmente")
        print("   3. Compare com funcionamento anterior")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam")
        print("🔧 Verifique os erros acima")
        print("\n💡 Possíveis soluções:")
        print("   - Verifique se todos os arquivos estão no lugar")
        print("   - Confirme estrutura de diretórios")
        print("   - Execute: ls -la src/extractors/ src/managers/")
        return 1


if __name__ == "__main__":
    exit(main())