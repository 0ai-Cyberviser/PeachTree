"""
Tests for lineage_visualizer module
"""
from pathlib import Path
import pytest
import json
from peachtree.lineage_visualizer import (
    LineageVisualizer,
    LineageGraph,
    LineageNode,
    LineageEdge,
)


def test_lineage_node_creation():
    """Test LineageNode dataclass"""
    node = LineageNode(
        node_id="dataset_1",
        node_type="dataset",
        label="Test Dataset",
        metadata={"records": 100},
    )
    
    assert node.node_id == "dataset_1"
    assert node.node_type == "dataset"
    assert node.metadata["records"] == 100
    
    data = node.to_dict()
    assert data["label"] == "Test Dataset"


def test_lineage_edge_creation():
    """Test LineageEdge dataclass"""
    edge = LineageEdge(
        source="dataset_1",
        target="dataset_2",
        edge_type="derived_from",
        label="optimized",
    )
    
    assert edge.source == "dataset_1"
    assert edge.target == "dataset_2"
    assert edge.edge_type == "derived_from"
    
    data = edge.to_dict()
    assert data["label"] == "optimized"


def test_lineage_graph_initialization():
    """Test LineageGraph initialization"""
    graph = LineageGraph()
    
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0
    assert isinstance(graph.metadata, dict)


def test_lineage_graph_add_node():
    """Test adding nodes to graph"""
    graph = LineageGraph()
    node = LineageNode("node1", "dataset", "Dataset 1")
    
    graph.add_node(node)
    
    assert len(graph.nodes) == 1
    assert graph.nodes[0].node_id == "node1"


def test_lineage_graph_add_edge():
    """Test adding edges to graph"""
    graph = LineageGraph()
    edge = LineageEdge("node1", "node2", "depends_on")
    
    graph.add_edge(edge)
    
    assert len(graph.edges) == 1
    assert graph.edges[0].source == "node1"


def test_lineage_graph_to_dict():
    """Test graph serialization to dict"""
    graph = LineageGraph()
    graph.add_node(LineageNode("n1", "dataset", "Dataset"))
    graph.add_edge(LineageEdge("n1", "n2", "depends_on"))
    
    data = graph.to_dict()
    
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 1
    assert len(data["edges"]) == 1


def test_lineage_graph_to_json():
    """Test graph JSON serialization"""
    graph = LineageGraph()
    graph.add_node(LineageNode("n1", "dataset", "Dataset"))
    
    json_str = graph.to_json()
    parsed = json.loads(json_str)
    
    assert "nodes" in parsed
    assert parsed["nodes"][0]["node_id"] == "n1"


def test_visualizer_initialization():
    """Test LineageVisualizer initialization"""
    viz = LineageVisualizer()
    
    assert isinstance(viz.graph, LineageGraph)
    assert len(viz.graph.nodes) == 0


def test_add_dataset_node():
    """Test adding dataset node"""
    viz = LineageVisualizer()
    viz.add_dataset_node("data/test.jsonl", record_count=100, quality_score=85.0)
    
    assert len(viz.graph.nodes) == 1
    node = viz.graph.nodes[0]
    assert node.node_type == "dataset"
    assert node.metadata["record_count"] == 100
    assert node.metadata["quality_score"] == 85.0


def test_add_repository_node():
    """Test adding repository node"""
    viz = LineageVisualizer()
    viz.add_repository_node("user/repo")
    
    assert len(viz.graph.nodes) == 1
    node = viz.graph.nodes[0]
    assert node.node_type == "repo"
    assert node.label == "user/repo"


def test_add_operation_node():
    """Test adding operation node"""
    viz = LineageVisualizer()
    viz.add_operation_node("merge_op", "merge")
    
    assert len(viz.graph.nodes) == 1
    node = viz.graph.nodes[0]
    assert node.node_type == "operation"
    assert node.metadata["operation_type"] == "merge"


def test_add_dependency():
    """Test adding dependency edge"""
    viz = LineageVisualizer()
    viz.add_dataset_node("dataset1.jsonl")
    viz.add_dataset_node("dataset2.jsonl")
    viz.add_dependency("dataset1.jsonl", "dataset2.jsonl")
    
    assert len(viz.graph.edges) == 1
    edge = viz.graph.edges[0]
    assert edge.edge_type == "derived_from"


def test_to_dot():
    """Test DOT format generation"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl", record_count=100)
    viz.add_repository_node("user/repo")
    viz.add_dependency("user/repo", "test.jsonl")
    
    dot = viz.to_dot()
    
    assert "digraph DatasetLineage" in dot
    assert "dataset_test" in dot
    assert "repo_user_repo" in dot
    assert "->" in dot


def test_to_mermaid():
    """Test Mermaid format generation"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl", record_count=100)
    viz.add_repository_node("user/repo")
    
    mermaid = viz.to_mermaid()
    
    assert "graph LR" in mermaid
    assert "dataset_test" in mermaid
    assert "repo_user_repo" in mermaid


