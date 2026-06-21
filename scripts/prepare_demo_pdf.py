import os

import fitz


def main():
    pdf_path = "data/arxiv_sample.pdf"
    output_path = "data/arxiv_pii_sample.pdf"

    if not os.path.exists(pdf_path):
        print(f"Error: Source PDF '{pdf_path}' not found. Please download it first.")
        return

    doc = fitz.open(pdf_path)
    page = doc[0]  # Get first page

    # Write synthetic PII line-by-line to avoid horizontal page clipping
    pii_lines = [
        "Document Owner: Alice Smith",
        "Email: alice.smith@example.com",
        "Phone: +1-555-0199",
        "Server IP: 10.0.0.1",
        "SSN: 123-45-6789",  # matched by SSN / SSN_US (US)
    ]

    for idx, line in enumerate(pii_lines):
        page.insert_text((50, 40 + idx * 15), line, fontsize=9, color=(1, 0, 0))

    doc.save(output_path)
    doc.close()
    print(f"Generated PDF with PII at: {output_path}")


if __name__ == "__main__":
    main()
