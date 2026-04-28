"""Enhanced recursive learning tree with training/inference pathways.

Extends the base RecursiveLearningTree with specialized branches for
model training, inference workflows, and security-focused learning objectives.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from typing import Any

from .models import LearningNode, sha256_text
from .planner import RecursiveLearningTree


# Fuzzing-specific learning branches
FUZZING_BRANCHES = (
    "crash-triage",
    "corpus-generation",
    "harness-design",
    "sanitizer-integration",
    "coverage-analysis",
    "mutation-strategies",
    "defensive-patterns",
)

# Security-focused learning branches
SECURITY_BRANCHES = (
    "vulnerability-patterns",
    "exploit-techniques",
    "defense-mechanisms",
    "threat-modeling",
    "incident-response",
    "secure-coding",
    "compliance",
)

# Training workflow branches
TRAINING_BRANCHES = (
    "dataset-curation",
    "quality-validation",
    "safety-gates",
    "deduplication",
    "augmentation",
    "evaluation-metrics",
    "model-cards",
)

# Inference workflow branches
INFERENCE_BRANCHES = (
    "prompt-engineering",
    "context-optimization",
    "output-validation",
    "reasoning-chains",
    "tool-integration",
    "performance-tuning",
)


@dataclass
class TrainingInferencePath:
    """Represents a training or inference execution path through the learning tree."""
    
    path_id: str
    path_type: str  # "training" or "inference"
    nodes: tuple[LearningNode, ...]
    entry_point: str
    exit_point: str
    estimated_complexity: float  # 0.0-1.0
    
    @property
    def depth(self) -> int:
        """Total depth of the path."""
        return max((node.depth for node in self.nodes), default=0)
    
    @property
    def node_count(self) -> int:
        """Number of nodes in the path."""
        return len(self.nodes)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert path to dictionary representation."""
        return {
            "path_id": self.path_id,
            "path_type": self.path_type,
            "node_ids": [node.id for node in self.nodes],
            "entry_point": self.entry_point,
            "exit_point": self.exit_point,
            "depth": self.depth,
            "node_count": self.node_count,
            "estimated_complexity": self.estimated_complexity,
        }


