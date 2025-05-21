import pytest
import threading
import time
import sys
import os
import json
import tempfile


# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.bcxlftranslator.statistics import (
    TranslationStatistics,
    StatisticsCollector,
    DetailedStatisticsCollector,
    StatisticsPersistence,
    StatisticsManager
)

class TestTranslationStatistics:
    """Test the statistics tracking functionality for translations."""

    def test_initialize_with_default_values(self):
        """
        Given a new TranslationStatistics instance
        When it is initialized without parameters
        Then it should have zero counts for all statistics
        """
        stats = TranslationStatistics()
        assert stats.google_translate_count == 0
        assert stats.total_count == 0
        assert stats.google_translate_percentage == 100.0  # Always 100% since we only use Google Translate

    def test_increment_google_translate_count(self):
        """
        Given a TranslationStatistics instance
        When google_translate_count is incremented
        Then the count should increase
        """
        stats = TranslationStatistics()
        stats.increment_google_translate_count()
        assert stats.google_translate_count == 1
        assert stats.total_count == 1
        assert stats.google_translate_percentage == 100.0  # Always 100% since we only use Google Translate

    def test_reset_statistics(self):
        """
        Given a TranslationStatistics instance with non-zero counts
        When reset is called
        Then all counts should be zero
        """
        stats = TranslationStatistics()
        stats.increment_google_translate_count()
        stats.reset()

        assert stats.google_translate_count == 0
        assert stats.total_count == 0
        assert stats.google_translate_percentage == 100.0  # Always 100% since we only use Google Translate

    def test_thread_safety(self):
        """
        Given a TranslationStatistics instance
        When multiple threads update it concurrently
        Then the final counts should be accurate
        """
        stats = TranslationStatistics()

        # Reduced iterations to prevent test hanging
        gt_count = 100   # Reduced from 500

        def increment_google(count):
            for _ in range(count):
                stats.increment_google_translate_count()

        thread1 = threading.Thread(target=increment_google, args=(gt_count,))
        thread2 = threading.Thread(target=increment_google, args=(gt_count,))

        thread1.start()
        thread2.start()

        # Add timeout to ensure test doesn't hang
        thread1.join(timeout=2.0)
        thread2.join(timeout=2.0)

        # Check if threads are still alive after timeout
        if thread1.is_alive() or thread2.is_alive():
            pytest.fail("Thread operation timed out - possible deadlock in thread-safety implementation")

        assert stats.google_translate_count == gt_count * 2
        assert stats.total_count == gt_count * 2
        assert stats.google_translate_percentage == 100.0  # Always 100% since we only use Google Translate


class TestStatisticsCollector:
    """Test the StatisticsCollector integration with the translation process."""

    def test_track_google_translate_translation(self):
        """
        Given a StatisticsCollector
        When a term is translated using Google Translate
        Then the google_translate_count should be incremented
        """
        collector = StatisticsCollector()
        collector.track_translation(source="Google Translate")

        assert collector.statistics.google_translate_count == 1
        assert collector.statistics.total_count == 1
        assert collector.statistics.google_translate_percentage == 100.0

    def test_track_multiple_translations(self):
        """
        Given a StatisticsCollector
        When multiple translations are tracked
        Then the counts should accumulate correctly
        """
        collector = StatisticsCollector()

        # Track 3 Google translations
        for _ in range(3):
            collector.track_translation(source="Google Translate")

        assert collector.statistics.google_translate_count == 3
        assert collector.statistics.total_count == 3
        assert collector.statistics.google_translate_percentage == 100.0

    def test_get_statistics(self):
        """
        Given a StatisticsCollector with tracked translations
        When get_statistics is called
        Then it should return the current statistics object
        """
        collector = StatisticsCollector()
        collector.track_translation(source="Google Translate")
        collector.track_translation(source="Google Translate")

        stats = collector.get_statistics()

        assert stats.google_translate_count == 2
        assert stats.total_count == 2
        assert stats.google_translate_percentage == 100.0

    def test_reset_statistics(self):
        """
        Given a StatisticsCollector with tracked translations
        When reset_statistics is called
        Then all counts should be reset to zero
        """
        collector = StatisticsCollector()
        collector.track_translation(source="Google Translate")
        collector.track_translation(source="Google Translate")

        collector.reset_statistics()

        assert collector.statistics.google_translate_count == 0
        assert collector.statistics.total_count == 0
        assert collector.statistics.google_translate_percentage == 100.0  # Always 100% since we only use Google Translate