def test_to_ascii():
    """Test ASCII format generation"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl")
    viz.add_repository_node("user/repo")
    viz.add_dependency("user/repo", "test.jsonl")
    
    ascii_art = viz.to_ascii()
    
    assert "Dataset Lineage Graph" in ascii_art
    assert "NODES:" in ascii_art
    assert "DEPENDENCIES:" in ascii_art
    assert "-->" in ascii_art


def test_build_from_manifest(tmp_path):
    """Test building graph from manifest"""
    manifest = tmp_path / "manifest.json"
    manifest_data = {
        "dataset_name": "test_dataset",
        "record_count": 150,
        "source_documents": [
            {"source_repo": "user/repo1", "source_path": "file1.txt"},
            {"source_repo": "user/repo2", "source_path": "file2.txt"},
        ],
    }
    manifest.write_text(json.dumps(manifest_data, indent=2))
    
    viz = LineageVisualizer()
    graph = viz.build_from_manifest(manifest)
    
    assert len(graph.nodes) >= 3  # dataset + 2 repos
    assert len(graph.edges) >= 2  # 2 contributions


def test_build_from_catalog(tmp_path):
    """Test building graph from catalog"""
    catalog = tmp_path / "catalog.json"
    catalog_data = {
        "entries": {
            "dataset1": {
                "dataset_path": "data/dataset1.jsonl",
                "record_count": 100,
                "quality_score": 85.0,
                "dependencies": [],
            },
            "dataset2": {
                "dataset_path": "data/dataset2.jsonl",
                "record_count": 50,
                "quality_score": 90.0,
                "dependencies": ["data/dataset1.jsonl"],
            },
        },
    }
    catalog.write_text(json.dumps(catalog_data, indent=2))
    
    viz = LineageVisualizer()
    graph = viz.build_from_catalog(catalog)
    
    assert len(graph.nodes) == 2  # 2 datasets
    assert len(graph.edges) == 1  # 1 dependency


def test_save_dot(tmp_path):
    """Test saving DOT format to file"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl")
    
    output = tmp_path / "lineage.dot"
    viz.save_dot(output)
    
    assert output.exists()
    content = output.read_text()
    assert "digraph DatasetLineage" in content


def test_save_mermaid(tmp_path):
    """Test saving Mermaid format to file"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl")
    
    output = tmp_path / "lineage.mmd"
    viz.save_mermaid(output)
    
    assert output.exists()
    content = output.read_text()
    assert "graph LR" in content


def test_save_ascii(tmp_path):
    """Test saving ASCII format to file"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl")
    
    output = tmp_path / "lineage.txt"
    viz.save_ascii(output)
    
    assert output.exists()
    content = output.read_text()
    assert "Dataset Lineage Graph" in content


def test_generate_markdown_with_mermaid():
    """Test generating markdown with embedded Mermaid"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl")
    viz.add_repository_node("user/repo")
    
    markdown = viz.generate_markdown_with_mermaid(
        title="Test Lineage",
        description="Test description",
    )
    
    assert "# Test Lineage" in markdown
    assert "Test description" in markdown
    assert "```mermaid" in markdown
    assert "## Statistics" in markdown


def test_save_markdown_with_mermaid(tmp_path):
    """Test saving markdown with Mermaid to file"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl")
    
    output = tmp_path / "lineage.md"
    viz.save_markdown_with_mermaid(output, title="Dataset Lineage")
    
    assert output.exists()
    content = output.read_text()
    assert "# Dataset Lineage" in content
    assert "```mermaid" in content


def test_creates_parent_directories(tmp_path):
    """Test that save methods create parent directories"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl")
    
    output = tmp_path / "nested" / "dir" / "lineage.dot"
    viz.save_dot(output)
    
    assert output.exists()
    assert output.parent.exists()


def test_complex_graph_structure(tmp_path):
    """Test building complex graph with multiple nodes and edges"""
    viz = LineageVisualizer()
    
    # Add multiple datasets
    viz.add_dataset_node("raw.jsonl", record_count=1000)
    viz.add_dataset_node("filtered.jsonl", record_count=800)
    viz.add_dataset_node("final.jsonl", record_count=600)
    
    # Add repositories
    viz.add_repository_node("owner/repo1")
    viz.add_repository_node("owner/repo2")
    
    # Add operations
    viz.add_operation_node("filter_op", "filter")
    viz.add_operation_node("merge_op", "merge")
    
    # Add dependencies
    viz.add_dependency("raw.jsonl", "filtered.jsonl")
    viz.add_dependency("filtered.jsonl", "final.jsonl")
    
    assert len(viz.graph.nodes) == 7
    assert len(viz.graph.edges) == 2
    
    # Generate all formats without error
    dot = viz.to_dot()
    mermaid = viz.to_mermaid()
    ascii_art = viz.to_ascii()
    
    assert len(dot) > 0
    assert len(mermaid) > 0
    assert len(ascii_art) > 0


def test_node_shapes_in_dot():
    """Test that different node types have different shapes in DOT"""
    viz = LineageVisualizer()
    viz.add_dataset_node("test.jsonl")
    viz.add_repository_node("user/repo")
    
    dot = viz.to_dot()
    
    assert "cylinder" in dot  # Dataset shape
    assert "box" in dot  # Other shapes


def test_edge_labels():
    """Test that edge labels appear in output"""
    viz = LineageVisualizer()
    viz.add_dataset_node("source.jsonl")
    viz.add_dataset_node("target.jsonl")
    
    edge = LineageEdge("dataset_source", "dataset_target", "derived_from", label="optimized")
    viz.graph.add_edge(edge)
    
    dot = viz.to_dot()
    mermaid = viz.to_mermaid()
    
    assert "optimized" in dot
    assert "optimized" in mermaid


def test_empty_graph():
    """Test handling empty graph"""
    viz = LineageVisualizer()
    
    dot = viz.to_dot()
    mermaid = viz.to_mermaid()
    ascii_art = viz.to_ascii()
    
    assert "digraph DatasetLineage" in dot
    assert "graph LR" in mermaid
    assert "Dataset Lineage Graph" in ascii_art
