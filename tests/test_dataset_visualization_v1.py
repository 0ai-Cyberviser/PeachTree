"""Tests for dataset_visualization module."""
import json
import pytest
from pathlib import Path
from peachtree.dataset_visualization import (
    DatasetVisualizer,
    ChartGenerator,
    DatasetAnalyzer,
    VisualizationExporter,
    ChartData,
    StatisticalSummary,
    Visualization,
    ChartType,
    ExportFormat,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create sample dataset."""
    dataset_path = tmp_path / "dataset.jsonl"
    data = [
        {"id": 1, "category": "A", "value": 10},
        {"id": 2, "category": "B", "value": 20},
        {"id": 3, "category": "A", "value": 15},
        {"id": 4, "category": "C", "value": 30},
        {"id": 5, "category": "B", "value": 25},
    ]
    dataset_path.write_text("\n".join(json.dumps(d) for d in data))
    return dataset_path


@pytest.fixture
def analyzer():
    """Create dataset analyzer."""
    return DatasetAnalyzer()


@pytest.fixture
def chart_generator(analyzer):
    """Create chart generator."""
    return ChartGenerator(analyzer)


@pytest.fixture
def exporter():
    """Create visualization exporter."""
    return VisualizationExporter()


@pytest.fixture
def visualizer():
    """Create dataset visualizer."""
    return DatasetVisualizer()


def test_dataset_analyzer_analyze_field(analyzer):
    """Test analyzing numeric field."""
    records = [
        {"value": 10},
        {"value": 20},
        {"value": 30},
        {"value": 40},
    ]
    
    stats = analyzer.analyze_field(records, "value")
    
    assert stats.count == 4
    assert stats.mean == 25.0
    assert stats.median == 25.0
    assert stats.min_value == 10
    assert stats.max_value == 40


def test_dataset_analyzer_count_values(analyzer):
    """Test counting values."""
    records = [
        {"category": "A"},
        {"category": "B"},
        {"category": "A"},
        {"category": "C"},
    ]
    
    counts = analyzer.count_values(records, "category")
    
    assert counts["A"] == 2
    assert counts["B"] == 1
    assert counts["C"] == 1


def test_dataset_analyzer_calculate_distribution(analyzer):
    """Test calculating distribution."""
    records = [{"value": i} for i in range(100)]
    
    distribution = analyzer.calculate_distribution(records, "value", bins=10)
    
    assert len(distribution) == 10
    assert all("bin" in d for d in distribution)
    assert all("count" in d for d in distribution)


def test_statistical_summary_to_dict():
    """Test statistical summary serialization."""
    summary = StatisticalSummary(
        count=10,
        mean=20.0,
        median=18.0,
        std_dev=5.0,
        min_value=10.0,
        max_value=30.0,
        quartiles=(15.0, 18.0, 25.0),
    )
    
    data = summary.to_dict()
    assert data["count"] == 10
    assert data["mean"] == 20.0
    assert data["q1"] == 15.0


def test_chart_data_to_dict():
    """Test chart data serialization."""
    chart = ChartData(
        chart_type=ChartType.BAR,
        title="Test Chart",
        x_label="X",
        y_label="Y",
        data=[{"x": 1, "y": 2}],
    )
    
    data = chart.to_dict()
    assert data["chart_type"] == "bar"
    assert data["title"] == "Test Chart"


def test_visualization_to_dict():
    """Test visualization serialization."""
    from datetime import datetime
    
    chart = ChartData(
        chart_type=ChartType.PIE,
        title="Test",
        x_label="",
        y_label="",
        data=[],
    )
    
    viz = Visualization(
        visualization_id="v1",
        chart=chart,
        created_at=datetime.now(),
    )
    
    data = viz.to_dict()
    assert data["visualization_id"] == "v1"
    assert "chart" in data


def test_chart_generator_create_bar_chart(chart_generator):
    """Test creating bar chart."""
    records = [
        {"category": "A"},
        {"category": "B"},
        {"category": "A"},
    ]
    
    chart = chart_generator.create_bar_chart(records, "category", "Category Distribution")
    
    assert chart.chart_type == ChartType.BAR
    assert chart.title == "Category Distribution"
    assert len(chart.data) == 2


def test_chart_generator_create_pie_chart(chart_generator):
    """Test creating pie chart."""
    records = [
        {"category": "A"},
        {"category": "B"},
        {"category": "A"},
    ]
    
    chart = chart_generator.create_pie_chart(records, "category", "Category Breakdown")
    
    assert chart.chart_type == ChartType.PIE
    assert chart.title == "Category Breakdown"
    assert len(chart.data) == 2
    assert all("percentage" in d for d in chart.data)


def test_chart_generator_create_line_chart(chart_generator):
    """Test creating line chart."""
    records = [
        {"x": 1, "y": 10},
        {"x": 2, "y": 20},
        {"x": 3, "y": 15},
    ]
    
    chart = chart_generator.create_line_chart(records, "x", "y", "Trend")
    
    assert chart.chart_type == ChartType.LINE
    assert len(chart.data) == 3
    assert chart.data[0]["x"] == 1


def test_chart_generator_create_histogram(chart_generator):
    """Test creating histogram."""
    records = [{"value": i} for i in range(100)]
    
    chart = chart_generator.create_histogram(records, "value", "Value Distribution", bins=10)
    
    assert chart.chart_type == ChartType.HISTOGRAM
    assert len(chart.data) == 10


def test_chart_generator_create_scatter_plot(chart_generator):
    """Test creating scatter plot."""
    records = [
        {"x": 1, "y": 10},
        {"x": 2, "y": 20},
        {"x": 3, "y": 15},
    ]
    
    chart = chart_generator.create_scatter_plot(records, "x", "y", "Scatter")
    
    assert chart.chart_type == ChartType.SCATTER
    assert len(chart.data) == 3


def test_exporter_export_json(exporter, tmp_path):
    """Test JSON export."""
    chart = ChartData(
        chart_type=ChartType.BAR,
        title="Test",
        x_label="X",
        y_label="Y",
        data=[{"x": 1, "y": 2}],
    )
    
    output_path = tmp_path / "chart.json"
    exporter.export_json(chart, output_path)
    
    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert data["title"] == "Test"


def test_exporter_export_html(exporter, tmp_path):
    """Test HTML export."""
    chart = ChartData(
        chart_type=ChartType.BAR,
        title="Test Chart",
        x_label="X",
        y_label="Y",
        data=[{"label": "A", "value": 10}],
    )
    
    output_path = tmp_path / "chart.html"
    exporter.export_html(chart, output_path)
    
    assert output_path.exists()
    html = output_path.read_text()
    assert "Test Chart" in html
    assert "<table>" in html


def test_exporter_export_markdown(exporter, tmp_path):
    """Test Markdown export."""
    chart = ChartData(
        chart_type=ChartType.PIE,
        title="Test Chart",
        x_label="X",
        y_label="Y",
        data=[{"label": "A", "value": 10}],
    )
    
    output_path = tmp_path / "chart.md"
    exporter.export_markdown(chart, output_path)
    
    assert output_path.exists()
    md = output_path.read_text()
    assert "# Test Chart" in md
    assert "|" in md


def test_exporter_export_csv(exporter, tmp_path):
    """Test CSV export."""
    chart = ChartData(
        chart_type=ChartType.BAR,
        title="Test",
        x_label="X",
        y_label="Y",
        data=[
            {"label": "A", "value": 10},
            {"label": "B", "value": 20},
        ],
    )
    
    output_path = tmp_path / "chart.csv"
    exporter.export_csv(chart, output_path)
    
    assert output_path.exists()
    csv = output_path.read_text()
    assert "label,value" in csv
    assert "A,10" in csv


def test_visualizer_visualize_dataset_bar(visualizer, sample_dataset):
    """Test creating bar chart from dataset."""
    viz = visualizer.visualize_dataset(
        sample_dataset,
        ChartType.BAR,
        "category",
    )
    
    assert viz.chart.chart_type == ChartType.BAR
    assert len(visualizer.visualizations) == 1


def test_visualizer_visualize_dataset_pie(visualizer, sample_dataset):
    """Test creating pie chart from dataset."""
    viz = visualizer.visualize_dataset(
        sample_dataset,
        ChartType.PIE,
        "category",
        title="Category Distribution",
    )
    
    assert viz.chart.chart_type == ChartType.PIE
    assert viz.chart.title == "Category Distribution"


def test_visualizer_visualize_dataset_histogram(visualizer, sample_dataset):
    """Test creating histogram from dataset."""
    viz = visualizer.visualize_dataset(
        sample_dataset,
        ChartType.HISTOGRAM,
        "value",
    )
    
    assert viz.chart.chart_type == ChartType.HISTOGRAM


def test_visualizer_export_visualization(visualizer, sample_dataset, tmp_path):
    """Test exporting visualization."""
    viz = visualizer.visualize_dataset(
        sample_dataset,
        ChartType.BAR,
        "category",
    )
    
    output_path = tmp_path / "viz.json"
    visualizer.export_visualization(viz, output_path, ExportFormat.JSON)
    
    assert output_path.exists()
    assert ExportFormat.JSON in viz.export_formats


def test_visualizer_get_statistics(visualizer, sample_dataset):
    """Test getting statistics."""
    stats = visualizer.get_statistics(sample_dataset, "value")
    
    assert stats.count == 5
    assert stats.mean == 20.0


def test_visualizer_create_dashboard(visualizer, sample_dataset, tmp_path):
    """Test creating dashboard."""
    output_dir = tmp_path / "dashboard"
    
    files = visualizer.create_dashboard(
        sample_dataset,
        ["category", "value"],
        output_dir,
    )
    
    assert len(files) > 0
    assert (output_dir / "index.html").exists()


def test_empty_dataset(visualizer, tmp_path):
    """Test visualizing empty dataset."""
    empty_path = tmp_path / "empty.jsonl"
    empty_path.write_text("")
    
    viz = visualizer.visualize_dataset(
        empty_path,
        ChartType.BAR,
        "field",
    )
    
    assert len(viz.chart.data) == 0


def test_analyzer_empty_values(analyzer):
    """Test analyzing with no valid values."""
    records = [{"other": "data"}]
    
    stats = analyzer.analyze_field(records, "missing_field")
    
    assert stats.count == 0
    assert stats.mean == 0.0


def test_analyzer_quartiles(analyzer):
    """Test quartile calculation."""
    records = [{"value": i} for i in range(1, 101)]
    
    stats = analyzer.analyze_field(records, "value")
    
    assert stats.quartiles[0] < stats.quartiles[1] < stats.quartiles[2]


def test_chart_with_metadata():
    """Test chart with custom metadata."""
    chart = ChartData(
        chart_type=ChartType.SCATTER,
        title="Test",
        x_label="X",
        y_label="Y",
        data=[],
        metadata={"source": "test", "version": "1.0"},
    )
    
    data = chart.to_dict()
    assert data["metadata"]["source"] == "test"


def test_multiple_visualizations(visualizer, sample_dataset):
    """Test creating multiple visualizations."""
    viz1 = visualizer.visualize_dataset(sample_dataset, ChartType.BAR, "category")
    viz2 = visualizer.visualize_dataset(sample_dataset, ChartType.PIE, "category")
    
    assert len(visualizer.visualizations) == 2
    assert viz1.visualization_id != viz2.visualization_id


def test_export_multiple_formats(visualizer, sample_dataset, tmp_path):
    """Test exporting in multiple formats."""
    viz = visualizer.visualize_dataset(sample_dataset, ChartType.BAR, "category")
    
    visualizer.export_visualization(viz, tmp_path / "viz.json", ExportFormat.JSON)
    visualizer.export_visualization(viz, tmp_path / "viz.html", ExportFormat.HTML)
    visualizer.export_visualization(viz, tmp_path / "viz.md", ExportFormat.MARKDOWN)
    
    assert len(viz.export_formats) == 3
