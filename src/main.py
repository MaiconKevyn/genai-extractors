import sys
from pathlib import Path
import json

# Adicionar o diretório raiz ao sys.path para imports relativos funcionarem
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extractors.pdf_extractor import TextExtractor
from config.settings import INPUT_DIR, OUTPUT_DIR
import logging


def main():
    """Função principal para teste do extractors"""
    logging.basicConfig(level=logging.INFO)

    print(f"Diretório atual: {Path.cwd()}")
    print(f"INPUT_DIR: {INPUT_DIR}")
    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    print(f"INPUT_DIR exists: {INPUT_DIR.exists()}")

    # Inicializar extractors
    extractor = TextExtractor()
    print(f"🔧 Formato de saída configurado: {extractor.config.output_format}")

    # Seu arquivo específico
    pdf_path = INPUT_DIR / "lec21_history_neural_networks_typednotes.pdf"

    if pdf_path.exists():
        print(f"📄 Extraindo texto de: {pdf_path.name}")
        result = extractor.extract_from_file(pdf_path)

        if result.success:
            print(f"✅ Extração bem-sucedida!")
            print(f"📊 Páginas: {result.page_count}")
            print(f"📝 Formato: {result.output_format}")

            # Mostrar estatísticas do JSON simplificado
            if isinstance(result.text_content, list):
                total_chars = sum(len(page_data.get("text", "")) for page_data in result.text_content)
                pages_with_content = len([p for p in result.text_content if p.get("text", "").strip()])

                print(f"📈 Estatísticas JSON:")
                print(f"   - Total de páginas: {len(result.text_content)}")
                print(f"   - Páginas com conteúdo: {pages_with_content}")
                print(f"   - Total de caracteres: {total_chars}")
                print(f"   - Páginas vazias: {len(result.text_content) - pages_with_content}")

                # Mostrar amostra da primeira página com conteúdo
                first_page_with_content = next(
                    (page for page in result.text_content if page.get("text", "").strip()),
                    None
                )

                if first_page_with_content:
                    sample_text = first_page_with_content["text"][:200]
                    page_num = first_page_with_content["page_num"]
                    print(f"📋 Amostra da página {page_num}:")
                    print(f"   {sample_text}...")

                # Demonstrar métodos utilitários
                print(f"\n🔍 Demonstração de funcionalidades:")

                # Buscar um termo
                search_results = extractor.search_in_pages(result, "neural")
                print(f"   - Páginas com 'neural': {len(search_results)}")

                # Obter texto de página específica
                page_1_text = extractor.get_page_text(result, 1)
                print(f"   - Caracteres na página 1: {len(page_1_text)}")

                # Páginas com conteúdo
                content_pages = extractor.get_pages_with_content(result)
                print(f"   - Páginas com conteúdo: {content_pages}")

            else:
                print(f"📝 Caracteres extraídos: {len(result.text_content)}")
                print(f"📋 Primeiros 200 caracteres:")
                print(f"   {result.text_content[:200]}...")

            # Salvar resultado
            output_file = OUTPUT_DIR / f"{pdf_path.stem}_extracted.json"
            success = extractor.save_extracted_text(result, output_file)

            if success:
                print(f"💾 Arquivo salvo em: {output_file}")

                # Mostrar estrutura do arquivo JSON salvo
                print(f"🔍 Estrutura do JSON salvo:")
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        saved_data = json.load(f)

                    if isinstance(saved_data, list):
                        print(f"   - Formato: Array de páginas")
                        print(f"   - Total de páginas: {len(saved_data)}")

                        if saved_data:
                            first_page = saved_data[0]
                            print(f"   - Estrutura da página: {list(first_page.keys())}")
                            print(f"   - Primeira página número: {first_page.get('page_num', '?')}")
                            print(f"   - Caracteres na primeira página: {len(first_page.get('text', ''))}")

                        # Mostrar páginas com mais conteúdo
                        pages_by_size = sorted(
                            saved_data,
                            key=lambda x: len(x.get('text', '')),
                            reverse=True
                        )[:3]

                        print(f"   - Top 3 páginas por conteúdo:")
                        for i, page in enumerate(pages_by_size, 1):
                            chars = len(page.get('text', ''))
                            page_num = page.get('page_num', '?')
                            print(f"     {i}. Página {page_num}: {chars} caracteres")

                except Exception as e:
                    print(f"   ❌ Erro ao ler arquivo salvo: {e}")

        else:
            print(f"❌ Erro na extração: {result.error_message}")
    else:
        print(f"❌ Arquivo não encontrado: {pdf_path}")
        print("📁 Arquivos disponíveis no diretório input:")
        for file in INPUT_DIR.glob("*.pdf"):
            print(f"   - {file.name}")

    # Processar todos os PDFs do diretório
    print(f"\n🔍 Processando todos os PDFs de: {INPUT_DIR}")
    try:
        results = extractor.extract_from_directory(INPUT_DIR)

        print(f"📊 Resumo do processamento:")
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        print(f"   ✅ Sucessos: {successful}")
        print(f"   ❌ Falhas: {failed}")

        for result in results:
            status = "✅" if result.success else "❌"
            name = Path(result.file_path).name
            format_info = f"({result.output_format})" if hasattr(result, 'output_format') else ""
            print(f"   {status} {name} {format_info}")

        # Mostrar estatísticas detalhadas
        if results:
            summary = extractor.get_extraction_summary(results)
            print(f"\n📈 Estatísticas detalhadas:")
            print(f"   - Total de páginas: {summary['total_pages']}")
            print(f"   - Total de caracteres: {summary['total_characters']}")
            print(f"   - Média de páginas por arquivo: {summary['average_pages']:.1f}")
            print(f"   - Formato de saída: {summary['output_format']}")

    except Exception as e:
        print(f"❌ Erro ao processar diretório: {str(e)}")


