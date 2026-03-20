from backend.services.parser import parse_pdf
import sys

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Usage: python run_parser.py <pdf_path> <section>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    section = sys.argv[2]

    result = parse_pdf(pdf_path, section)

    print("Parsing complete.")