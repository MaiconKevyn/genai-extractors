# pipelinerunner.py
"""
Pipeline runner simplificado - sem Factory Pattern.
Sistema plug-and-play que funciona sem configurações obrigatórias.
Versão melhorada com verificação de OCR e instruções claras.
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


def check_ocr_dependencies():
    """
    Verifica se OCR está disponível e informa ao usuário.

    Returns:
        bool: True se OCR estiver disponível, False caso contrário
    """
    try:
        from src.utils.pytesseract_processor import validate_tesseract_dependencies

        deps = validate_tesseract_dependencies()

        ocr_available = (
                deps.get('pytesseract_available', False) and
                deps.get('tesseract_executable', False) and
                deps.get('pillow_available', False)
        )

        if ocr_available:
            logging.info("✅ OCR (Tesseract) está disponível e funcionando")
            try:
                import pytesseract
                version = pytesseract.get_tesseract_version()
                logging.info(f"📋 Tesseract versão: {version}")
            except:
                pass
        else:
            logging.warning("⚠️  OCR (Tesseract) NÃO está disponível")
            logging.warning("📄 Documentos com texto de baixa qualidade não serão melhorados com OCR")

            # Instruções específicas por dependência faltante
            if not deps.get('pytesseract_available', False):
                logging.warning("   • Instale pytesseract: pip install pytesseract")

            if not deps.get('tesseract_executable', False):
                logging.warning("   • Instale Tesseract executável:")
                logging.warning("     - Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-por")
                logging.warning("     - macOS: brew install tesseract")
                logging.warning("     - Windows: baixe de https://github.com/UB-Mannheim/tesseract/wiki")

            if not deps.get('pillow_available', False):
                logging.warning("   • Instale Pillow: pip install Pillow")

        return ocr_available

    except ImportError:
        logging.warning("⚠️  Módulo de OCR não encontrado")
        return False


def analyze_extracted_content(output_dir):
    """
    Analisa o conteúdo extraído e identifica quais documentos se beneficiariam de OCR.

    Args:
        output_dir: Diretório com arquivos JSON extraídos
    """
    try:
        from src.utils.text_quality import needs_ocr
        import json

        json_files = list(output_dir.glob("*.json"))

        if not json_files:
            return

        logging.info(f"\n📊 Análise de qualidade do texto extraído:")

        ocr_recommended = []
        good_quality = []

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                content = data.get('content', '')
                if needs_ocr(content):
                    ocr_recommended.append(json_file.stem)
                else:
                    good_quality.append(json_file.stem)

            except Exception as e:
                logging.warning(f"   Erro ao analisar {json_file.name}: {e}")

        if good_quality:
            logging.info(f"   ✅ Boa qualidade ({len(good_quality)} arquivos):")
            for filename in good_quality[:3]:  # Mostrar apenas primeiros 3
                logging.info(f"      • {filename}")
            if len(good_quality) > 3:
                logging.info(f"      • ... e mais {len(good_quality) - 3} arquivos")

        if ocr_recommended:
            logging.info(f"   📋 Recomendado OCR ({len(ocr_recommended)} arquivos):")
            for filename in ocr_recommended[:3]:  # Mostrar apenas primeiros 3
                logging.info(f"      • {filename}")
            if len(ocr_recommended) > 3:
                logging.info(f"      • ... e mais {len(ocr_recommended) - 3} arquivos")

            logging.info(f"\n💡 Para melhorar estes {len(ocr_recommended)} arquivos:")
            logging.info(f"   1. Instale Tesseract OCR (veja instruções acima)")
            logging.info(f"   2. Execute novamente: python pipelinerunner.py")
            logging.info(f"   3. Os arquivos serão automaticamente melhorados com OCR")

    except ImportError:
        logging.debug("Módulo de análise de qualidade não disponível")


def main():
    """Função principal do pipeline."""

    logging.info("🚀 Iniciando Pipeline de Extração de Documentos")
    logging.info("=" * 60)

    # ✅ Verificar OCR primeiro (informa ao usuário sobre capacidades)
    ocr_available = check_ocr_dependencies()

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

    # ✅ Aviso sobre OCR se não estiver disponível
    if not ocr_available:
        logging.info(f"\n⚠️  OCR não está disponível - documentos escaneados podem ter qualidade reduzida")

    logging.info(f"\n🔄 Iniciando processamento de {len(supported_files)} arquivos...")
    logging.info("=" * 60)

    # ✅ Processar arquivos suportados
    results = {
        'success': [],
        'failed': [],
        'total_time': 0,
        'ocr_improved': 0
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