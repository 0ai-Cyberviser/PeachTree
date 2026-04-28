"""Dataset visualization for charts and statistical analysis.

Provides visualization capabilities with chart generation,
statistical analysis, and export to multiple formats.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import statistics


class ChartType(Enum):
    """Chart types."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    HEATMAP = "heatmap"


class ExportFormat(Enum):
    """Export formats for visualizations."""
    JSON = "json"
    HTML = "html"
    SVG = "svg"
    CSV = "csv"
    MARKDOWN = "markdown"


@dataclass
class ChartData:
    """Chart data configuration."""
    chart_type: ChartType
    title: str
    x_label: str
    y_label: str
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chart_type": self.chart_type.value,
            "title": self.title,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "data": self.data,
            "metadata": self.metadata,
        }


@dataclass
class StatisticalSummary:
    """Statistical summary of data."""
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    quartiles: Tuple[float, float, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "mean": self.mean,
            "median": self.median,
            "std_dev": self.std_dev,
            "min": self.min_value,
            "max": self.max_value,
            "q1": self.quartiles[0],
            "q2": self.quartiles[1],
            "q3": self.quartiles[2],
        }


@dataclass
class Visualization:
    """Visualization result."""
    visualization_id: str
    chart: ChartData
    created_at: datetime
    export_formats: List[ExportFormat] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "visualization_id": self.visualization_id,
            "chart": self.chart.to_dict(),
            "created_at": self.created_at.isoformat(),
            "export_formats": [fmt.value for fmt in self.export_formats],
        }