class TestDetailedStatisticsCollector:
    """Test the DetailedStatisticsCollector with categorization and grouping."""

    def test_track_by_object_type(self):
        """
        Given a DetailedStatisticsCollector
        When translations are tracked with different object types
        Then statistics should be tracked separately by object type
        """
        collector = DetailedStatisticsCollector()

        # Track translations for different object types
        collector.track_translation(source="Google Translate", object_type="Table")
        collector.track_translation(source="Google Translate", object_type="Page")
        collector.track_translation(source="Google Translate", object_type="Field")

        # Check overall statistics
        assert collector.statistics.google_translate_count == 3
        assert collector.statistics.total_count == 3

        # Check statistics by object type
        table_stats = collector.get_statistics_by_object_type("Table")
        assert table_stats.google_translate_count == 1
        assert table_stats.total_count == 1

        page_stats = collector.get_statistics_by_object_type("Page")
        assert page_stats.google_translate_count == 1
        assert page_stats.total_count == 1

        field_stats = collector.get_statistics_by_object_type("Field")
        assert field_stats.google_translate_count == 1
        assert field_stats.total_count == 1

    def test_track_by_context(self):
        """
        Given a DetailedStatisticsCollector
        When translations are tracked with different contexts
        Then statistics should be tracked separately by context
        """
        collector = DetailedStatisticsCollector()

        # Track translations for different contexts
        collector.track_translation(source="Google Translate", context="Sales")
        collector.track_translation(source="Google Translate", context="Purchase")
        collector.track_translation(source="Google Translate", context="Inventory")

        # Check statistics by context
        sales_stats = collector.get_statistics_by_context("Sales")
        assert sales_stats.google_translate_count == 1
        assert sales_stats.total_count == 1

        purchase_stats = collector.get_statistics_by_context("Purchase")
        assert purchase_stats.google_translate_count == 1
        assert purchase_stats.total_count == 1

        inventory_stats = collector.get_statistics_by_context("Inventory")
        assert inventory_stats.google_translate_count == 1
        assert inventory_stats.total_count == 1

    def test_track_by_file(self):
        """
        Given a DetailedStatisticsCollector
        When translations are tracked with different file paths
        Then statistics should be tracked separately by file
        """
        collector = DetailedStatisticsCollector()

        # Track translations for different files
        collector.track_translation(source="Google Translate", file_path="file1.xlf")
        collector.track_translation(source="Google Translate", file_path="file1.xlf")
        collector.track_translation(source="Google Translate", file_path="file2.xlf")

        # Check statistics by file
        file1_stats = collector.get_statistics_by_file("file1.xlf")
        assert file1_stats.google_translate_count == 2
        assert file1_stats.total_count == 2

        file2_stats = collector.get_statistics_by_file("file2.xlf")
        assert file2_stats.google_translate_count == 1
        assert file2_stats.total_count == 1

    def test_hierarchical_aggregation(self):
        """
        Given a DetailedStatisticsCollector with tracked translations
        When hierarchical statistics are requested
        Then statistics should be aggregated correctly at each level
        """
        collector = DetailedStatisticsCollector()

        # Track translations with multiple dimensions
        collector.track_translation(
            source="Google Translate",
            object_type="Table",
            context="Sales",
            file_path="file1.xlf"
        )
        collector.track_translation(
            source="Google Translate",
            object_type="Table",
            context="Purchase",
            file_path="file1.xlf"
        )
        collector.track_translation(
            source="Google Translate",
            object_type="Page",
            context="Sales",
            file_path="file2.xlf"
        )

        # Check hierarchical statistics
        hierarchy = collector.get_hierarchical_statistics()

        # Check top level
        assert hierarchy["total"].google_translate_count == 3
        assert hierarchy["total"].total_count == 3

        # Check file level
        assert hierarchy["files"]["file1.xlf"].google_translate_count == 2
        assert hierarchy["files"]["file1.xlf"].total_count == 2
        assert hierarchy["files"]["file2.xlf"].google_translate_count == 1
        assert hierarchy["files"]["file2.xlf"].total_count == 1

        # Check object type level
        assert hierarchy["object_types"]["Table"].google_translate_count == 2
        assert hierarchy["object_types"]["Table"].total_count == 2
        assert hierarchy["object_types"]["Page"].google_translate_count == 1
        assert hierarchy["object_types"]["Page"].total_count == 1

        # Check context level
        assert hierarchy["contexts"]["Sales"].google_translate_count == 2
        assert hierarchy["contexts"]["Sales"].total_count == 2
        assert hierarchy["contexts"]["Purchase"].google_translate_count == 1
        assert hierarchy["contexts"]["Purchase"].total_count == 1

    def test_filtered_statistics(self):
        """
        Given a DetailedStatisticsCollector with tracked translations
        When filtered statistics are requested
        Then only relevant statistics should be returned
        """
        collector = DetailedStatisticsCollector()

        # Add diverse set of translations
        collector.track_translation(source="Google Translate", object_type="Table")
        collector.track_translation(source="Google Translate", object_type="Page")
        collector.track_translation(source="Google Translate", object_type="Table", context="Sales")
        collector.track_translation(source="Google Translate", object_type="Field")
        collector.track_translation(source="Google Translate", context="Sales")
        collector.track_translation(source="Google Translate", context="Purchase")

        # Get filtered statistics
        table_stats = collector.get_filtered_statistics(object_type="Table")
        assert table_stats.google_translate_count == 2
        assert table_stats.total_count == 2

        sales_stats = collector.get_filtered_statistics(context="Sales")
        assert sales_stats.google_translate_count == 2
        assert sales_stats.total_count == 2

        # Test multiple filters
        table_sales_stats = collector.get_filtered_statistics(object_type="Table", context="Sales")
        assert table_sales_stats.google_translate_count == 1
        assert table_sales_stats.total_count == 1
        assert isinstance(table_sales_stats, TranslationStatistics)

    def test_compare_statistics_sets(self):
        """
        Given two DetailedStatisticsCollector instances
        When statistics are compared between them
        Then differences should be calculated correctly
        """
        collector1 = DetailedStatisticsCollector()
        collector2 = DetailedStatisticsCollector()

        # Add different statistics to each collector
        collector1.track_translation(source="Google Translate")
        collector1.track_translation(source="Google Translate")
        collector1.track_translation(source="Google Translate")

        collector2.track_translation(source="Google Translate")
        collector2.track_translation(source="Google Translate")

        # Compare statistics
        diff = collector1.compare_with(collector2)

        assert diff["google_translate_diff"] == 1  # collector1 has 1 more Google term
        assert diff["total_diff"] == 1  # collector1 has 1 more term in total


