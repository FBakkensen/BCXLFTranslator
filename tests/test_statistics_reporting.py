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
