import json
from pathlib import Path

from core.checker import screen_pdf
from core.models import Finding, ScanResult

# Backward-compatibility aliases
CheckResult = Finding
AccessibilityReport = ScanResult


def check_pdf(file_path: str) -> ScanResult | None:
    try:
        scan_result = screen_pdf(file_path)

        print("\nPDF ACCESSIBILITY CHECKER")
        print("-------------------------")
        print("PDF opened successfully!")
        print("Number of pages:", scan_result.pages)
        print()

        for finding in scan_result.findings:
            print(f"{finding.input_location} ({finding.WCAG_criterion}): [{finding.status}] {finding.issue_description}")
            if finding.remediation_guidance:
                print(f"  Remediation: {finding.remediation_guidance}")

        # Generate JSON report matching api/api.md schema
        report_path = Path(file_path).with_name(
            Path(file_path).stem + "_accessibility_report.json"
        )

        with open(report_path, "w", encoding="utf-8") as report:
            json.dump(scan_result.to_dict(), report, indent=4)

        # Display summary
        print("\n-------------------------")
        print("ACCESSIBILITY REVIEW SUMMARY")
        print("-------------------------")
        print("Total pages:", scan_result.pages)
        print("Checks performed:", scan_result.summary.checks)
        print("Passed:", scan_result.summary.passed)
        print("Issues:", scan_result.summary.issues)
        print("Items needing review:", scan_result.summary.human_review)
        print("Could not evaluate:", scan_result.summary.could_not_evaluate)
        print("Report saved to:", report_path)

        print("\nNote: This is an automated screening tool.")
        print("It does not certify ADA or WCAG compliance.")

        return scan_result

    except (FileNotFoundError, OSError) as error:
        print("Error opening PDF:", error)
        return None
    except Exception as error:  # noqa: BLE001
        print("An error occurred:", error)
        return None


if __name__ == "__main__":
    pdf_path = input("Enter the path to your PDF file: ").strip().strip('"')
    check_pdf(pdf_path)
