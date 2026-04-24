from __future__ import annotations

from dataclasses import dataclass, field
import json

from .models import LearningNode, sha256_text

DEFAULT_BRANCHES = (
    "architecture",
    "commands",
    "safety",
    "tests",
    "examples",
    "failure-modes",
    "docs",
)


@dataclass
class RecursiveLearningTree:
    project: str
    goal: str
    max_depth: int = 2
    branches: tuple[str, ...] = DEFAULT_BRANCHES
    nodes: dict[str, LearningNode] = field(default_factory=dict)

    def build(self) -> list[LearningNode]:
        self.nodes.clear()
        root = self._make_node(self.goal, depth=0, parent_id=None, tags=("root",))
        self.nodes[root.id] = root
        self._expand(root)
        return list(self.nodes.values())

    def _expand(self, parent: LearningNode) -> None:
        if parent.depth >= self.max_depth:
            return
        child_ids: list[str] = []
        for branch in self.branches:
            child = self._make_node(f"{parent.goal} :: learn {branch}", parent.depth + 1, parent.id, (branch,))
            self.nodes[child.id] = child
            child_ids.append(child.id)
            self._expand(child)
        self.nodes[parent.id] = LearningNode(
            id=parent.id,
            goal=parent.goal,
            project=parent.project,
            depth=parent.depth,
            parent_id=parent.parent_id,
            status=parent.status,
            children=tuple(child_ids),
            tags=parent.tags,
        )

    def _make_node(self, goal: str, depth: int, parent_id: str | None, tags: tuple[str, ...]) -> LearningNode:
        node_id = sha256_text(f"{self.project}:{goal}:{depth}:{parent_id}")[:16]
        return LearningNode(node_id, goal, self.project, depth, parent_id, tags=tags)

    def to_json(self) -> str:
        if not self.nodes:
            self.build()
        return json.dumps([node.to_dict() for node in self.nodes.values()], indent=2, sort_keys=True)