class DatasetAnalyzer:
    """Analyze dataset for visualization."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def analyze_field(
        self,
        records: List[Dict[str, Any]],
        field_name: str,
    ) -> StatisticalSummary:
        """Analyze a numeric field."""
        values = [r.get(field_name, 0) for r in records if isinstance(r.get(field_name), (int, float))]
        
        if not values:
            return StatisticalSummary(
                count=0,
                mean=0.0,
                median=0.0,
                std_dev=0.0,
                min_value=0.0,
                max_value=0.0,
                quartiles=(0.0, 0.0, 0.0),
            )
        
        return StatisticalSummary(
            count=len(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            min_value=min(values),
            max_value=max(values),
            quartiles=self._calculate_quartiles(values),
        )
    
    def _calculate_quartiles(self, values: List[float]) -> Tuple[float, float, float]:
        """Calculate quartiles."""
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        q1 = sorted_values[n // 4] if n >= 4 else sorted_values[0]
        q2 = statistics.median(sorted_values)
        q3 = sorted_values[(3 * n) // 4] if n >= 4 else sorted_values[-1]
        
        return (q1, q2, q3)
    
    def count_values(
        self,
        records: List[Dict[str, Any]],
        field_name: str,
    ) -> Dict[Any, int]:
        """Count occurrences of values in field."""
        counts: Dict[Any, int] = {}
        
        for record in records:
            value = record.get(field_name)
            if value is not None:
                counts[value] = counts.get(value, 0) + 1
        
        return counts
    
    def calculate_distribution(
        self,
        records: List[Dict[str, Any]],
        field_name: str,
        bins: int = 10,
    ) -> List[Dict[str, Any]]:
        """Calculate distribution for histogram."""
        values = [r.get(field_name, 0) for r in records if isinstance(r.get(field_name), (int, float))]
        
        if not values:
            return []
        
        min_val = min(values)
        max_val = max(values)
        bin_width = (max_val - min_val) / bins if bins > 0 else 1
        
        distribution = []
        for i in range(bins):
            bin_min = min_val + i * bin_width
            bin_max = min_val + (i + 1) * bin_width
            count = sum(1 for v in values if bin_min <= v < bin_max)
            
            distribution.append({
                "bin": f"{bin_min:.2f}-{bin_max:.2f}",
                "count": count,
                "bin_min": bin_min,
                "bin_max": bin_max,
            })
        
        return distribution


class ChartGenerator:
    """Generate charts from data."""
    
    def __init__(self, analyzer: DatasetAnalyzer):
        """Initialize chart generator."""
        self.analyzer = analyzer
    
    def create_bar_chart(
        self,
        records: List[Dict[str, Any]],
        field_name: str,
        title: str,
    ) -> ChartData:
        """Create bar chart."""
        counts = self.analyzer.count_values(records, field_name)
        
        data = [
            {"label": str(k), "value": v}
            for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return ChartData(
            chart_type=ChartType.BAR,
            title=title,
            x_label=field_name,
            y_label="Count",
            data=data,
        )
    
    def create_pie_chart(
        self,
        records: List[Dict[str, Any]],
        field_name: str,
        title: str,
    ) -> ChartData:
        """Create pie chart."""
        counts = self.analyzer.count_values(records, field_name)
        total = sum(counts.values())
        
        data = [
            {
                "label": str(k),
                "value": v,
                "percentage": (v / total * 100) if total > 0 else 0,
            }
            for k, v in counts.items()
        ]
        
        return ChartData(
            chart_type=ChartType.PIE,
            title=title,
            x_label="",
            y_label="",
            data=data,
        )
    
    def create_line_chart(
        self,
        records: List[Dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str,
    ) -> ChartData:
        """Create line chart."""
        data = [
            {"x": r.get(x_field), "y": r.get(y_field)}
            for r in records
            if r.get(x_field) is not None and r.get(y_field) is not None
        ]
        
        # Sort by x value
        data.sort(key=lambda d: d["x"])
        
        return ChartData(
            chart_type=ChartType.LINE,
            title=title,
            x_label=x_field,
            y_label=y_field,
            data=data,
        )
    
    def create_histogram(
        self,
        records: List[Dict[str, Any]],
        field_name: str,
        title: str,
        bins: int = 10,
    ) -> ChartData:
        """Create histogram."""
        distribution = self.analyzer.calculate_distribution(records, field_name, bins)
        
        return ChartData(
            chart_type=ChartType.HISTOGRAM,
            title=title,
            x_label=field_name,
            y_label="Frequency",
            data=distribution,
        )
    
    def create_scatter_plot(
        self,
        records: List[Dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str,
    ) -> ChartData:
        """Create scatter plot."""
        data = [
            {"x": r.get(x_field), "y": r.get(y_field)}
            for r in records
            if isinstance(r.get(x_field), (int, float)) and isinstance(r.get(y_field), (int, float))
        ]
        
        return ChartData(
            chart_type=ChartType.SCATTER,
            title=title,
            x_label=x_field,
            y_label=y_field,
            data=data,
        )


class VisualizationExporter:
    """Export visualizations to different formats."""
    
    def __init__(self):
        """Initialize exporter."""
        pass
    
    def export_json(self, chart: ChartData, output_path: Path) -> None:
        """Export chart to JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(chart.to_dict(), indent=2))
    
    def export_html(self, chart: ChartData, output_path: Path) -> None:
        """Export chart to HTML."""
        html = self._generate_html(chart)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
    
    def export_markdown(self, chart: ChartData, output_path: Path) -> None:
        """Export chart to Markdown."""
        md = self._generate_markdown(chart)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md)
    
    def export_csv(self, chart: ChartData, output_path: Path) -> None:
        """Export chart data to CSV."""
        if not chart.data:
            return
        
        # Get all keys from first row
        keys = list(chart.data[0].keys())
        
        lines = [",".join(keys)]
        for row in chart.data:
            values = [str(row.get(k, "")) for k in keys]
            lines.append(",".join(values))
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines))
    
    def _generate_html(self, chart: ChartData) -> str:
        """Generate HTML for chart."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{chart.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .chart-container {{ margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>{chart.title}</h1>
    <div class="chart-container">
        <p><strong>X-Axis:</strong> {chart.x_label}</p>
        <p><strong>Y-Axis:</strong> {chart.y_label}</p>
        <p><strong>Type:</strong> {chart.chart_type.value}</p>
        
        <table>
            <thead>
                <tr>
"""
        
        if chart.data:
            keys = list(chart.data[0].keys())
            for key in keys:
                html += f"                    <th>{key}</th>\n"
            html += "                </tr>\n            </thead>\n            <tbody>\n"
            
            for row in chart.data:
                html += "                <tr>\n"
                for key in keys:
                    html += f"                    <td>{row.get(key, '')}</td>\n"
                html += "                </tr>\n"
        
        html += """            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_markdown(self, chart: ChartData) -> str:
        """Generate Markdown for chart."""
        md = f"# {chart.title}\n\n"
        md += f"**Type:** {chart.chart_type.value}\n\n"
        md += f"**X-Axis:** {chart.x_label}\n\n"
        md += f"**Y-Axis:** {chart.y_label}\n\n"
        md += "## Data\n\n"
        
        if chart.data:
            keys = list(chart.data[0].keys())
            
            # Header
            md += "| " + " | ".join(keys) + " |\n"
            md += "| " + " | ".join(["---"] * len(keys)) + " |\n"
            
            # Rows
            for row in chart.data:
                values = [str(row.get(k, "")) for k in keys]
                md += "| " + " | ".join(values) + " |\n"
        
        return md


class DatasetVisualizer:
    """Create visualizations for datasets."""
    
    def __init__(self):
        """Initialize visualizer."""
        self.analyzer = DatasetAnalyzer()
        self.chart_generator = ChartGenerator(self.analyzer)
        self.exporter = VisualizationExporter()
        self.visualizations: List[Visualization] = []
    
    def visualize_dataset(
        self,
        dataset_path: Path,
        chart_type: ChartType,
        field_name: str,
        title: Optional[str] = None,
    ) -> Visualization:
        """Create visualization for dataset."""
        # Read dataset
        records = []
        if dataset_path.exists():
            content = dataset_path.read_text()
            for line in content.strip().split("\n"):
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # Generate chart
        title = title or f"{chart_type.value.title()} Chart: {field_name}"
        
        if chart_type == ChartType.BAR:
            chart = self.chart_generator.create_bar_chart(records, field_name, title)
        elif chart_type == ChartType.PIE:
            chart = self.chart_generator.create_pie_chart(records, field_name, title)
        elif chart_type == ChartType.HISTOGRAM:
            chart = self.chart_generator.create_histogram(records, field_name, title)
        else:
            chart = ChartData(
                chart_type=chart_type,
                title=title,
                x_label=field_name,
                y_label="Value",
                data=[],
            )
        
        visualization = Visualization(
            visualization_id=f"vis_{len(self.visualizations)}",
            chart=chart,
            created_at=datetime.now(),
        )
        
        self.visualizations.append(visualization)
        return visualization
    
    def export_visualization(
        self,
        visualization: Visualization,
        output_path: Path,
        export_format: ExportFormat,
    ) -> None:
        """Export visualization."""
        if export_format == ExportFormat.JSON:
            self.exporter.export_json(visualization.chart, output_path)
        elif export_format == ExportFormat.HTML:
            self.exporter.export_html(visualization.chart, output_path)
        elif export_format == ExportFormat.MARKDOWN:
            self.exporter.export_markdown(visualization.chart, output_path)
        elif export_format == ExportFormat.CSV:
            self.exporter.export_csv(visualization.chart, output_path)
        
        if export_format not in visualization.export_formats:
            visualization.export_formats.append(export_format)
    
    def get_statistics(
        self,
        dataset_path: Path,
        field_name: str,
    ) -> StatisticalSummary:
        """Get statistical summary for field."""
        records = []
        if dataset_path.exists():
            content = dataset_path.read_text()
            for line in content.strip().split("\n"):
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        return self.analyzer.analyze_field(records, field_name)
    
    def create_dashboard(
        self,
        dataset_path: Path,
        fields: List[str],
        output_dir: Path,
    ) -> List[Path]:
        """Create visualization dashboard."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        for field in fields:
            # Create bar chart
            viz = self.visualize_dataset(
                dataset_path,
                ChartType.BAR,
                field,
                title=f"Distribution of {field}",
            )
            
            # Export to HTML
            html_path = output_dir / f"{field}_bar.html"
            self.export_visualization(viz, html_path, ExportFormat.HTML)
            generated_files.append(html_path)
            
            # Export statistics
            stats = self.get_statistics(dataset_path, field)
            stats_path = output_dir / f"{field}_stats.json"
            stats_path.write_text(json.dumps(stats.to_dict(), indent=2))
            generated_files.append(stats_path)
        
        # Create index page
        index_path = output_dir / "index.html"
        index_html = self._create_index_page(fields)
        index_path.write_text(index_html)
        generated_files.append(index_path)
        
        return generated_files
    
    def _create_index_page(self, fields: List[str]) -> str:
        """Create dashboard index page."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Dataset Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .field-list { list-style-type: none; padding: 0; }
        .field-list li { margin: 10px 0; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Dataset Visualization Dashboard</h1>
    <ul class="field-list">
"""
        
        for field in fields:
            html += f'        <li><a href="{field}_bar.html">{field} Distribution</a> | <a href="{field}_stats.json">Statistics</a></li>\n'
        
        html += """    </ul>
</body>
</html>
"""
        return html
