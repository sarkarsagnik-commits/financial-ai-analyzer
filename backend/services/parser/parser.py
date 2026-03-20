from .financial_extractor import extract_financial_data
from .mdna_extractor import extract_mdna
from .risk_extractor import extract_risk_factors
from .utils import get_processed_dir

import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)


ALLOWED_SECTIONS = {
    "financials": extract_financial_data,
    "mdna": extract_mdna,
    "risk_factors": extract_risk_factors
}


def save_json(data: dict, pdf_path: str, section: str):

    output_dir = get_processed_dir()

    filename = os.path.basename(pdf_path).replace(".pdf", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = output_dir / f"{filename}_{section}_{timestamp}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    logging.info(f"JSON saved to {output_path}")


def parse_pdf(pdf_path: str, section: str) -> dict:

    section = section.lower().strip()

    if section not in ALLOWED_SECTIONS:
        raise ValueError(
            f"Invalid section '{section}'. "
            f"Allowed: {', '.join(ALLOWED_SECTIONS.keys())}"
        )

    logging.info(f"Running parser for section: {section}")

    extractor_function = ALLOWED_SECTIONS[section]
    result = extractor_function(pdf_path)

    save_json(result, pdf_path, section)

    return result