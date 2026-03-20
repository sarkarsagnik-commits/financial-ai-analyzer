import re
from .section_detector import extract_section_text
from .text_cleaner import clean_text


MDNA_SUBSECTIONS = {
    "overview": r"overview",
    "results_of_operations": r"results of operations",
    "liquidity_and_capital_resources": r"liquidity and capital",
    "critical_accounting_policies": r"critical accounting"
}


def split_mdna_sections(text: str):

    sections = {}
    text_lower = text.lower()

    for key, pattern in MDNA_SUBSECTIONS.items():

        match = re.search(pattern, text_lower)

        if match:
            sections[key] = text[match.start():]

    return sections


def extract_mdna(pdf_path: str):

    raw_text = extract_section_text(pdf_path, "mdna")
    cleaned = clean_text(raw_text)

    structured_sections = split_mdna_sections(cleaned)

    return {
        "section": "mdna",
        "character_count": len(cleaned),
        "subsections": structured_sections,
        "full_text": cleaned
    }