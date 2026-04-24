"""Dry-run training launch plans for PeachTree.

The launch plans are review artifacts only. They contain command previews and
checklists but never execute training jobs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .lora_job import LoraJobCard, LoraHyperparameters


@dataclass(frozen=True)
class DryRunTrainingPlan:
    job_name: str
    trainer_profile: str
    created_at: str
    command_preview: tuple[str, ...]
    checklist: tuple[str, ...]
    environment: dict[str, Any]
    safety: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Dry-Run Training Launch Plan",
            "",
            f"- Job: `{self.job_name}`",
            f"- Trainer profile: `{self.trainer_profile}`",
            f"- Created: `{self.created_at}`",
            "",
            "## Command Preview",
            "",
        ]
        lines.extend(f"```bash\n{command}\n```" for command in self.command_preview)
        lines += ["", "## Review Checklist", ""]
        lines.extend(f"- [ ] {item}" for item in self.checklist)
        lines += ["", "## Safety", ""]
        for key, value in self.safety.items():
            lines.append(f"- {key}: `{value}`")
        return "\n".join(lines)


class DryRunTrainingPlanner:
    """Creates trainer-specific dry-run plans without executing them."""

    def build(self, job_card: LoraJobCard) -> DryRunTrainingPlan:
        commands = self._commands(job_card)
        return DryRunTrainingPlan(
            job_name=job_card.job_name,
            trainer_profile=job_card.trainer_profile,
            created_at=datetime.now(timezone.utc).isoformat(),
            command_preview=tuple(commands),
            checklist=(
                "Verify dataset license/compliance gate passed.",
                "Verify quality/readiness gates passed.",
                "Verify model card and SBOM are present.",
                "Confirm base model license permits intended use.",
                "Confirm GPU, storage, and secrets are configured outside PeachTree.",
                "Obtain human approval before launching actual training.",
            ),
            environment={
                "base_model": job_card.base_model,
                "dataset_path": job_card.dataset_path,
                "dataset_format": job_card.dataset_format,
                "output_dir": job_card.output_dir,
                "hyperparameters": job_card.hyperparameters.to_dict(),
            },
            safety={
                "dry_run_only": True,
                "commands_are_preview_only": True,
                "does_not_execute_shell": True,
                "does_not_train_models": True,
                "does_not_upload_datasets": True,
            },
        )

    def write(self, plan: DryRunTrainingPlan, output_path: str | Path, markdown_output: str | Path | None = None) -> tuple[Path, Path | None]:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(plan.to_json() + "\n", encoding="utf-8")
        md_path: Path | None = None
        if markdown_output:
            md_path = Path(markdown_output)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(plan.to_markdown() + "\n", encoding="utf-8")
        return out, md_path

    @staticmethod
    def read_job_card(path: str | Path) -> LoraJobCard:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        hp = LoraHyperparameters(**data["hyperparameters"])
        return LoraJobCard(
            job_name=data["job_name"],
            base_model=data["base_model"],
            dataset_path=data["dataset_path"],
            dataset_format=data["dataset_format"],
            trainer_profile=data["trainer_profile"],
            output_dir=data["output_dir"],
            created_at=data["created_at"],
            dataset_sha256=data["dataset_sha256"],
            hyperparameters=hp,
            safety=data.get("safety", {}),
            metadata=data.get("metadata", {}),
        )

    @staticmethod
    def _commands(card: LoraJobCard) -> list[str]:
        hp = card.hyperparameters
        common = (
            f"--base-model {card.base_model} "
            f"--dataset {card.dataset_path} "
            f"--dataset-format {card.dataset_format} "
            f"--output-dir {card.output_dir} "
            f"--lora-rank {hp.rank} "
            f"--lora-alpha {hp.alpha} "
            f"--learning-rate {hp.learning_rate} "
            f"--epochs {hp.epochs} "
            f"--batch-size {hp.batch_size} "
            f"--grad-accum {hp.gradient_accumulation_steps} "
            f"--max-seq-length {hp.max_seq_length}"
        )
        if card.trainer_profile == "unsloth":
            return [f"# DRY RUN ONLY: python train_unsloth_lora.py {common}"]
        if card.trainer_profile == "axolotl":
            return [f"# DRY RUN ONLY: axolotl train generated_config.yml  # derived from {common}"]
        if card.trainer_profile == "transformers":
            return [f"# DRY RUN ONLY: accelerate launch train_lora.py {common}"]
        if card.trainer_profile == "modal":
            return [f"# DRY RUN ONLY: modal run train_lora.py -- {common}"]
        if card.trainer_profile == "colab":
            return [f"# DRY RUN ONLY: open Colab notebook and fill parameters: {common}"]
        if card.trainer_profile == "kaggle":
            return [f"# DRY RUN ONLY: kaggle kernels push with generated job spec: {common}"]
        return [f"# DRY RUN ONLY: unsupported trainer profile preview for {card.trainer_profile}"]
