import csv
import logging

class ExtractionResultsReporter:
    """
    Reporting for terminology extraction results (step 8.4).
    """
    def format_summary_report(self, extraction_results):
        """
        Given extraction results with added, updated, skipped, errors, and warnings
        When the extraction summary report is generated
        Then it should include correct counts for each category
        """
        lines = [
            "Extraction Results Summary:",
            f"Added: {extraction_results.get('added', 0)}",
            f"Updated: {extraction_results.get('updated', 0)}",
            f"Skipped: {extraction_results.get('skipped', 0)}",
            f"Errors: {extraction_results.get('errors', 0)}",
            f"Warnings: {extraction_results.get('warnings', 0)}",
        ]
        return "\n".join(lines)

    def format_detailed_report(self, extraction_results):
        """
        Given extraction results with term-by-term info
        When the detailed extraction report is generated
        Then each term and its action should be listed
        """
        lines = ["Extraction Results (Detailed):"]
        for t in extraction_results.get('terms', []):
            lines.append(f"Term: {t.get('term', '')} | Action: {t.get('action', '')}")
        return "\n".join(lines)

    def export_csv_report(self, extraction_results, csv_path):
        """
        Given extraction results
        When the CSV report is generated
        Then the CSV should have correct headers and rows for each term
        """
        terms = extraction_results.get('terms', [])
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['term', 'action'])
            writer.writeheader()
            for t in terms:
                writer.writerow({'term': t.get('term', ''), 'action': t.get('action', '')})

    def log_issues(self, extraction_results):
        """
        Given extraction results with errors and warnings
        When the extraction report is generated
        Then errors and warnings should be logged for troubleshooting
        """
        for err in extraction_results.get('error_details', []):
            logging.warning(err)
        for warn in extraction_results.get('warning_details', []):
            logging.warning(warn)
