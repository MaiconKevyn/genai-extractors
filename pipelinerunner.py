# pipelinerunner.py
"""
Pipeline runner simplificado - sem Factory Pattern.
Sistema plug-and-play que funciona sem configurações obrigatórias.
"""

import sys
import logging
from pathlib import Path

# Setup do projeto
project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.managers.file_manager import FileTypeManager


def get_directories():
    """
    Define diretórios de entrada e saída.
    Tenta usar configurações se disponíveis, senão usa padrões.
    """
    try:
        # Tenta importar configurações se existem
        from config.settings import INPUT_DIR, OUTPUT_DIR
        return INPUT_DIR, OUTPUT_DIR
    except ImportError:
        # Usa diretórios padrão se config não existe
        logging.info("Configurações não encontradas, usando diretórios padrão")
        project_root = Path.cwd()
        input_dir = project_root / "data" / "input"
        output_dir = project_root / "data" / "output"

        # Cria diretórios se não existem
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        return input_dir, output_dir


def main():
    """Função principal do pipeline."""

    logging.info("🚀 Iniciando Pipeline de Extração de Documentos")
    logging.info("=" * 60)

    # ✅ Obter diretórios (configurado ou padrão)
    input_dir, output_dir = get_directories()
    logging.info(f"📂 Diretório de entrada: {input_dir}")
    logging.info(f"📂 Diretório de saída: {output_dir}")

    # ✅ Criar manager simplificado (auto-registra extractors)
    manager = FileTypeManager()

    # ✅ Log das extensões suportadas (sem factory)
    supported_extensions = manager.get_supported_extensions()
    logging.info(f"🔧 Extensões suportadas: {', '.join(supported_extensions)}")

    if not supported_extensions:
        logging.error("❌ Nenhum extractor disponível! Verifique instalação das dependências.")
        return False

    logging.info("\n" + "=" * 60)

    # ✅ Verificar se diretório de entrada existe e tem arquivos
    if not input_dir.exists():
        logging.warning(f"⚠️  Diretório de entrada não existe: {input_dir}")
        logging.info(f"💡 Criando diretório: {input_dir}")
        input_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"📝 Coloque arquivos para processar em: {input_dir}")
        return True

    # ✅ Listar todos os arquivos no diretório
    all_files = [f for f in input_dir.iterdir() if f.is_file()]

    if not all_files:
        logging.warning(f"⚠️  Diretório de entrada vazio: {input_dir}")
        logging.info(f"📝 Coloque arquivos (.pdf, .docx, .csv, .xlsx) em: {input_dir}")
        return True

    # ✅ Separar arquivos suportados e não suportados
    supported_files = [f for f in all_files if manager.is_supported(f)]
    unsupported_files = [f for f in all_files if not manager.is_supported(f)]

    # ✅ Log estatísticas iniciais
    logging.info(f"📊 Estatísticas dos arquivos:")
    logging.info(f"   Total de arquivos: {len(all_files)}")
    logging.info(f"   Arquivos suportados: {len(supported_files)}")
    logging.info(f"   Arquivos não suportados: {len(unsupported_files)}")

    if unsupported_files:
        logging.info(f"🚫 Arquivos não suportados:")
        for file in unsupported_files:
            logging.info(f"      • {file.name} ({file.suffix})")

    if not supported_files:
        logging.warning("⚠️  Nenhum arquivo suportado encontrado!")
        logging.info(f"💡 Extensões aceitas: {', '.join(supported_extensions)}")
        return True

    logging.info(f"\n🔄 Iniciando processamento de {len(supported_files)} arquivos...")
    logging.info("=" * 60)

    # ✅ Processar arquivos suportados
    results = {
        'success': [],
        'failed': [],
        'total_time': 0
    }

    import time
    start_time = time.time()

    for file_path in sorted(supported_files):
        file_start_time = time.time()

        logging.info(f"📄 Processando: {file_path.name}")

        try:
            success = manager.process_file(file_path, output_dir)
            file_time = time.time() - file_start_time

            if success:
                results['success'].append(file_path.name)
                logging.info(f"   ✅ Sucesso ({file_time:.2f}s)")
                print(f"✅ {file_path.name} processado com sucesso")
            else:
                results['failed'].append(file_path.name)
                logging.error(f"   ❌ Falha ({file_time:.2f}s)")
                print(f"❌ Falha ao processar: {file_path.name}")

        except Exception as e:
            results['failed'].append(file_path.name)
            logging.error(f"   💥 Erro inesperado: {e}")
            print(f"💥 Erro inesperado em {file_path.name}: {e}")

        print("-" * 50)

    results['total_time'] = time.time() - start_time

    # ✅ Relatório final
    logging.info("\n" + "=" * 60)
    logging.info("🎉 Processamento concluído!")
    logging.info(f"📂 Resultados salvos em: {output_dir}")

    logging.info(f"\n📊 Relatório Final:")
    logging.info(f"   ✅ Sucessos: {len(results['success'])}")
    logging.info(f"   ❌ Falhas: {len(results['failed'])}")
    logging.info(f"   ⏱️  Tempo total: {results['total_time']:.2f}s")
    logging.info(f"   📈 Taxa de sucesso: {len(results['success']) / len(supported_files):.1%}")

    if results['success']:
        logging.info(f"\n✅ Arquivos processados com sucesso:")
        for filename in results['success']:
            logging.info(f"      • {filename}")

    if results['failed']:
        logging.info(f"\n❌ Arquivos com falha:")
        for filename in results['failed']:
            logging.info(f"      • {filename}")

    # ✅ Dicas para melhorar resultados
    if results['failed']:
        logging.info(f"\n💡 Dicas para resolver falhas:")
        logging.info(f"   • Verifique se arquivos não estão corrompidos")
        logging.info(f"   • Para PDFs escaneados, instale: pip install easyocr")
        logging.info(f"   • Verifique logs detalhados acima para erros específicos")

    return len(results['success']) > 0


if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1

        if success:
            print(f"\n🎉 Pipeline executado com sucesso!")
        else:
            print(f"\n⚠️  Pipeline executado com problemas. Verifique logs acima.")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        logging.info("\n\n⏹️  Pipeline interrompido pelo usuário")
        print("\n⏹️  Processamento cancelado")
        sys.exit(1)

    except Exception as e:
        logging.error(f"\n💥 Erro crítico no pipeline: {e}")
        print(f"\n💥 Erro crítico: {e}")
        sys.exit(1)