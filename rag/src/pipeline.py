import os
import re
import json
import glob
from collections import defaultdict
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
    output_dirBefore = os.path.join(raw_path, "processedBefore_json")
    output_image_dir = os.path.join(raw_path, "processed_images")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_dirBefore, exist_ok=True)
    os.makedirs(output_image_dir, exist_ok=True)
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
                extract_image_block_types=["Image", "Table"],
                extract_images_in_pdf=True,
                extract_image_block_to_payload=False,
                image_output_dir_path=output_image_dir,
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
            
            output_filenameBefore = f"{os.path.splitext(file_name)[0]}Before.json"
            output_pathBefore = os.path.join(output_dirBefore, output_filenameBefore)

            with open(output_pathBefore, "w", encoding="utf-8") as f:
                json.dump(filtered_elements, f, indent=4, ensure_ascii=False)

            grouped_pages = group_elements_by_page(filtered_elements, source_filename=file_name)
            
            # Guardar ficheiro limpo
            output_filename = f"{os.path.splitext(file_name)[0]}.json"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(grouped_pages, f, indent=4, ensure_ascii=False)
            
            print(f"Sucesso: {output_filename} guardado (Filtrados {len(dict_elements) - len(filtered_elements)} elementos).")

        except Exception as e:
            print(f"Erro ao processar {file_name}: {str(e)}")

def extract_course_from_filename(filename: str) -> str:
    stem = os.path.splitext(filename)[0]  # "2024.ED.Aula01"
    parts = stem.split(".")
    return parts[1] if len(parts) > 1 else ""

def get_top_left(el):
    md = el.get("metadata", {})
    coords = md.get("coordinates", {})
    points = coords.get("points")
    if not points:
        return (10**18, 10**18)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(ys), min(xs))

def build_page_text(page_elements):
    lines = []
    for el in page_elements:
        el_type = el.get("type")
        if el_type in ("Image", "Table"):
            continue

        txt = (el.get("text") or "").strip()
        if not txt:
            continue

        txt = txt.replace("•", "• ").replace("  ", " ").strip()
        lines.append(txt)

    page_text = "\n".join(lines)
    while "\n\n\n" in page_text:
        page_text = page_text.replace("\n\n\n", "\n\n")
    return page_text.strip()

def extract_tables_html(page_elements):
    tables = []
    for el in page_elements:
        if el.get("type") != "Table":
            continue

        md = el.get("metadata", {}) or {}
        html = md.get("text_as_html") or md.get("html")

        if not html:
            txt = (el.get("text") or "").strip()
            if txt:
                html = f"<pre>{txt}</pre>"

        if html:
            tables.append(html)

    return tables

def group_elements_by_page(elements, source_filename=None):
    pages = defaultdict(list)
    for el in elements:
        page = el.get("metadata", {}).get("page_number", -1)
        pages[page].append(el)

    cadeira = extract_course_from_filename(source_filename or "")

    grouped = []
    for page in sorted(pages.keys()):
        page_elements = sorted(pages[page], key=get_top_left)

        # base metadata (para filetype)
        base_md = (page_elements[0].get("metadata") or {}) if page_elements else {}

        page_text = build_page_text(page_elements)
        tables = extract_tables_html(page_elements)

        # se não houver texto nem tabelas, ignora
        if not page_text and not tables:
            continue

        grouped.append({
            "metadata": {
                "filename": source_filename,
                "course": cadeira,
                "page_number": page,
                "filetype": base_md.get("filetype"),
            },
            "text": page_text,
            "tables": tables,
        })

    return grouped

if __name__ == "__main__":
    process_all_pdfs()