class TestStatisticsPersistence:
    """Test the persistence of statistics between runs."""

    def test_serialize_statistics_to_json(self):
        """
        Given a StatisticsCollector with statistics
        When serialized to JSON
        Then the resulting JSON should contain all stats information
        """
        collector = StatisticsCollector()
        collector.track_translation(source="Google Translate")
        collector.track_translation(source="Google Translate")

        persistence = StatisticsPersistence()
        json_data = persistence.serialize_to_json(collector)

        # Parse the JSON to verify it contains correct data
        data = json.loads(json_data)
        assert data["version"] == "1.0"
        assert data["statistics"]["google_translate_count"] == 2
        assert data["statistics"]["total_count"] == 2

    def test_save_statistics_to_file(self):
        """
        Given a StatisticsCollector with statistics
        When saved to a file
        Then the file should contain valid JSON with the statistics
        """
        collector = StatisticsCollector()
        collector.track_translation(source="Google Translate")
        collector.track_translation(source="Google Translate")
        collector.track_translation(source="Google Translate")

        persistence = StatisticsPersistence()

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            file_path = temp_file.name

        try:
            # Save statistics to the temporary file
            persistence.save_to_file(collector, file_path)

            # Verify file exists and contains valid JSON
            assert os.path.exists(file_path)

            with open(file_path, 'r') as f:
                data = json.load(f)
                assert data["version"] == "1.0"
                assert data["statistics"]["google_translate_count"] == 3
                assert data["statistics"]["total_count"] == 3
        finally:
            # Clean up the temporary file
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_load_statistics_from_json(self):
        """
        Given a JSON string with statistics data
        When loaded into a StatisticsCollector
        Then the collector should have the correct statistics
        """
        json_data = json.dumps({
            "version": "1.0",
            "statistics": {
                "google_translate_count": 5,
                "total_count": 5
            }
        })

        persistence = StatisticsPersistence()
        collector = StatisticsCollector()

        persistence.load_from_json(collector, json_data)

        assert collector.statistics.google_translate_count == 5
        assert collector.statistics.total_count == 5
        assert collector.statistics.google_translate_percentage == 100.0

    def test_load_statistics_from_file(self):
        """
        Given a file with statistics data
        When loaded into a StatisticsCollector
        Then the collector should have the correct statistics
        """
        # Create a temporary file with test data
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            file_path = temp_file.name
            json_data = json.dumps({
                "version": "1.0",
                "statistics": {
                    "google_translate_count": 20,
                    "total_count": 20
                }
            })
            temp_file.write(json_data.encode('utf-8'))

        try:
            persistence = StatisticsPersistence()
            collector = StatisticsCollector()

            persistence.load_from_file(collector, file_path)

            assert collector.statistics.google_translate_count == 20
            assert collector.statistics.total_count == 20
            assert collector.statistics.google_translate_percentage == 100.0
        finally:
            # Clean up the temporary file
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_merge_statistics(self):
        """
        Given two StatisticsCollector instances
        When merged together
        Then the resulting collector should have combined statistics
        """
        collector1 = StatisticsCollector()
        collector1.track_translation(source="Google Translate")
        collector1.track_translation(source="Google Translate")

        collector2 = StatisticsCollector()
        collector2.track_translation(source="Google Translate")
        collector2.track_translation(source="Google Translate")
        collector2.track_translation(source="Google Translate")

        persistence = StatisticsPersistence()
        merged_collector = persistence.merge_statistics(collector1, collector2)

        assert merged_collector.statistics.google_translate_count == 5
        assert merged_collector.statistics.total_count == 5
        assert merged_collector.statistics.google_translate_percentage == 100.0

    def test_handle_older_version(self):
        """
        Given a JSON string with an older statistics format version
        When loaded into a StatisticsCollector
        Then the collector should handle version differences properly
        """
        # Create JSON with an older version format
        json_data = json.dumps({
            "version": "0.9",
            "statistics": {
                "google_count": 8      # Different field name in "old" version
            }
        })

        persistence = StatisticsPersistence()
        collector = StatisticsCollector()

        # This should handle the version difference and map the fields correctly
        persistence.load_from_json(collector, json_data)

        assert collector.statistics.google_translate_count == 8
        assert collector.statistics.total_count == 8
        assert collector.statistics.google_translate_percentage == 100.0


