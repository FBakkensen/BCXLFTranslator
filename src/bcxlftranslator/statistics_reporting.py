"""
Module for generating reports from translation statistics.

This module provides functionality for formatting and displaying
statistics about translations in various formats, primarily for
console output.
"""

import time
from datetime import datetime
import shutil
import csv
import json
from datetime import timezone


class StatisticsReporter:
    """
    Class for generating formatted reports from translation statistics.
    
    This class provides methods to format statistics into readable reports
    for console output with various levels of detail.
    """
    
    def __init__(self):
        """
        Initialize a new StatisticsReporter instance.
        """
        # Get terminal width or use default if not available
        try:
            self._default_terminal_width = shutil.get_terminal_size().columns
        except (AttributeError, OSError):
            self._default_terminal_width = 80
    
    def format_console_report(self, statistics, detail_level="summary", 
                             terminal_width=None, duration_seconds=None,
                             start_time=None, end_time=None):
        """
        Format statistics for console output.
        
        Args:
            statistics: The TranslationStatistics object to format.
            detail_level (str): Level of detail to include ("summary" or "detailed").
            terminal_width (int, optional): Width of the terminal to format for.
            duration_seconds (float, optional): Duration of the translation process in seconds.
            start_time (str, optional): Start time of the translation process.
            end_time (str, optional): End time of the translation process.
            
        Returns:
            str: Formatted statistics report for console output.
        """
        width = terminal_width or self._default_terminal_width
        
        # Start with the header
        if detail_level == "detailed":
            report = ["Translation Statistics (Detailed)".center(width)]
        else:
            report = ["Translation Statistics Summary".center(width)]
        
        report.append("=" * width)
        report.append("")
        
        # Add basic statistics
        total = statistics.total_count
        ms_count = statistics.microsoft_terminology_count
        gt_count = statistics.google_translate_count
        ms_pct = statistics.microsoft_terminology_percentage
        gt_pct = statistics.google_translate_percentage
        
        if detail_level == "summary":
            report.append(f"Total translations: {total}")
            report.append(f"Microsoft Terminology: {ms_count} ({ms_pct:.1f}%)")
            report.append(f"Google Translate: {gt_count} ({gt_pct:.1f}%)")
        else:
            # Formatting for alignment in detailed view
            label_width = 22
            num_width = max(len(str(ms_count)), len(str(gt_count)), 3)
            pct_width = 6
            stat_fmt = f"{{:<{label_width}}} {{:>{num_width}}} ({{:>{pct_width}.1f}}%)"
            report.append(f"Total translations: {total}")
            report.append(stat_fmt.format("Microsoft Terminology:", ms_count, ms_pct))
            report.append(stat_fmt.format("Google Translate:", gt_count, gt_pct))
        report.append("")
        
        # Add timing information if provided
        if duration_seconds is not None:
            minutes, seconds = divmod(duration_seconds, 60)
            report.append(f"Duration: {int(minutes)}m {seconds:.1f}s")
        
        if start_time is not None:
            report.append(f"Start time: {start_time}")
        
        if end_time is not None:
            report.append(f"End time: {end_time}")
        
        # Add extra info for detailed reports
        if detail_level == "detailed":
            report.append("\nBreakdown by Source:")
            report.append("  Microsoft Terminology translations are sourced from the official Business Central terminology database.")
            report.append("  Google Translate translations are used as fallback when no official terminology is available.")
            report.append("")
        
        # Join all lines with newlines
        return "\n".join(report)
    
    def format_detailed_console_report(self, detailed_collector, terminal_width=None):
        """
        Format detailed statistics from a DetailedStatisticsCollector for console output.
        
        Args:
            detailed_collector: The DetailedStatisticsCollector object to format.
            terminal_width (int, optional): Width of the terminal to format for.
            
        Returns:
            str: Formatted detailed statistics report for console output.
        """
        width = terminal_width or self._default_terminal_width
        
        # Start with the basic report
        report = [self.format_console_report(detailed_collector.statistics, 
                                           detail_level="detailed", 
                                           terminal_width=width)]
        
        # Add statistics by object type
        report.append("\nStatistics by Object Type")
        report.append("-" * width)
        
        # Get all object types from the collector
        object_types = []
        if hasattr(detailed_collector, "get_dimension_values"):
            object_types = detailed_collector.get_dimension_values("object_type")
        elif hasattr(detailed_collector, "_stats_by_object_type"):
            object_types = list(detailed_collector._stats_by_object_type.keys())
        
        for obj_type in sorted(object_types):
            if obj_type:  # Skip empty object types
                stats = detailed_collector.get_statistics_by_object_type(obj_type)
                report.append(f"\n{obj_type}:")
                report.append(f"  Total: {stats.total_count}")
                report.append(f"  Microsoft Terminology: {stats.microsoft_terminology_count} ({stats.microsoft_terminology_percentage:.1f}%)")
                report.append(f"  Google Translate: {stats.google_translate_count} ({stats.google_translate_percentage:.1f}%)")
        
        # Join all lines with newlines
        return "\n".join(report)
    
    def print_statistics(self, statistics, detail_level="summary", 
                        duration_seconds=None, start_time=None, end_time=None):
        """
        Print statistics to the console.
        
        Args:
            statistics: The TranslationStatistics object to print.
            detail_level (str): Level of detail to include ("summary" or "detailed").
            duration_seconds (float, optional): Duration of the translation process in seconds.
            start_time (str, optional): Start time of the translation process.
            end_time (str, optional): End time of the translation process.
        """
        # Format the report
        report = self.format_console_report(
            statistics, 
            detail_level=detail_level,
            duration_seconds=duration_seconds,
            start_time=start_time,
            end_time=end_time
        )
        
        # Print to console
        print(report)

    def export_statistics_csv(self, statistics, file_path, overwrite=True, detail_level="summary"):
        """
        Export statistics to a CSV file.

        Args:
            statistics: The TranslationStatistics object to export.
            file_path: Path to the CSV file to write.
            overwrite (bool): Whether to overwrite the file if it exists.
            detail_level (str): Level of detail (currently unused, for future extension).
        """
        mode = "w" if overwrite else "x"
        with open(file_path, mode, encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self._csv_headers())
            writer.writerow(self._csv_data_row(statistics))

    def _csv_headers(self):
        """
        Return the CSV headers for statistics export.
        """
        return [
            "Total translations",
            "Microsoft Terminology",
            "Google Translate"
        ]

    def _csv_data_row(self, statistics):
        """
        Return the main CSV data row for statistics export.
        """
        return [
            getattr(statistics, "total_count", 0),
            getattr(statistics, "microsoft_terminology_count", 0),
            getattr(statistics, "google_translate_count", 0)
        ]

    def export_statistics_json(self, statistics, file_path, pretty_print=False):
        """
        Export statistics to a JSON file, including nested structure and metadata.

        Args:
            statistics: The TranslationStatistics or similar object to export.
            file_path: Path to the JSON file to write.
            pretty_print (bool): Whether to pretty-print the JSON output.
        """
        import json
        def stats_to_dict(obj):
            import builtins
            # If it's a basic type, just return it
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            # If it's a dict, serialize keys/values
            if isinstance(obj, dict):
                return {k: stats_to_dict(v) for k, v in obj.items()}
            # If it's a list or tuple, serialize elements
            if isinstance(obj, (list, tuple)):
                return [stats_to_dict(i) for i in obj]
            # If it's a built-in type (not user-defined), return as-is
            if type(obj).__module__ == 'builtins':
                return obj
            # Handle objects with properties and attributes
            result = {}
            processed = set()
            for name in dir(obj):
                if name.startswith("_") or name in processed:
                    continue
                try:
                    value = getattr(obj, name)
                except Exception:
                    continue
                if callable(value):
                    continue
                if name in ("__class__", "__dict__", "__weakref__", "__module__", "__doc__"):
                    continue
                result[name] = stats_to_dict(value)
                processed.add(name)
            if not result and hasattr(obj, "__dict__"):
                for k, v in obj.__dict__.items():
                    if not k.startswith("_"):
                        result[k] = stats_to_dict(v)
            if not result:
                return obj
            return result
        metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "version": "1.0",
            "run_info": {
                "exported_by": "BCXLFTranslator",
                "export_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        }
        statistics_dict = stats_to_dict(statistics)
        data = {
            "metadata": metadata,
            "statistics": statistics_dict
        }
        kwargs = {"indent": 2} if pretty_print else {}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, **kwargs)
