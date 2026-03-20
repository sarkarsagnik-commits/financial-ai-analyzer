import fitz
import re


SECTION_BOUNDARIES = {
    "risk_factors": {
        "start": r"\nitem\s*1a\b",
        "end": r"\nitem\s*1b\b|\nitem\s*2\b"
    },
    "mdna": {
        "start": r"\nitem\s*(7|2)\b",
        "end": r"\nitem\s*7a\b|\nitem\s*8\b"
    },
    "financials": {
        "start": r"\nitem\s*8\b",
        "end": r"\nitem\s*9\b"
    }
}


def extract_section_text(pdf_path: str, section: str) -> str:

    section = section.lower()

    if section not in SECTION_BOUNDARIES:
        raise ValueError("Invalid section type")

    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:

        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))

        for block in blocks:
            full_text += block[4] + "\n"

    full_text_lower = full_text.lower()

    toc_index = full_text_lower.find("table of contents")

    if toc_index != -1:
        first_real_item = re.search(r"\nitem\s*1\b", full_text_lower[toc_index:])

        if first_real_item:
            cut_index = toc_index + first_real_item.start()
            full_text_lower = full_text_lower[:toc_index] + full_text_lower[cut_index:]
            full_text = full_text[:toc_index] + full_text[cut_index:]

    start_pattern = re.compile(SECTION_BOUNDARIES[section]["start"], re.IGNORECASE)
    end_pattern = re.compile(SECTION_BOUNDARIES[section]["end"], re.IGNORECASE)

    start_matches = list(start_pattern.finditer(full_text_lower))

    if not start_matches:
        return "Section not found"

    start_index = start_matches[-1].start()

    end_match = end_pattern.search(full_text_lower[start_index + 1:])

    if end_match:
        end_index = start_index + 1 + end_match.start()
        section_text = full_text[start_index:end_index]
    else:
        section_text = full_text[start_index:]

    return section_text.strip()