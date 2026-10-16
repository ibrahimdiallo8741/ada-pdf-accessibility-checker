
import pymupdf

def check_pdf(file_path):
    document = pymupdf.open(file_path)

    print("PDF opened successfully!")
    print("Number of pages:", len(document))

    for page_number, page in enumerate(document, start=1):
        text = page.get_text().strip()

        if text:
            print(f"Page {page_number}: Extractable text found.")
        else:
            print(f"Page {page_number}: No extractable text found. Needs further review.")

    document.close()


pdf_path = input("Enter the path to your PDF file: ").strip().strip('"')
check_pdf(pdf_path)
