import pytest
import sys
import os
import io
from unittest.mock import patch

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.bcxlftranslator.statistics import TranslationStatistics

# Import the module we'll be creating
from src.bcxlftranslator.statistics_reporting import StatisticsReporter


class TestStatisticsReporter:
    """
    Test the console reporting functionality for translation statistics.
    """

    def test_format_basic_statistics_summary(self):
        """
        Given a TranslationStatistics object with counts
        When format_console_report is called with default detail level
        Then it should return a properly formatted summary string
        """
        # Create statistics with sample data
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()

        # Create reporter and format report
        reporter = StatisticsReporter()
        report = reporter.format_console_report(stats)

        # Check that the report contains expected elements
        assert "Translation Statistics Summary" in report
        assert "Total translations: 100" in report
        assert "Google Translate: 100 (100.0%)" in report

    def test_display_statistics_with_different_detail_levels(self):
        """
        Given a TranslationStatistics object
        When format_console_report is called with different detail levels
        Then it should return reports with appropriate detail
        """
        # Create statistics with sample data
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()

        # Create reporter
        reporter = StatisticsReporter()

        # Test summary level
        summary_report = reporter.format_console_report(stats, detail_level="summary")
        assert "Translation Statistics Summary" in summary_report
        assert len(summary_report.splitlines()) < 10  # Summary should be concise

        # Test detailed level
        detailed_report = reporter.format_console_report(stats, detail_level="detailed")
        assert "Translation Statistics (Detailed)" in detailed_report
        assert len(detailed_report.splitlines()) > len(summary_report.splitlines())

    def test_formatting_output_with_spacing_and_alignment(self):
        """
        Given a TranslationStatistics object
        When format_console_report is called (detailed)
        Then the output should have proper spacing and alignment
        """
        # Create statistics with sample data
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()

        # Create reporter and format report (detailed)
        reporter = StatisticsReporter()
        report = reporter.format_console_report(stats, detail_level="detailed")

        # Check for proper formatting
        lines = report.splitlines()

        # Find line with Google Translate statistics and check formatting
        gt_line = next((line for line in lines if "Google Translate" in line), None)

        assert gt_line is not None

        # Check that the numbers are properly formatted
        gt_number_pos = gt_line.find("100")
        assert gt_number_pos > 0

    def test_inclusion_of_timing_information(self):
        """
        Given a TranslationStatistics object and timing information
        When format_console_report is called with timing data
        Then the report should include timing information
        """
        # Create statistics with sample data
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()

        # Create reporter and format report with timing
        reporter = StatisticsReporter()
        report = reporter.format_console_report(
            stats,
            duration_seconds=120.5,
            start_time="2023-05-05 10:00:00",
            end_time="2023-05-05 10:02:00"
        )

        # Check for timing information
        assert "Duration: 2m 0.5s" in report
        assert "Start time: 2023-05-05 10:00:00" in report
        assert "End time: 2023-05-05 10:02:00" in report

    def test_handling_empty_statistics(self):
        """
        Given an empty TranslationStatistics object
        When format_console_report is called
        Then it should handle the edge case gracefully
        """
        # Create empty statistics
        stats = TranslationStatistics()

        # Create reporter and format report
        reporter = StatisticsReporter()
        report = reporter.format_console_report(stats)

        # Check that the report handles empty stats
        assert "Total translations: 0" in report
        assert "Google Translate: 0 (100.0%)" in report

    def test_output_adapts_to_terminal_width(self):
        """
        Given a TranslationStatistics object and different terminal widths
        When format_console_report is called with different widths
        Then the output should adapt to the specified width
        """
        # Create statistics with sample data
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()

        # Create reporter
        reporter = StatisticsReporter()

        # Test with narrow terminal
        narrow_report = reporter.format_console_report(stats, terminal_width=40)
        narrow_lines = narrow_report.splitlines()
        assert all(len(line) <= 40 for line in narrow_lines)

        # Test with wide terminal
        wide_report = reporter.format_console_report(stats, terminal_width=100)
        wide_lines = wide_report.splitlines()

        # The wide report should have some lines longer than the narrow report
        assert any(len(line) > 40 for line in wide_lines)

    def test_print_statistics_to_console(self):
        """
        Given a TranslationStatistics object
        When print_statistics is called
        Then it should print the formatted report to the console
        """
        # Create statistics with sample data
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()

        # Create reporter
        reporter = StatisticsReporter()

        # Capture stdout
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            reporter.print_statistics(stats)
            console_output = fake_stdout.getvalue()

        # Check that the output contains expected elements
        assert "Translation Statistics Summary" in console_output
        assert "Total translations: 100" in console_output
        assert "Google Translate: 100 (100.0%)" in console_output



    def test_export_csv_correct_headers(self, tmp_path):
        """
        Given a TranslationStatistics object
        When export_statistics_csv is called
        Then the generated CSV should have correct headers for statistics data
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.csv"
        reporter = StatisticsReporter()
        reporter.export_statistics_csv(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            header = f.readline().strip()
        assert header.startswith("Total translations,Google Translate")

    def test_export_csv_data_rows_match_statistics(self, tmp_path):
        """
        Given a TranslationStatistics object with data
        When export_statistics_csv is called
        Then the CSV data row should match the statistics values accurately
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.csv"
        reporter = StatisticsReporter()
        reporter.export_statistics_csv(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
        assert "100" in lines[1]

    def test_export_csv_escaping_special_characters(self, tmp_path):
        """
        Given a TranslationStatistics object with special characters in fields
        When export_statistics_csv is called
        Then special characters should be properly escaped in the CSV output
        """
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 1
        stats.google_translate_count = 2
        stats.extra_info = 'Value with,comma and "quote"'  # Simulate extra info field
        file_path = tmp_path / "stats.csv"
        reporter = StatisticsReporter()
        # Monkeypatch reporter to include extra_info
        def fake_row(stats):
            return [stats.microsoft_terminology_count, stats.google_translate_count, stats.extra_info]
        reporter._csv_data_row = fake_row
        reporter._csv_headers = lambda: ["Microsoft Terminology", "Google Translate", "Extra Info"]
        reporter.export_statistics_csv(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        assert '"Value with,comma and ""quote"""' in content

    def test_export_csv_file_overwrite_and_creation(self, tmp_path):
        """
        Given a file path for CSV output
        When export_statistics_csv is called with overwrite option
        Then it should create a new file or overwrite existing file as specified
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 7
        file_path = tmp_path / "stats.csv"
        file_path.write_text("old content", encoding="utf-8")
        reporter = StatisticsReporter()
        reporter.export_statistics_csv(stats, file_path, overwrite=True)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        assert "old content" not in content
        assert "Google Translate" in content

    def test_export_csv_file_system_errors(self, tmp_path):
        """
        Given a file path with restricted permissions
        When export_statistics_csv is called
        Then it should handle file system errors gracefully (e.g., permission denied)
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100

        # Create a directory where we'll try to create a file (which will fail)
        file_path = tmp_path / "nonexistent_dir" / "stats.csv"

        reporter = StatisticsReporter()
        with pytest.raises(FileNotFoundError):
            reporter.export_statistics_csv(stats, file_path)

    def test_export_csv_parsable_by_standard_csv_parser(self, tmp_path):
        """
        Given a generated CSV file
        When read by the Python csv module
        Then it should be parsed without errors and match the statistics data
        """
        import csv
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.csv"
        reporter = StatisticsReporter()
        reporter.export_statistics_csv(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows
        assert int(rows[0]["Google Translate"]) == 100

    def test_export_json_valid_output(self, tmp_path):
        """
        Given a TranslationStatistics object with data
        When export_statistics_json is called
        Then it should produce valid JSON output
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.json"
        reporter = StatisticsReporter()
        reporter.export_statistics_json(stats, file_path)
        import json
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert data["statistics"]["google_translate_count"] == 100
        assert data["statistics"]["total_count"] == 100

    def test_export_json_structure_and_fields(self, tmp_path):
        """
        Given a TranslationStatistics object with nested data
        When export_statistics_json is called
        Then the JSON structure should include all relevant fields and nesting
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.nested = {"by_object_type": {"Table": 50, "Page": 50}}
        file_path = tmp_path / "stats.json"
        reporter = StatisticsReporter()
        reporter.export_statistics_json(stats, file_path)
        import json
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "statistics" in data
        assert "nested" in data["statistics"]
        assert "by_object_type" in data["statistics"]["nested"]
        assert data["statistics"]["nested"]["by_object_type"]["Table"] == 50

    def test_export_json_includes_metadata(self, tmp_path):
        """
        Given a TranslationStatistics object
        When export_statistics_json is called
        Then the JSON should include metadata (timestamp, version, run info)
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        file_path = tmp_path / "stats.json"
        reporter = StatisticsReporter()
        reporter.export_statistics_json(stats, file_path)
        import json
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "metadata" in data
        assert "timestamp" in data["metadata"]
        assert "version" in data["metadata"]
        assert "run_info" in data["metadata"]

    def test_export_json_pretty_print(self, tmp_path):
        """
        Given a TranslationStatistics object
        When export_statistics_json is called with pretty_print=True
        Then the JSON output should be indented for readability
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        file_path = tmp_path / "stats.json"
        reporter = StatisticsReporter()
        reporter.export_statistics_json(stats, file_path, pretty_print=True)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        assert "\n  " in content or "\n    " in content  # Indentation present

    def test_export_json_streaming_large_dataset(self, tmp_path):
        """
        Given a very large TranslationStatistics-like object
        When export_statistics_json is called
        Then it should stream or handle writing without memory errors
        """
        class LargeStats:
            def __init__(self, n):
                self.google_translate_count = n
                self.total_count = n
                self.nested = {"by_object_type": {str(i): i for i in range(n)}}
        large_stats = LargeStats(10000)
        file_path = tmp_path / "large_stats.json"
        reporter = StatisticsReporter()
        # Should not raise MemoryError
        reporter.export_statistics_json(large_stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            import json
            data = json.load(f)
        assert data["statistics"]["google_translate_count"] == 10000
        assert len(data["statistics"]["nested"]["by_object_type"]) == 10000

    def test_export_html_generates_valid_html(self, tmp_path):
        """
        Given a TranslationStatistics object with sample data
        When export_statistics_html is called
        Then the output file should contain valid HTML
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.html"
        reporter = StatisticsReporter()
        reporter.export_statistics_html(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        assert content.strip().startswith("<!DOCTYPE html>")
        assert "<html" in content and "</html>" in content

    def test_export_html_includes_css_and_js(self, tmp_path):
        """
        Given a TranslationStatistics object
        When export_statistics_html is called
        Then the HTML should include embedded CSS and JavaScript
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.html"
        reporter = StatisticsReporter()
        reporter.export_statistics_html(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        assert "<style" in content and "</style>" in content
        assert "<script" in content and "</script>" in content

    def test_export_html_creates_data_table(self, tmp_path):
        """
        Given a TranslationStatistics object with counts
        When export_statistics_html is called
        Then the HTML should include a table with correct statistics values
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.html"
        reporter = StatisticsReporter()
        reporter.export_statistics_html(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        assert "<table" in content and "</table>" in content
        assert "100" in content

    def test_export_html_includes_chart_visualization(self, tmp_path):
        """
        Given a TranslationStatistics object with source percentages
        When export_statistics_html is called
        Then the HTML should include chart visualization data for source percentages
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.html"
        reporter = StatisticsReporter()
        reporter.export_statistics_html(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        assert "chart" in content.lower() or "canvas" in content.lower()
        assert "100" in content

    def test_export_html_is_self_contained(self, tmp_path):
        """
        Given a TranslationStatistics object
        When export_statistics_html is called
        Then the HTML report should be self-contained (no external dependencies)
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.html"
        reporter = StatisticsReporter()
        reporter.export_statistics_html(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        # Check for no external CSS/JS links
        assert "<link rel=" not in content
        assert "<script src=" not in content

    def test_export_html_validity_against_w3c(self, tmp_path):
        """
        Given a generated HTML report
        When checked for validity
        Then it should conform to basic W3C HTML standards (structure, tags)
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        file_path = tmp_path / "stats.html"
        reporter = StatisticsReporter()
        reporter.export_statistics_html(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        # Basic checks for valid structure
        assert "<!DOCTYPE html>" in content
        assert content.count("<html") == 1
        assert content.count("</html>") == 1
        assert content.count("<body") == 1
        assert content.count("</body>") == 1

    def test_unified_api_generates_all_formats(self, tmp_path):
        """
        Given a TranslationStatistics object
        When the unified report API is called for each supported format
        Then it should generate valid reports in all formats (console, CSV, JSON, HTML)
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        reporter = StatisticsReporter()
        formats = ["console", "csv", "json", "html"]
        outputs = {}
        for fmt in formats:
            if fmt == "console":
                outputs[fmt] = reporter.generate_report(stats, format=fmt)
                assert "Translation Statistics" in outputs[fmt]
            else:
                file_path = tmp_path / f"stats.{fmt}"
                result = reporter.generate_report(stats, format=fmt, output_path=file_path)
                assert result is None
                assert file_path.exists()
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                if fmt == "csv":
                    assert "," in content
                elif fmt == "json":
                    assert "metadata" in content and "statistics" in content
                elif fmt == "html":
                    assert "<html" in content.lower()

    def test_unified_api_with_configurable_options(self, tmp_path):
        """
        Given a TranslationStatistics object and various config options
        When the unified report API is called with options
        Then it should generate reports reflecting those options (e.g., detail level, pretty-print)
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        reporter = StatisticsReporter()
        # Example configurable options
        config = {"detail_level": "detailed", "pretty": True}
        report = reporter.generate_report(stats, format="console", config=config)
        assert "Detailed" in report or "detail" in report.lower()
        json_path = tmp_path / "stats.json"
        reporter.generate_report(stats, format="json", output_path=json_path, config={"pretty": True})
        with open(json_path, encoding="utf-8") as f:
            content = f.read()
        assert "\n    " in content  # Pretty-printed JSON has indentation

    def test_unified_api_format_detection(self, tmp_path):
        """
        Given a TranslationStatistics object and an output file path with extension
        When the unified report API is called without explicit format
        Then it should detect the format from the file extension and generate the correct report
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        reporter = StatisticsReporter()
        html_path = tmp_path / "stats_report.html"
        reporter.generate_report(stats, output_path=html_path)
        with open(html_path, encoding="utf-8") as f:
            content = f.read()
        assert "<html" in content.lower()
        csv_path = tmp_path / "stats_report.csv"
        reporter.generate_report(stats, output_path=csv_path)
        with open(csv_path, encoding="utf-8") as f:
            content = f.read()
        assert "," in content

    def test_unified_api_includes_timestamp_and_session_info(self, tmp_path):
        """
        Given a TranslationStatistics object
        When the unified report API is called
        Then all generated reports should include timestamp and session information
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        reporter = StatisticsReporter()
        # Assume session_info is provided or generated
        session_info = {"session_id": "abc123", "user": "testuser"}
        html_path = tmp_path / "stats.html"
        reporter.generate_report(stats, format="html", output_path=html_path, session_info=session_info)
        with open(html_path, encoding="utf-8") as f:
            content = f.read()
        assert "session_id" in content or "Session" in content
        assert "timestamp" in content or "time" in content.lower()
        json_path = tmp_path / "stats.json"
        reporter.generate_report(stats, format="json", output_path=json_path, session_info=session_info)
        with open(json_path, encoding="utf-8") as f:
            content = f.read()
        assert "session_id" in content
        assert "timestamp" in content

    def test_unified_api_batch_generation(self, tmp_path):
        """
        Given a TranslationStatistics object
        When the unified report API is called to generate multiple formats at once
        Then it should produce all requested report files correctly
        """
        stats = TranslationStatistics()
        stats.google_translate_count = 100
        stats.calculate_percentages()
        reporter = StatisticsReporter()
        output_map = {
            "csv": tmp_path / "batch_stats.csv",
            "json": tmp_path / "batch_stats.json",
            "html": tmp_path / "batch_stats.html",
        }
        reporter.generate_report(stats, batch_outputs=output_map)
        for fmt, path in output_map.items():
            assert path.exists()
            with open(path, encoding="utf-8") as f:
                content = f.read()
            if fmt == "html":
                assert "<html" in content.lower()
            elif fmt == "json":
                assert "{" in content
            elif fmt == "csv":
                assert "," in content


