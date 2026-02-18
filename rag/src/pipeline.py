import os
import glob
import logging
from config import (
    COURSE_PATH,
    OUTPUT_DIR,
    OUTPUT_DIR_BEFORE,
    KEYWORDS_TO_EXCLUDE,
)
from utils import extract_source_type
from pdf_extractor import (
    extract_elements_from_pdf,
    filter_elements,
    group_elements_by_page,
    save_json,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def process_all_pdfs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR_BEFORE, exist_ok=True)

    pdf_files = glob.glob(os.path.join(COURSE_PATH, "**", "*.pdf"), recursive=True)
    if not pdf_files:
        logging.warning(f"Nenhum PDF encontrado em: {COURSE_PATH}")
        return

    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        source_type = extract_source_type(pdf_path)
        logging.info(f"A processar e filtrar: {file_name}...")

        try:
            elements = extract_elements_from_pdf(pdf_path)
            filtered_elements = filter_elements(elements, KEYWORDS_TO_EXCLUDE)

            # Guardar JSON antes da filtragem
            before_path = os.path.join(OUTPUT_DIR_BEFORE, f"{os.path.splitext(file_name)[0]}Before.json")
            save_json(filtered_elements, before_path)

            # Agrupar por página
            grouped_pages = group_elements_by_page(filtered_elements, source_filename=file_name, source_type=source_type)
            output_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file_name)[0]}.json")
            save_json(grouped_pages, output_path)

            logging.info(f"Sucesso: {output_path} guardado (Filtrados {len(elements) - len(filtered_elements)} elementos).")

        except Exception as e:
            logging.error(f"Erro ao processar {file_name}: {str(e)}")

if __name__ == "__main__":
    process_all_pdfs()