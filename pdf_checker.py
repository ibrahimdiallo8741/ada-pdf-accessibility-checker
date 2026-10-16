
import pymupdf
from pypdf import PdfReader
from pathlib import Path
import json


def check_pdf(file_path):
    results = {
        "file": Path(file_path).name,
        "pages": 0,
        "checks": [],
        "warnings": []
    }

    def add_check(name, status, details):
        results["checks"].append({
            "check": name,
            "status": status,
            "details": details
        })

        print(f"{name}: {details}")

        if status == "REVIEW":
            results["warnings"].append(details)

    try:
        document = pymupdf.open(file_path)
        reader = PdfReader(file_path)

        print("\nPDF ACCESSIBILITY CHECKER")
        print("-------------------------")
        print("PDF opened successfully!")

        results["pages"] = len(document)
        print("Number of pages:", len(document))

        # Check document title
        metadata = document.metadata or {}
        title = metadata.get("title", "")

        if title and title.strip():
            add_check("Document title", "FOUND",
                      f"Title found: {title}")
        else:
            add_check("Document title", "REVIEW",
                      "No document title found.")

        # Check document language
        language = document.language

        if language:
            add_check("Document language", "FOUND",
                      f"Language found: {language}")
        else:
            add_check("Document language", "REVIEW",
                      "No document language specified.")

        # Check PDF structure tree
        root = reader.trailer["/Root"]

        if "/StructTreeRoot" in root:
            add_check("PDF structure", "FOUND",
                      "Structure tree found. Tag quality needs review.")
        else:
            add_check("PDF structure", "REVIEW",
                      "No PDF structure tree found.")

        # Check each page
        for page_number, page in enumerate(document, start=1):
            print(f"\nChecking page {page_number}...")

            # Check extractable text
            text = page.get_text().strip()

            if text:
                add_check(
                    f"Page {page_number} text",
                    "FOUND",
                    "Extractable text found."
                )
            else:
                add_check(
                    f"Page {page_number} text",
                    "REVIEW",
                    "No extractable text found. Manual review needed."
                )

            # Detect embedded images
            images = page.get_images(full=True)

            if images:
                add_check(
                    f"Page {page_number} images",
                    "REVIEW",
                    f"{len(images)} image resource(s) found. "
                    "Check whether meaningful images have alt text."
                )
            else:
                add_check(
                    f"Page {page_number} images",
                    "INFO",
                    "No embedded image resources detected."
                )

        document.close()

        # Generate JSON report
        report_path = Path(file_path).with_name(
            Path(file_path).stem + "_accessibility_report.json"
        )

        with open(report_path, "w", encoding="utf-8") as report:
            json.dump(results, report, indent=4)

        # Display summary
        print("\n-------------------------")
        print("ACCESSIBILITY REVIEW SUMMARY")
        print("-------------------------")
        print("Total pages:", results["pages"])
        print("Checks performed:", len(results["checks"]))
        print("Items needing review:", len(results["warnings"]))
        print("Report saved to:", report_path)

        print("\nNote: This is an automated screening tool.")
        print("It does not certify ADA or WCAG compliance.")

    except (FileNotFoundError, OSError) as error:
        print("Error opening PDF:", error)
    except Exception as error:
        print("An error occurred:", error)


if __name__ == "__main__":
    pdf_path = input(
        "Enter the path to your PDF file: "
    ).strip().strip('"')

    check_pdf(pdf_path)
