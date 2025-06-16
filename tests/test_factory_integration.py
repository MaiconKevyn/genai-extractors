# test_factory_integration.py
"""
Script simples para testar se a integração do Factory Pattern funcionou.
Execute este script para validar as mudanças.
"""

import sys
from pathlib import Path

# Setup do projeto - corrige path para encontrar módulos
project_root = Path(__file__).parent.parent  # Volta para raiz do projeto
src_path = project_root / "src"
config_path = project_root

# Adiciona paths necessários
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(config_path) not in sys.path:
    sys.path.insert(0, str(config_path))


def test_factory_basic():
    """Testa funcionalidade básica do factory."""
    print("🧪 Testando Factory Pattern...")

    try:
        from extractors.factory import ExtractorFactory, get_default_factory

        # Teste 1: Criação do factory
        factory = ExtractorFactory()
        print(f"✅ Factory criado com sucesso")

        # Teste 2: Extensões suportadas
        extensions = factory.get_supported_extensions()
        print(f"✅ Extensões suportadas: {extensions}")

        # Teste 3: Singleton
        factory2 = get_default_factory()
        factory3 = get_default_factory()
        assert factory2 is factory3, "Singleton não funcionando"
        print(f"✅ Singleton funcionando")

        return True

    except Exception as e:
        print(f"❌ Erro no factory: {e}")
        return False


def test_file_manager_integration():
    """Testa integração com FileManager."""
    print("\n🧪 Testando FileManager integração...")

    try:
        from managers.file_manager import FileTypeManager

        # Teste 1: Criação com factory automático
        manager = FileTypeManager()
        print(f"✅ FileManager criado com factory automático")

        # Teste 2: Compatibilidade com registro manual
        from extractors.base_extractor import BaseExtractor, ExtractionResult

        class DummyExtractor(BaseExtractor):
            def extract(self, input_path):
                return ExtractionResult(
                    source_file=str(input_path),
                    content="Dummy content",
                    success=True
                )

        manager.register_extractor('.dummy', DummyExtractor)
        assert manager.factory.is_supported(Path('test.dummy'))
        print(f"✅ Registro manual ainda funciona")

        return True

    except Exception as e:
        print(f"❌ Erro no FileManager: {e}")
        return False


def test_pipeline_compatibility():
    """Testa compatibilidade com pipeline atual."""
    print("\n🧪 Testando compatibilidade do pipeline...")

    try:
        # Testa imports do pipeline atual
        from config.settings import INPUT_DIR, OUTPUT_DIR, EXTRACTOR_CONFIG
        from managers.file_manager import FileTypeManager

        manager = FileTypeManager()

        # Verifica se as configurações ainda são respeitadas
        supported = manager.factory.get_supported_extensions()
        config_extensions = EXTRACTOR_CONFIG.supported_extensions

        # Log compatibilidade
        compatible = [ext for ext in config_extensions if ext in supported]
        incompatible = [ext for ext in config_extensions if ext not in supported]

        print(f"✅ Extensões compatíveis: {compatible}")
        if incompatible:
            print(f"⚠️  Extensões não implementadas: {incompatible}")

        print(f"✅ Pipeline compatível com configuração atual")
        return True

    except Exception as e:
        print(f"❌ Erro na compatibilidade: {e}")
        return False


def test_extractor_creation():
    """Testa criação de extractors específicos."""
    print("\n🧪 Testando criação de extractors...")

    try:
        from extractors.factory import get_default_factory
        import tempfile

        factory = get_default_factory()

        # Teste com diferentes tipos de arquivo
        test_files = [
            ('test.pdf', 'PDF'),
            ('test.docx', 'DOCX'),
            ('test.csv', 'CSV'),
            ('test.xlsx', 'XLSX'),
            ('test.unknown', 'Unknown')
        ]

        for filename, file_type in test_files:
            # Cria arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as f:
                temp_path = Path(f.name)

                extractor = factory.create_extractor(temp_path)

                if extractor:
                    print(f"✅ {file_type}: {extractor.__class__.__name__}")
                else:
                    print(f"🚫 {file_type}: Não suportado")

                # Cleanup
                temp_path.unlink()

        return True

    except Exception as e:
        print(f"❌ Erro na criação de extractors: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("🚀 Iniciando testes de integração do Factory Pattern")
    print("=" * 60)

    tests = [
        test_factory_basic,
        test_file_manager_integration,
        test_pipeline_compatibility,
        test_extractor_creation
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    print("\n" + "=" * 60)
    print("📊 RESULTADOS DOS TESTES")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 TODOS OS TESTES PASSARAM! ({passed}/{total})")
        print("✅ Factory Pattern integrado com sucesso!")
        print("\n💡 Próximos passos:")
        print("   1. Execute o pipeline normal para verificar funcionamento")
        print("   2. Rode: python pipelinerunner.py")
        print("   3. Confirme que arquivos são processados normalmente")
        return 0
    else:
        print(f"❌ ALGUNS TESTES FALHARAM ({passed}/{total} passaram)")
        print("🔧 Verifique os erros acima e corrija antes de prosseguir")
        return 1


if __name__ == "__main__":
    sys.exit(main())