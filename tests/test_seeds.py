from pathlib import Path
import json

from peachtree.seeds import PeachSeedExporter, write_seed_manifest


def _write_dataset(path: Path) -> None:
    record = {
        "id": "record-1",
        "instruction": "Explain this local parser fixture.",
        "input": "Repository: peachfuzz\nPath: targets/json.py\n{}",
        "output": "Local parser fixture for fuzzing.",
        "source_repo": "peachfuzz",
        "source_path": "targets/json.py",
        "source_digest": "abc123",
        "license_id": "apache-2.0",
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")


def test_seed_export_is_dry_run_by_default(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.jsonl"
    output = tmp_path / "corpus"
    _write_dataset(dataset)

    manifest = PeachSeedExporter().export(dataset, "json", output)

    assert manifest.write_enabled is False
    assert len(manifest.seeds) == 1
    assert not output.exists()


def test_seed_export_writes_manifest_and_corpus(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.jsonl"
    output = tmp_path / "corpus"
    manifest_path = tmp_path / "seeds.json"
    _write_dataset(dataset)

    manifest = PeachSeedExporter().export(dataset, "graphql", output, write=True)
    write_seed_manifest(manifest, manifest_path)

    assert output.exists()
    assert manifest_path.exists()
    assert len(list(output.iterdir())) == 1
    assert manifest.seeds[0].path.endswith(".graphql")


def test_seed_export_skips_secret_like_payload(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.jsonl"
    record = {
        "id": "record-1",
        "instruction": "bad",
        "input": "api_key = '1234567890abcdef1234567890abcdef'",
        "output": "bad",
        "source_repo": "x",
        "source_path": "x.txt",
        "source_digest": "x",
        "license_id": "apache-2.0",
    }
    dataset.write_text(json.dumps(record) + "\n", encoding="utf-8")

    manifest = PeachSeedExporter().export(dataset, "log", tmp_path / "out", write=True)

    assert len(manifest.seeds) == 0
    assert manifest.skipped == 1
