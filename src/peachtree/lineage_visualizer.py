"""
PeachTree Dataset Lineage Visualizer

Generate visual dependency graphs and lineage diagrams for datasets. Supports
DOT/Graphviz, Mermaid, and ASCII formats for documentation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass
class LineageNode:
    """Node in lineage graph"""
    node_id: str
    node_type: str  # dataset, repo, operation, policy
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "metadata": self.metadata,
        }


@dataclass
class LineageEdge:
    """Edge in lineage graph"""
    source: str
    target: str
    edge_type: str  # derived_from, depends_on, generated_by, validated_by
    label: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type,
            "label": self.label,
        }


@dataclass
class LineageGraph:
    """Complete lineage graph"""
    nodes: list[LineageNode] = field(default_factory=list)
    edges: list[LineageEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: LineageNode) -> None:
        """Add node to graph"""
        self.nodes.append(node)
    
    def add_edge(self, edge: LineageEdge) -> None:
        """Add edge to graph"""
        self.edges.append(edge)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class LineageVisualizer:
    """Generate visual lineage diagrams"""
    
    def __init__(self):
        """Initialize lineage visualizer"""
        self.graph = LineageGraph()
    
    def add_dataset_node(
        self,
        dataset_path: str,
        record_count: int | None = None,
        quality_score: float | None = None,
    ) -> None:
        """Add dataset node to graph"""
        node_id = f"dataset_{Path(dataset_path).stem}"
        label = Path(dataset_path).stem
        
        metadata = {}
        if record_count is not None:
            metadata["record_count"] = record_count
        if quality_score is not None:
            metadata["quality_score"] = quality_score
        
        self.graph.add_node(LineageNode(
            node_id=node_id,
            node_type="dataset",
            label=label,
            metadata=metadata,
        ))
    
    def add_repository_node(self, repo_name: str) -> None:
        """Add source repository node"""
        node_id = f"repo_{repo_name.replace('/', '_')}"
        
        self.graph.add_node(LineageNode(
            node_id=node_id,
            node_type="repo",
            label=repo_name,
        ))
    
    def add_operation_node(self, operation_name: str, operation_type: str) -> None:
        """Add operation node (merge, split, optimize, etc.)"""
        node_id = f"op_{operation_name}"
        
        self.graph.add_node(LineageNode(
            node_id=node_id,
            node_type="operation",
            label=operation_name,
            metadata={"operation_type": operation_type},
        ))
    
    def add_dependency(
        self,
        source_dataset: str,
        target_dataset: str,
        relationship: str = "derived_from",
    ) -> None:
        """Add dependency between datasets"""
        source_id = f"dataset_{Path(source_dataset).stem}"
        target_id = f"dataset_{Path(target_dataset).stem}"
        
        self.graph.add_edge(LineageEdge(
            source=source_id,
            target=target_id,
            edge_type=relationship,
        ))
    
    def to_dot(self) -> str:
        """Generate DOT/Graphviz format"""
        lines = [
            "digraph DatasetLineage {",
            "  rankdir=LR;",
            "  node [shape=box, style=rounded];",
            "",
        ]
        
        # Nodes
        for node in self.graph.nodes:
            shape = "cylinder" if node.node_type == "dataset" else "box"
            color = "lightblue" if node.node_type == "dataset" else "lightgray"
            
            label = node.label
            if node.metadata.get("record_count"):
                label += f"\\n{node.metadata['record_count']:,} records"
            if node.metadata.get("quality_score"):
                label += f"\\nQ: {node.metadata['quality_score']:.0f}"
            
            lines.append(f'  {node.node_id} [label="{label}", shape={shape}, fillcolor={color}, style=filled];')
        
        lines.append("")
        
        # Edges
        for edge in self.graph.edges:
            label_str = f' [label="{edge.label}"]' if edge.label else ""
            lines.append(f"  {edge.source} -> {edge.target}{label_str};")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def to_mermaid(self) -> str:
        """Generate Mermaid diagram format"""
        lines = [
            "graph LR",
            "",
        ]
        
        # Nodes
        for node in self.graph.nodes:
            shape_start = "[(" if node.node_type == "dataset" else "["
            shape_end = ")]" if node.node_type == "dataset" else "]"
            
            label = node.label
            if node.metadata.get("record_count"):
                label += f"<br/>{node.metadata['record_count']:,} records"
            
            lines.append(f"  {node.node_id}{shape_start}{label}{shape_end}")
        
        lines.append("")
        
        # Edges
        for edge in self.graph.edges:
            arrow = "-->|" if edge.label else "-->"
            label_str = f"{edge.label}|" if edge.label else ""
            lines.append(f"  {edge.source} {arrow}{label_str} {edge.target}")
        
        return "\n".join(lines)
    
    def to_ascii(self) -> str:
        """Generate ASCII art diagram"""
        lines = ["Dataset Lineage Graph", "=" * 50, ""]
        
        # List nodes
        lines.append("NODES:")
        for node in self.graph.nodes:
            node_type_icon = "🗄️" if node.node_type == "dataset" else "📁" if node.node_type == "repo" else "⚙️"
            lines.append(f"  {node_type_icon} {node.label} ({node.node_type})")
        
        lines.append("")
        lines.append("DEPENDENCIES:")
        
        # List edges
        for edge in self.graph.edges:
            source_label = next((n.label for n in self.graph.nodes if n.node_id == edge.source), edge.source)
            target_label = next((n.label for n in self.graph.nodes if n.node_id == edge.target), edge.target)
            
            relationship = edge.label or edge.edge_type
            lines.append(f"  {source_label} --> [{relationship}] --> {target_label}")
        
        return "\n".join(lines)
    
    def build_from_manifest(self, manifest_path: Path | str) -> LineageGraph:
        """Build lineage graph from dataset manifest"""
        manifest_path = Path(manifest_path)
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Add dataset node
        dataset_name = manifest.get("dataset_name", "unknown")
        self.add_dataset_node(
            dataset_name,
            record_count=manifest.get("record_count"),
        )
        
        # Add source repositories
        for source in manifest.get("source_documents", []):
            if "source_repo" in source:
                repo_name = source["source_repo"]
                self.add_repository_node(repo_name)
                
                # Add edge from repo to dataset
                repo_id = f"repo_{repo_name.replace('/', '_')}"
                dataset_id = f"dataset_{dataset_name}"
                
                self.graph.add_edge(LineageEdge(
                    source=repo_id,
                    target=dataset_id,
                    edge_type="contributed_to",
                ))
        
        return self.graph
    
    def build_from_catalog(self, catalog_index: Path | str) -> LineageGraph:
        """Build lineage graph from catalog index"""
        catalog_index = Path(catalog_index)
        
        with open(catalog_index) as f:
            catalog = json.load(f)
        
        # Add all datasets
        for entry_data in catalog.get("entries", {}).values():
            self.add_dataset_node(
                entry_data["dataset_path"],
                record_count=entry_data.get("record_count"),
                quality_score=entry_data.get("quality_score"),
            )
            
            # Add dependencies
            for dep in entry_data.get("dependencies", []):
                self.add_dependency(dep, entry_data["dataset_path"])
        
        return self.graph
    
    def save_dot(self, output_path: Path | str) -> None:
        """Save DOT format to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_dot() + "\n", encoding="utf-8")
    
    def save_mermaid(self, output_path: Path | str) -> None:
        """Save Mermaid format to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_mermaid() + "\n", encoding="utf-8")
    
    def save_ascii(self, output_path: Path | str) -> None:
        """Save ASCII format to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_ascii() + "\n", encoding="utf-8")
    
    def generate_markdown_with_mermaid(
        self,
        title: str = "Dataset Lineage",
        description: str = "",
    ) -> str:
        """Generate markdown document with embedded Mermaid diagram"""
        lines = [
            f"# {title}",
            "",
        ]
        
        if description:
            lines.extend([description, ""])
        
        lines.extend([
            "## Lineage Diagram",
            "",
            "```mermaid",
            self.to_mermaid(),
            "```",
            "",
            "## Statistics",
            "",
            f"- **Total Datasets:** {sum(1 for n in self.graph.nodes if n.node_type == 'dataset')}",
            f"- **Total Repositories:** {sum(1 for n in self.graph.nodes if n.node_type == 'repo')}",
            f"- **Total Dependencies:** {len(self.graph.edges)}",
            "",
        ])
        
        return "\n".join(lines)
    
    def save_markdown_with_mermaid(
        self,
        output_path: Path | str,
        title: str = "Dataset Lineage",
        description: str = "",
    ) -> None:
        """Save markdown with Mermaid to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        markdown = self.generate_markdown_with_mermaid(title, description)
        output_path.write_text(markdown + "\n", encoding="utf-8")
