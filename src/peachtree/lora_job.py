"""LoRA job card generation for PeachTree trainer handoff."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .registry import sha256_file


SUPPORTED_TRAINER_PROFILES = ("unsloth", "axolotl", "transformers", "modal", "colab", "kaggle")
SUPPORTED_DATASET_FORMATS = ("chatml", "alpaca", "sharegpt")


@dataclass(frozen=True)
class LoraHyperparameters:
    rank: int = 16
    alpha: int = 32
    dropout: float = 0.05
    learning_rate: float = 2e-4
    epochs: float = 1.0
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    max_seq_length: int = 4096
    warmup_ratio: float = 0.03

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LoraJobCard:
    job_name: str
    base_model: str
    dataset_path: str
    dataset_format: str
    trainer_profile: str
    output_dir: str
    created_at: str
    dataset_sha256: str
    hyperparameters: LoraHyperparameters
    safety: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_name": self.job_name,
            "base_model": self.base_model,
            "dataset_path": self.dataset_path,
            "dataset_format": self.dataset_format,
            "trainer_profile": self.trainer_profile,
            "output_dir": self.output_dir,
            "created_at": self.created_at,
            "dataset_sha256": self.dataset_sha256,
            "hyperparameters": self.hyperparameters.to_dict(),
            "safety": self.safety,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        hp = self.hyperparameters
        lines = [
            "# PeachTree LoRA Job Card",
            "",
            f"- Job: `{self.job_name}`",
            f"- Base model: `{self.base_model}`",
            f"- Trainer profile: `{self.trainer_profile}`",
            f"- Dataset: `{self.dataset_path}`",
            f"- Dataset format: `{self.dataset_format}`",
            f"- Output dir: `{self.output_dir}`",
            f"- Dataset SHA-256: `{self.dataset_sha256}`",
            "",
            "## Hyperparameters",
            "",
        ]
        for key, value in hp.to_dict().items():
            lines.append(f"- {key}: `{value}`")
        lines += ["", "## Safety", ""]
        for key, value in self.safety.items():
            lines.append(f"- {key}: `{value}`")
        return "\n".join(lines)


class LoraJobCardBuilder:
    """Builds LoRA job cards without launching training."""

    def build(
        self,
        dataset_path: str | Path,
        job_name: str,
        base_model: str,
        output_dir: str,
        trainer_profile: str = "unsloth",
        dataset_format: str = "chatml",
        hyperparameters: LoraHyperparameters | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LoraJobCard:
        profile = self._require(trainer_profile, SUPPORTED_TRAINER_PROFILES, "trainer profile")
        fmt = self._require(dataset_format, SUPPORTED_DATASET_FORMATS, "dataset format")
        dataset = Path(dataset_path)
        if not dataset.exists():
            raise FileNotFoundError(str(dataset))
        return LoraJobCard(
            job_name=job_name,
            base_model=base_model,
            dataset_path=str(dataset),
            dataset_format=fmt,
            trainer_profile=profile,
            output_dir=output_dir,
            created_at=datetime.now(timezone.utc).isoformat(),
            dataset_sha256=sha256_file(dataset),
            hyperparameters=hyperparameters or LoraHyperparameters(),
            safety={
                "dry_run_only": True,
                "does_not_train_models": True,
                "requires_human_approval_before_training": True,
                "review_handoff_manifest_first": True,
            },
            metadata=metadata or {},
        )

    def write(self, card: LoraJobCard, output_path: str | Path, markdown_output: str | Path | None = None) -> tuple[Path, Path | None]:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(card.to_json() + "\n", encoding="utf-8")
        md_path: Path | None = None
        if markdown_output:
            md_path = Path(markdown_output)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(card.to_markdown() + "\n", encoding="utf-8")
        return out, md_path

    @staticmethod
    def _require(value: str, allowed: tuple[str, ...], label: str) -> str:
        normalized = value.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"unsupported {label}: {value}")
        return normalized
