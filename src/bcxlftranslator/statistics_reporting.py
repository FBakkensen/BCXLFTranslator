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
        gt_count = statistics.google_translate_count
        gt_pct = statistics.google_translate_percentage

        if detail_level == "summary":
            report.append(f"Total translations: {total}")
            report.append(f"Google Translate: {gt_count} ({gt_pct:.1f}%)")
        else:
            # Formatting for alignment in detailed view
            label_width = 22
            num_width = max(len(str(gt_count)), 3)
            pct_width = 6
            stat_fmt = f"{{:<{label_width}}} {{:>{num_width}}} ({{:>{pct_width}.1f}}%)"
            report.append(f"Total translations: {total}")
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
            report.append("\nTranslation Source:")
            report.append("  All translations are performed using Google Translate.")
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
            "Google Translate"
        ]

    def _csv_data_row(self, statistics):
        """
        Return the main CSV data row for statistics export.
        """
        return [
            getattr(statistics, "total_count", 0),
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

    def export_statistics_html(self, statistics, file_path):
        """
        Export statistics to a self-contained HTML file with basic visualizations.
        Args:
            statistics: The TranslationStatistics object to export.
            file_path: Path to the HTML file to write.
        """
        gt_count = getattr(statistics, "google_translate_count", 0)
        total = getattr(statistics, "total_count", gt_count)
        gt_pct = getattr(statistics, "google_translate_percentage", 100.0)
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Translation Statistics Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2em; }}
        h1 {{ text-align: center; }}
        table {{ border-collapse: collapse; margin: 2em auto; min-width: 350px; }}
        th, td {{ border: 1px solid #ccc; padding: 0.5em 1em; text-align: right; }}
        th {{ background: #f0f0f0; }}
        .center {{ text-align: center; }}
        .chart-container {{ width: 400px; margin: 2em auto; }}
    </style>
</head>
<body>
    <h1>Translation Statistics Report</h1>
    <div class="center">
        <table>
            <tr><th>Source</th><th>Count</th><th>Percentage</th></tr>
            <tr><td>Google Translate</td><td>{gt_count}</td><td>{gt_pct:.1f}%</td></tr>
            <tr><th>Total</th><th colspan="2">{total}</th></tr>
        </table>
    </div>
    <div class="chart-container">
        <canvas id="chart" width="400" height="300"></canvas>
    </div>
    <script>
    // Chart visualization (simple pie chart)
    const ctx = document.getElementById('chart').getContext('2d');
    const data = [{gt_count}];
    const colors = ["#34A853"];
    const labels = ["Google Translate"];
    const total = data.reduce((a, b) => a + b, 0);
    let start = 0;
    for (let i = 0; i < data.length; i++) {{
        const val = data[i];
        const angle = (val / total) * 2 * Math.PI;
        ctx.beginPath();
        ctx.moveTo(200, 150);
        ctx.arc(200, 150, 100, start, start + angle);
        ctx.closePath();
        ctx.fillStyle = colors[i];
        ctx.fill();
        start += angle;
    }}
    // Add legend
    ctx.font = "16px Arial";
    ctx.fillStyle = "#000";
    ctx.fillText(labels[0] + `: {gt_count} ({gt_pct:.1f}%)`, 10, 280);
    </script>
</body>
</html>
'''
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

    def generate_report(self, statistics, format=None, output_path=None, config=None, session_info=None, batch_outputs=None):
        """
        Unified API for generating reports in any format.
        Args:
            statistics: The TranslationStatistics object.
            format: The format to generate (console, csv, json, html). Optional if output_path is given.
            output_path: File path to write the report. If omitted, returns report as string (for console).
            config: Dict of configuration options (detail_level, pretty, etc.).
            session_info: Dict of session/timestamp info to include in reports.
            batch_outputs: Dict mapping format name to output_path for batch generation.
        Returns:
            The report string (for console), or None for file outputs.
        """
        import os
        from datetime import datetime, timezone
        # Handle batch generation
        if batch_outputs:
            results = {}
            for fmt, path in batch_outputs.items():
                results[fmt] = self.generate_report(
                    statistics, format=fmt, output_path=path, config=config, session_info=session_info)
            return results
        # Auto-detect format from output_path
        if not format and output_path:
            ext = os.path.splitext(str(output_path))[1].lower()
            if ext == ".csv":
                format = "csv"
            elif ext == ".json":
                format = "json"
            elif ext == ".html":
                format = "html"
            else:
                format = "console"
        format = (format or "console").lower()
        detail_level = (config or {}).get("detail_level", "summary")
        pretty = (config or {}).get("pretty", False)
        # Timestamp/session info
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        session = session_info or {}
        # Console
        if format == "console":
            report = self.format_console_report(
                statistics, detail_level=detail_level)
            # Add timestamp/session info
            report += f"\nTimestamp: {now}"
            if session:
                for k, v in session.items():
                    report += f"\nSession {k}: {v}"
            return report
        # CSV
        elif format == "csv":
            # Not supporting session info/timestamp in CSV for now
            self.export_statistics_csv(
                statistics, output_path, overwrite=True, detail_level=detail_level)
            return None
        # JSON
        elif format == "json":
            # Wrap stats and session info in metadata
            def stats_to_dict(obj):
                if hasattr(obj, "__dict__"):
                    return {k: stats_to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
                elif isinstance(obj, dict):
                    return {k: stats_to_dict(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [stats_to_dict(x) for x in obj]
                else:
                    return obj
            metadata = {
                "timestamp": now,
                "session": session,
                "version": "1.0"
            }
            data = {
                "metadata": metadata,
                "statistics": stats_to_dict(statistics)
            }
            kwargs = {"indent": 2} if pretty else {}
            with open(output_path, "w", encoding="utf-8") as f:
                import json
                json.dump(data, f, **kwargs)
            return None
        # HTML
        elif format == "html":
            # Generate HTML, inject session/timestamp if possible
            gt_count = getattr(statistics, "google_translate_count", 0)
            total = getattr(statistics, "total_count", gt_count)
            gt_pct = getattr(statistics, "google_translate_percentage", 100.0)
            info_html = f"<p>Timestamp: {now}</p>"
            if session:
                info_html += "<ul>" + "".join(f"<li>{k}: {v}</li>" for k, v in session.items()) + "</ul>"
            html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Translation Statistics Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2em; }}
        h1 {{ text-align: center; }}
        table {{ border-collapse: collapse; margin: 2em auto; min-width: 350px; }}
        th, td {{ border: 1px solid #ccc; padding: 0.5em 1em; text-align: right; }}
        th {{ background: #f0f0f0; }}
        .center {{ text-align: center; }}
        .chart-container {{ width: 400px; margin: 2em auto; }}
    </style>
</head>
<body>
    <h1>Translation Statistics Report</h1>
    {info_html}
    <div class="center">
        <table>
            <tr><th>Source</th><th>Count</th><th>Percentage</th></tr>
            <tr><td>Google Translate</td><td>{gt_count}</td><td>{gt_pct:.1f}%</td></tr>
            <tr><th>Total</th><th colspan="2">{total}</th></tr>
        </table>
    </div>
    <div class="chart-container">
        <canvas id="chart" width="400" height="300"></canvas>
    </div>
    <script>
    // Chart visualization (simple pie chart)
    const ctx = document.getElementById('chart').getContext('2d');
    const data = [{gt_count}];
    const colors = ["#34A853"];
    const labels = ["Google Translate"];
    const total = data.reduce((a, b) => a + b, 0);
    let start = 0;
    for (let i = 0; i < data.length; i++) {{
        const val = data[i];
        const angle = (val / total) * 2 * Math.PI;
        ctx.beginPath();
        ctx.moveTo(200, 150);
        ctx.arc(200, 150, 100, start, start + angle);
        ctx.closePath();
        ctx.fillStyle = colors[i];
        ctx.fill();
        start += angle;
    }}
    // Add legend
    ctx.font = "16px Arial";
    ctx.fillStyle = "#000";
    ctx.fillText(labels[0] + `: {gt_count} ({gt_pct:.1f}%)`, 10, 280);
    </script>
</body>
</html>
'''
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            return None
        else:
            raise ValueError(f"Unsupported report format: {format}")
