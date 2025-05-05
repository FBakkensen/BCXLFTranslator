import pytest
import sys
import os
import io
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.bcxlftranslator.statistics import (
    TranslationStatistics,
    StatisticsCollector,
    DetailedStatisticsCollector,
    StatisticsManager
)

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
        stats.microsoft_terminology_count = 30
        stats.google_translate_count = 70
        stats.calculate_percentages()
        
        # Create reporter and format report
        reporter = StatisticsReporter()
        report = reporter.format_console_report(stats)
        
        # Check that the report contains expected elements
        assert "Translation Statistics Summary" in report
        assert "Total translations: 100" in report
        assert "Microsoft Terminology: 30 (30.0%)" in report
        assert "Google Translate: 70 (70.0%)" in report
    
    def test_display_statistics_with_different_detail_levels(self):
        """
        Given a TranslationStatistics object
        When format_console_report is called with different detail levels
        Then it should return reports with appropriate detail
        """
        # Create statistics with sample data
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 25
        stats.google_translate_count = 75
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
        stats.microsoft_terminology_count = 42
        stats.google_translate_count = 58
        stats.calculate_percentages()
        
        # Create reporter and format report (detailed)
        reporter = StatisticsReporter()
        report = reporter.format_console_report(stats, detail_level="detailed")
        
        # Check for proper formatting
        lines = report.splitlines()
        
        # Find lines with statistics and check alignment
        ms_line = next((line for line in lines if "Microsoft Terminology" in line), None)
        gt_line = next((line for line in lines if "Google Translate" in line), None)
        
        assert ms_line is not None
        assert gt_line is not None
        
        # Check that the numbers are aligned (same position in both lines)
        ms_number_pos = ms_line.find("42")
        gt_number_pos = gt_line.find("58")
        assert ms_number_pos == gt_number_pos
    
    def test_inclusion_of_timing_information(self):
        """
        Given a TranslationStatistics object and timing information
        When format_console_report is called with timing data
        Then the report should include timing information
        """
        # Create statistics with sample data
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 50
        stats.google_translate_count = 50
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
        assert "Microsoft Terminology: 0 (0.0%)" in report
        assert "Google Translate: 0 (0.0%)" in report
    
    def test_output_adapts_to_terminal_width(self):
        """
        Given a TranslationStatistics object and different terminal widths
        When format_console_report is called with different widths
        Then the output should adapt to the specified width
        """
        # Create statistics with sample data
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 40
        stats.google_translate_count = 60
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
        stats.microsoft_terminology_count = 35
        stats.google_translate_count = 65
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
        assert "Microsoft Terminology: 35 (35.0%)" in console_output
        assert "Google Translate: 65 (65.0%)" in console_output
    
    def test_detailed_statistics_collector_report(self):
        """
        Given a DetailedStatisticsCollector with data
        When format_console_report is called with a detailed collector
        Then it should include categorized statistics in the report
        """
        # Create a detailed collector with sample data
        collector = DetailedStatisticsCollector()
        
        # Add some categorized data
        collector.track_translation("Microsoft Terminology", object_type="Table")
        collector.track_translation("Microsoft Terminology", object_type="Page")
        collector.track_translation("Google Translate", object_type="Field")
        
        # Create reporter and format report
        reporter = StatisticsReporter()
        report = reporter.format_detailed_console_report(collector)
        
        # Check that the report contains categorized statistics
        assert "Statistics by Object Type" in report
        assert "Table" in report
        assert "Page" in report
        assert "Field" in report

    def test_export_csv_correct_headers(self, tmp_path):
        """
        Given a TranslationStatistics object
        When export_statistics_csv is called
        Then the generated CSV should have correct headers for statistics data
        """
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 12
        stats.google_translate_count = 88
        stats.calculate_percentages()
        file_path = tmp_path / "stats.csv"
        reporter = StatisticsReporter()
        reporter.export_statistics_csv(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            header = f.readline().strip()
        assert header.startswith("Total translations,Microsoft Terminology,Google Translate")

    def test_export_csv_data_rows_match_statistics(self, tmp_path):
        """
        Given a TranslationStatistics object with data
        When export_statistics_csv is called
        Then the CSV data row should match the statistics values accurately
        """
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 55
        stats.google_translate_count = 45
        stats.calculate_percentages()
        file_path = tmp_path / "stats.csv"
        reporter = StatisticsReporter()
        reporter.export_statistics_csv(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
        assert "55" in lines[1] and "45" in lines[1]

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
        stats.microsoft_terminology_count = 3
        stats.google_translate_count = 7
        file_path = tmp_path / "stats.csv"
        file_path.write_text("old content", encoding="utf-8")
        reporter = StatisticsReporter()
        reporter.export_statistics_csv(stats, file_path, overwrite=True)
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        assert "old content" not in content
        assert "Microsoft Terminology" in content

    def test_export_csv_file_system_errors(self, tmp_path, monkeypatch):
        """
        Given a file path with restricted permissions
        When export_statistics_csv is called
        Then it should handle file system errors gracefully (e.g., permission denied)
        """
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 1
        stats.google_translate_count = 2
        file_path = tmp_path / "stats.csv"
        reporter = StatisticsReporter()
        def raise_permission(*a, **kw):
            raise PermissionError("Permission denied!")
        monkeypatch.setattr("builtins.open", raise_permission)
        with pytest.raises(PermissionError):
            reporter.export_statistics_csv(stats, file_path)

    def test_export_csv_parsable_by_standard_csv_parser(self, tmp_path):
        """
        Given a generated CSV file
        When read by the Python csv module
        Then it should be parsed without errors and match the statistics data
        """
        import csv
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 21
        stats.google_translate_count = 79
        stats.calculate_percentages()
        file_path = tmp_path / "stats.csv"
        reporter = StatisticsReporter()
        reporter.export_statistics_csv(stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows
        assert int(rows[0]["Microsoft Terminology"]) == 21
        assert int(rows[0]["Google Translate"]) == 79

    def test_export_json_valid_output(self, tmp_path):
        """
        Given a TranslationStatistics object with data
        When export_statistics_json is called
        Then it should produce valid JSON output
        """
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 10
        stats.google_translate_count = 20
        stats.calculate_percentages()
        file_path = tmp_path / "stats.json"
        reporter = StatisticsReporter()
        reporter.export_statistics_json(stats, file_path)
        import json
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert data["statistics"]["microsoft_terminology_count"] == 10
        assert data["statistics"]["google_translate_count"] == 20

    def test_export_json_structure_and_fields(self, tmp_path):
        """
        Given a TranslationStatistics object with nested data
        When export_statistics_json is called
        Then the JSON structure should include all relevant fields and nesting
        """
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 5
        stats.google_translate_count = 15
        stats.nested = {"by_object_type": {"Table": 2, "Page": 3}}
        file_path = tmp_path / "stats.json"
        reporter = StatisticsReporter()
        reporter.export_statistics_json(stats, file_path)
        import json
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "statistics" in data
        assert "nested" in data["statistics"]
        assert "by_object_type" in data["statistics"]["nested"]
        assert data["statistics"]["nested"]["by_object_type"]["Table"] == 2

    def test_export_json_includes_metadata(self, tmp_path):
        """
        Given a TranslationStatistics object
        When export_statistics_json is called
        Then the JSON should include metadata (timestamp, version, run info)
        """
        stats = TranslationStatistics()
        stats.microsoft_terminology_count = 1
        stats.google_translate_count = 2
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
        stats.microsoft_terminology_count = 3
        stats.google_translate_count = 7
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
                self.microsoft_terminology_count = n
                self.google_translate_count = n
                self.nested = {"by_object_type": {str(i): i for i in range(n)}}
        large_stats = LargeStats(10000)
        file_path = tmp_path / "large_stats.json"
        reporter = StatisticsReporter()
        # Should not raise MemoryError
        reporter.export_statistics_json(large_stats, file_path)
        with open(file_path, encoding="utf-8") as f:
            import json
            data = json.load(f)
        assert data["statistics"]["microsoft_terminology_count"] == 10000
        assert len(data["statistics"]["nested"]["by_object_type"]) == 10000
