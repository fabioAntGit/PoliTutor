import os
import re
import json
import glob
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import convert_to_dict

AULA_PATTERN = re.compile(r"Aula\s+\d+", re.IGNORECASE)

# Lista de keywords para descartar
KEYWORDS_TO_EXCLUDE = [
    "Ricardo Santos", 
    "rjs@estg.ipp.pt", 
    "P. PORTO", 
    "— P2PORTO",
    "ESCOLA",
    "SUPERIOR",
    "DE TECNOLOGIA",
    "PARADIGMAS DE PROGRAMAÇÃO 2023/2024",
    "E GESTÃO",
]

def process_all_pdfs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.normpath(os.path.join(base_dir, "..", "data", "raw"))
    output_dir = os.path.join(raw_path, "processed_json")
    
    os.makedirs(output_dir, exist_ok=True)
    pdf_files = glob.glob(os.path.join(raw_path, "*.pdf"))
    
    if not pdf_files:
        print(f"Nenhum PDF encontrado em: {raw_path}")
        return

    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        print(f"A processar e filtrar: {file_name}...")

        try:
            elements = partition_pdf(
                filename=pdf_path,
                strategy="hi_res",
                languages=["por", "eng"],
                infer_table_structure=True,
                extract_images_in_pdf=True,
                extract_image_block_types=["Image", "Table"],
                extract_image_block_to_payload=True,
                chunking_strategy=None,
                include_orig_elements=False,
            )

            dict_elements = convert_to_dict(elements)
            
            # --- LÓGICA DE FILTRAGEM ---
            filtered_elements = []
            for el in dict_elements:
                # Filtrar por tipo (Remover Footers)
                if el.get("type") == "Footer":
                    continue
                
                text_content = el.get("text", "")

                # Filtro de Keywords (Exatas/Parciais)
                if any(key.lower() in text_content.lower() for key in KEYWORDS_TO_EXCLUDE):
                    continue

                if AULA_PATTERN.fullmatch(text_content) or AULA_PATTERN.search(text_content):
                    continue
                
                # Se passar os filtros, adicionamos à lista final
                filtered_elements.append(el)
            
            # Guardar ficheiro limpo
            output_filename = f"{os.path.splitext(file_name)[0]}.json"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(filtered_elements, f, indent=4, ensure_ascii=False)
            
            print(f"Sucesso: {output_filename} guardado (Filtrados {len(dict_elements) - len(filtered_elements)} elementos).")

        except Exception as e:
            print(f"Erro ao processar {file_name}: {str(e)}")

if __name__ == "__main__":
    process_all_pdfs()