@dataclass
class EnhancedLearningTree(RecursiveLearningTree):
    """Enhanced recursive learning tree with training/inference support."""
    
    specialized_mode: str | None = None  # "fuzzing", "security", "training", "inference"
    training_paths: list[TrainingInferencePath] = field(default_factory=list)
    inference_paths: list[TrainingInferencePath] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Initialize with specialized branches based on mode."""
        if self.specialized_mode == "fuzzing":
            # Override branches with fuzzing-specific ones
            object.__setattr__(self, "branches", FUZZING_BRANCHES)
        elif self.specialized_mode == "security":
            object.__setattr__(self, "branches", SECURITY_BRANCHES)
        elif self.specialized_mode == "training":
            object.__setattr__(self, "branches", TRAINING_BRANCHES)
        elif self.specialized_mode == "inference":
            object.__setattr__(self, "branches", INFERENCE_BRANCHES)
    
    def build_with_pathways(self) -> tuple[list[LearningNode], list[TrainingInferencePath], list[TrainingInferencePath]]:
        """Build tree and generate training/inference pathways.
        
        Returns:
            Tuple of (nodes, training_paths, inference_paths)
        """
        nodes = self.build()
        
        # Generate training pathways
        self.training_paths = self._generate_training_paths()
        
        # Generate inference pathways
        self.inference_paths = self._generate_inference_paths()
        
        return nodes, self.training_paths, self.inference_paths
    
    def _generate_training_paths(self) -> list[TrainingInferencePath]:
        """Generate training execution paths through the learning tree."""
        paths: list[TrainingInferencePath] = []
        
        # Find root node
        root = next((node for node in self.nodes.values() if node.parent_id is None), None)
        if not root:
            return paths
        
        # Generate paths for training-relevant branches
        training_tags = {
            "dataset-curation",
            "quality-validation",
            "safety-gates",
            "deduplication",
            "tests",
            "examples",
        }
        
        for start_node in self.nodes.values():
            if any(tag in training_tags for tag in start_node.tags):
                path = self._extract_path(start_node, "training")
                if path:
                    paths.append(path)
        
        return paths
    
    def _generate_inference_paths(self) -> list[TrainingInferencePath]:
        """Generate inference execution paths through the learning tree."""
        paths: list[TrainingInferencePath] = []
        
        # Find root node
        root = next((node for node in self.nodes.values() if node.parent_id is None), None)
        if not root:
            return paths
        
        # Generate paths for inference-relevant branches
        inference_tags = {
            "prompt-engineering",
            "context-optimization",
            "reasoning-chains",
            "commands",
            "architecture",
        }
        
        for start_node in self.nodes.values():
            if any(tag in inference_tags for tag in start_node.tags):
                path = self._extract_path(start_node, "inference")
                if path:
                    paths.append(path)
        
        return paths
    
    def _extract_path(self, start_node: LearningNode, path_type: str) -> TrainingInferencePath | None:
        """Extract a complete path from start node to leaf.
        
        Args:
            start_node: Starting node for the path
            path_type: Type of path ("training" or "inference")
            
        Returns:
            TrainingInferencePath or None if path cannot be extracted
        """
        # Build path from root to start_node
        path_nodes: list[LearningNode] = []
        current = start_node
        
        while current:
            path_nodes.insert(0, current)
            if current.parent_id:
                current = self.nodes.get(current.parent_id)  # type: ignore
            else:
                break
        
        # Extend to leaf nodes if possible
        leaf_nodes = self._find_leaf_nodes(start_node)
        if leaf_nodes:
            # Use the first leaf as the end point
            leaf = leaf_nodes[0]
            # Add nodes from start to leaf
            if leaf.id != start_node.id:
                intermediate = leaf
                intermediate_nodes = []
                while intermediate and intermediate.id != start_node.id:
                    intermediate_nodes.insert(0, intermediate)
                    if intermediate.parent_id:
                        intermediate = self.nodes.get(intermediate.parent_id)  # type: ignore
                    else:
                        break
                path_nodes.extend(intermediate_nodes)
        
        if not path_nodes:
            return None
        
        # Calculate complexity based on depth and node count
        complexity = min(1.0, (len(path_nodes) / 10.0) + (start_node.depth / 5.0))
        
        path_id = sha256_text(f"{path_type}:{start_node.id}:{len(path_nodes)}")[:16]
        
        return TrainingInferencePath(
            path_id=path_id,
            path_type=path_type,
            nodes=tuple(path_nodes),
            entry_point=path_nodes[0].goal,
            exit_point=path_nodes[-1].goal,
            estimated_complexity=complexity,
        )
    
    def _find_leaf_nodes(self, node: LearningNode) -> list[LearningNode]:
        """Find all leaf nodes descending from the given node."""
        if not node.children:
            return [node]
        
        leaves: list[LearningNode] = []
        for child_id in node.children:
            child = self.nodes.get(child_id)
            if child:
                leaves.extend(self._find_leaf_nodes(child))
        
        return leaves
    
    def get_optimal_training_path(self) -> TrainingInferencePath | None:
        """Get the optimal training path based on complexity and coverage.
        
        Returns:
            Best training path or None if no paths available
        """
        if not self.training_paths:
            return None
        
        # Prefer paths with medium complexity (not too simple, not too complex)
        sorted_paths = sorted(
            self.training_paths,
            key=lambda p: abs(p.estimated_complexity - 0.6),  # Target 0.6 complexity
        )
        
        return sorted_paths[0] if sorted_paths else None
    
    def get_optimal_inference_path(self) -> TrainingInferencePath | None:
        """Get the optimal inference path based on complexity and coverage.
        
        Returns:
            Best inference path or None if no paths available
        """
        if not self.inference_paths:
            return None
        
        # Prefer shorter, simpler paths for inference
        sorted_paths = sorted(
            self.inference_paths,
            key=lambda p: (p.estimated_complexity, p.depth),
        )
        
        return sorted_paths[0] if sorted_paths else None
    
    def to_json_with_paths(self) -> str:
        """Export tree with training/inference paths to JSON."""
        if not self.nodes:
            self.build_with_pathways()
        
        output = {
            "project": self.project,
            "goal": self.goal,
            "specialized_mode": self.specialized_mode,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "training_paths": [path.to_dict() for path in self.training_paths],
            "inference_paths": [path.to_dict() for path in self.inference_paths],
            "statistics": {
                "total_nodes": len(self.nodes),
                "max_depth": max((node.depth for node in self.nodes.values()), default=0),
                "training_paths_count": len(self.training_paths),
                "inference_paths_count": len(self.inference_paths),
            },
        }
        
        return json.dumps(output, indent=2, sort_keys=True)
    
    def export_training_workflow(self, output_path: str) -> dict[str, Any]:
        """Export training workflow based on optimal training path.
        
        Args:
            output_path: Path to write training workflow JSON
            
        Returns:
            Workflow summary
        """
        from pathlib import Path
        
        optimal_path = self.get_optimal_training_path()
        if not optimal_path:
            return {"error": "No training paths available"}
        
        workflow = {
            "workflow_type": "training",
            "project": self.project,
            "path_id": optimal_path.path_id,
            "steps": [
                {
                    "step_number": i + 1,
                    "node_id": node.id,
                    "goal": node.goal,
                    "depth": node.depth,
                    "tags": list(node.tags),
                }
                for i, node in enumerate(optimal_path.nodes)
            ],
            "estimated_complexity": optimal_path.estimated_complexity,
            "total_steps": optimal_path.node_count,
        }
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(workflow, indent=2, sort_keys=True), encoding="utf-8")
        
        return {
            "output_path": str(path),
            "workflow_type": "training",
            "total_steps": optimal_path.node_count,
        }
    
    def export_inference_workflow(self, output_path: str) -> dict[str, Any]:
        """Export inference workflow based on optimal inference path.
        
        Args:
            output_path: Path to write inference workflow JSON
            
        Returns:
            Workflow summary
        """
        from pathlib import Path
        
        optimal_path = self.get_optimal_inference_path()
        if not optimal_path:
            return {"error": "No inference paths available"}
        
        workflow = {
            "workflow_type": "inference",
            "project": self.project,
            "path_id": optimal_path.path_id,
            "steps": [
                {
                    "step_number": i + 1,
                    "node_id": node.id,
                    "goal": node.goal,
                    "depth": node.depth,
                    "tags": list(node.tags),
                }
                for i, node in enumerate(optimal_path.nodes)
            ],
            "estimated_complexity": optimal_path.estimated_complexity,
            "total_steps": optimal_path.node_count,
        }
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(workflow, indent=2, sort_keys=True), encoding="utf-8")
        
        return {
            "output_path": str(path),
            "workflow_type": "inference",
            "total_steps": optimal_path.node_count,
        }


def build_fuzzing_learning_tree(
    project: str,
    goal: str,
    max_depth: int = 2,
) -> EnhancedLearningTree:
    """Create a fuzzing-specialized learning tree.
    
    Args:
        project: Project name
        goal: Learning goal
        max_depth: Maximum tree depth
        
    Returns:
        EnhancedLearningTree with fuzzing branches
    """
    return EnhancedLearningTree(
        project=project,
        goal=goal,
        max_depth=max_depth,
        specialized_mode="fuzzing",
    )


def build_security_learning_tree(
    project: str,
    goal: str,
    max_depth: int = 2,
) -> EnhancedLearningTree:
    """Create a security-specialized learning tree.
    
    Args:
        project: Project name
        goal: Learning goal
        max_depth: Maximum tree depth
        
    Returns:
        EnhancedLearningTree with security branches
    """
    return EnhancedLearningTree(
        project=project,
        goal=goal,
        max_depth=max_depth,
        specialized_mode="security",
    )
