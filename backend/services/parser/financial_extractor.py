import fitz
import camelot


FINANCIAL_ANCHORS = [
    "consolidated statements of operations",
    "consolidated statements of income",
    "consolidated statements of comprehensive income",
    "consolidated balance sheets",
    "consolidated statements of cash flows"
]


def find_financial_page_block(pdf_path: str):

    doc = fitz.open(pdf_path)

    anchor_page = None

    for i, page in enumerate(doc):
        text = page.get_text("text").lower()

        for anchor in FINANCIAL_ANCHORS:
            if anchor in text:
                anchor_page = i + 1
                break

        if anchor_page:
            break

    if anchor_page is None:
        return []

    start_page = anchor_page
    end_page = min(anchor_page + 25, len(doc))

    return list(range(start_page, end_page + 1))


def is_real_financial_table(table_data):

    flat = " ".join(cell.lower() for row in table_data for cell in row)

    required_terms = [
        "revenue",
        "net income",
        "total assets",
        "total liabilities",
        "cash flows"
    ]

    return any(term in flat for term in required_terms)


def extract_financial_data(pdf_path: str) -> dict:

    pages = find_financial_page_block(pdf_path)

    if not pages:
        return {
            "section": "financials",
            "error": "Financial statements not detected",
            "tables": []
        }

    page_string = ",".join(map(str, pages))

    tables = camelot.read_pdf(
        pdf_path,
        pages=page_string,
        flavor="stream"
    )

    cleaned_tables = []

    for table in tables:

        df = table.df.fillna("").astype(str)

        table_data = [
            [cell.strip() for cell in row]
            for row in df.values.tolist()
        ]

        if is_real_financial_table(table_data):
            cleaned_tables.append(table_data)

    return {
        "section": "financials",
        "page_range": pages,
        "table_count": len(cleaned_tables),
        "tables": cleaned_tables
    }