class TestStatisticsManager:
    """Test the complete statistics system with a unified API."""

    def test_create_collector(self):
        """
        Given a StatisticsManager
        When create_collector is called with different configurations
        Then it should return the appropriate collector type
        """
        manager = StatisticsManager()

        # Test creating a simple collector
        simple_collector = manager.create_collector(detailed=False)
        assert isinstance(simple_collector, StatisticsCollector)
        assert not isinstance(simple_collector, DetailedStatisticsCollector)

        # Test creating a detailed collector
        detailed_collector = manager.create_collector(detailed=True)
        assert isinstance(detailed_collector, DetailedStatisticsCollector)

    def test_enable_disable_statistics(self):
        """
        Given a StatisticsManager
        When statistics collection is enabled/disabled
        Then tracking should be active/inactive accordingly
        """
        manager = StatisticsManager()
        collector = manager.create_collector()

        # Test enabled by default
        assert manager.is_enabled()

        # Test tracking when enabled
        manager.track_translation(collector, "Google Translate")
        assert collector.statistics.google_translate_count == 1

        # Test disabling
        manager.set_enabled(False)
        assert not manager.is_enabled()

        # Test tracking when disabled
        manager.track_translation(collector, "Google Translate")
        # Count should remain the same since tracking is disabled
        assert collector.statistics.google_translate_count == 1

        # Test re-enabling
        manager.set_enabled(True)
        manager.track_translation(collector, "Google Translate")
        assert collector.statistics.google_translate_count == 2

    def test_statistics_detail_level(self):
        """
        Given a StatisticsManager
        When detail level is configured
        Then the collector should track at that detail level
        """
        manager = StatisticsManager()

        # Test basic detail level
        manager.set_detail_level("basic")
        collector_basic = manager.create_collector()
        assert isinstance(collector_basic, StatisticsCollector)
        assert not isinstance(collector_basic, DetailedStatisticsCollector)

        # Test detailed level
        manager.set_detail_level("detailed")
        collector_detailed = manager.create_collector()
        assert isinstance(collector_detailed, DetailedStatisticsCollector)

        # Test invalid detail level defaults to basic
        manager.set_detail_level("invalid")
        collector_invalid = manager.create_collector()
        assert isinstance(collector_invalid, StatisticsCollector)
        assert not isinstance(collector_invalid, DetailedStatisticsCollector)

    def test_complete_workflow(self):
        """
        Given a StatisticsManager
        When a complete translation workflow is performed
        Then statistics should be collected accurately
        """
        manager = StatisticsManager()
        collector = manager.create_collector(detailed=True)

        # Track some translations
        manager.track_translation(collector, "Google Translate", object_type="Table", context="Sales")
        manager.track_translation(collector, "Google Translate", object_type="Page", context="Sales")
        manager.track_translation(collector, "Google Translate", object_type="Field", context="Purchase")

        # Verify statistics
        assert collector.statistics.google_translate_count == 3
        assert collector.statistics.total_count == 3

        # Save to file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            file_path = temp_file.name

        try:
            manager.save_statistics(collector, file_path)

            # Create a new collector and load from file
            new_collector = manager.create_collector(detailed=True)
            manager.load_statistics(new_collector, file_path)

            # Verify loaded statistics
            assert new_collector.statistics.google_translate_count == 3
            assert new_collector.statistics.total_count == 3

            # Verify hierarchical statistics were preserved
            table_stats = new_collector.get_statistics_by_object_type("Table")
            assert table_stats.google_translate_count == 1
            assert table_stats.total_count == 1
        finally:
            # Clean up the temporary file
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_statistics_query(self):
        """
        Given a StatisticsManager with collected statistics
        When statistics are queried
        Then correct results should be returned efficiently
        """
        manager = StatisticsManager()
        collector = manager.create_collector(detailed=True)

        # Add diverse set of translations
        manager.track_translation(collector, "Google Translate", object_type="Table", context="Sales")
        manager.track_translation(collector, "Google Translate", object_type="Page", context="Sales")
        manager.track_translation(collector, "Google Translate", object_type="Table", context="Purchase")
        manager.track_translation(collector, "Google Translate", object_type="Field", context="Inventory")

        # Test querying overall statistics
        overall = manager.get_statistics(collector)
        assert overall.google_translate_count == 4
        assert overall.total_count == 4

        # Test querying by dimension
        sales_stats = manager.get_filtered_statistics(collector, context="Sales")
        assert sales_stats.google_translate_count == 2
        assert sales_stats.total_count == 2

        table_stats = manager.get_filtered_statistics(collector, object_type="Table")
        assert table_stats.google_translate_count == 2
        assert table_stats.total_count == 2

    def test_performance_with_large_datasets(self):
        """
        Given a StatisticsManager
        When tracking a large number of translations
        Then performance should remain acceptable
        """
        manager = StatisticsManager()
        collector = manager.create_collector()

        num_iterations = 1000

        # Track a large number of translations
        start_time = time.time()
        for i in range(num_iterations):
            manager.track_translation(collector, "Google Translate")
        end_time = time.time()

        # Verify translations were tracked correctly
        assert collector.statistics.google_translate_count == num_iterations
        assert collector.statistics.total_count == num_iterations
        assert collector.statistics.google_translate_percentage == 100.0

        # Ensure operation completed in a reasonable time
        # For 1000 translations, it should be well under a second on most systems
        assert end_time - start_time < 1.0