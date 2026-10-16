
import pymupdf
from pypdf import PdfReader

def check_pdf(file_path):
    document = pymupdf.open(file_path)

    print("PDF opened successfully!")
    print("Number of pages:", len(document))

    
    # Check whether the PDF has a document title
    metadata = document.metadata
    title = metadata.get("title", "") if metadata else ""

    if title and title.strip():
        print("Document title found:", title)
    else:
        print("Warning: No document title found. Needs accessibility review.")

    
    # Check the PDF's declared document language
    language = document.language

    if language:
        print("Document language found:", language)
    else:
        print("Warning: No document language specified. Needs accessibility review.")




    
    # Check whether the PDF contains a structure tree
    reader = PdfReader(file_path)
    root = reader.trailer["/Root"]

    if "/StructTreeRoot" in root:
        print("PDF structure tree found. Document contains tagging information.")
    else:
        print("Warning: No PDF structure tree found. Needs accessibility review.")



    for page_number, page in enumerate(document, start=1):
        text = page.get_text().strip()

        if text:
            print(f"Page {page_number}: Extractable text found.")
        else:
            print(f"Page {page_number}: No extractable text found. Needs further review.")

    document.close()


pdf_path = input("Enter the path to your PDF file: ").strip().strip('"')
check_pdf(pdf_path)