def demo_json_structure():
    """Demonstra a estrutura do JSON simplificado gerado"""
    print("\n" + "=" * 50)
    print("📋 ESTRUTURA DO JSON SIMPLIFICADO:")
    print("=" * 50)

    example_structure = [
        {
            "page_num": 1,
            "text": "CS 486/686 Lecture 21 A brief history of deep learning\n\nThis summary is based on A 'Brief' History of Neural Nets and Deep Learning by Andrew Kurenkov..."
        },
        {
            "page_num": 2,
            "text": "The output is 1 if the weighted sum is big enough and the output is 0 otherwise.\n\nActivation function: a non-linear function..."
        },
        {
            "page_num": 3,
            "text": "A simple algorithm to learn a perceptron:\n1. Start with random weights in a perceptron..."
        }
    ]

    print(json.dumps(example_structure, indent=2, ensure_ascii=False))
    print("=" * 50)


def demo_usage_examples():
    """Demonstra como usar o JSON extraído"""
    print("\n" + "=" * 50)
    print("💡 EXEMPLOS DE USO DO JSON EXTRAÍDO:")
    print("=" * 50)

    example_code = '''
# Carregar JSON extraído
import json
with open('output.json', 'r', encoding='utf-8') as f:
    pages = json.load(f)

# 1. Acessar página específica
page_1 = pages[0]  # Primeira página (índice 0)
page_1_text = page_1["text"]
page_1_num = page_1["page_num"]

# 2. Buscar em todas as páginas
def search_term(pages, term):
    results = []
    for page in pages:
        if term.lower() in page["text"].lower():
            results.append({
                "page_num": page["page_num"], 
                "snippet": page["text"][:100] + "..."
            })
    return results

neural_pages = search_term(pages, "neural")

# 3. Estatísticas
total_chars = sum(len(page["text"]) for page in pages)
avg_chars_per_page = total_chars / len(pages)

# 4. Filtrar páginas por tamanho
large_pages = [p for p in pages if len(p["text"]) > 1000]

# 5. Converter para texto único
full_text = "\\n\\n".join(page["text"] for page in pages)

# 6. Processar com LLMs (exemplo conceitual)
for page in pages:
    if len(page["text"]) > 500:  # Só páginas com conteúdo substancial
        # Enviar page["text"] para LLM para análise
        pass
'''

    print(example_code)
    print("=" * 50)


if __name__ == "__main__":
    main()

    # Mostrar estrutura de exemplo e usos
    demo_json_structure()
    demo_usage_examples()