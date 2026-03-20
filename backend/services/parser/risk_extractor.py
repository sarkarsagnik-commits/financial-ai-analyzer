import re
from .section_detector import extract_section_text
from .text_cleaner import clean_text


def extract_risk_factors(pdf_path: str):

    raw_text = extract_section_text(pdf_path, "risk_factors")
    cleaned = clean_text(raw_text)

    risks = re.split(r"\n\s*[•\-]\s*", cleaned)

    risks = [r.strip() for r in risks if len(r.strip()) > 50]

    return {
        "section": "risk_factors",
        "character_count": len(cleaned),
        "risk_count": len(risks),
        "risks": risks,
        "full_text": cleaned
    }