from pathlib import Path
import json
import zipfile

from peachtree.cli import main
from peachtree.registry import DatasetRegistryBuilder, sha256_file
from peachtree.signing import ArtifactSigner
from peachtree.sbom import SBOMGenerator
from peachtree.release_bundle import ReleaseBundleBuilder


def _artifact(tmp_path: Path, name: str = "dataset.jsonl") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"id": "a", "instruction": "Explain safely.", "output": "Safe output."}) + "\n", encoding="utf-8")
    return path


def test_sha256_file_is_stable(tmp_path: Path):
    path = _artifact(tmp_path)
    assert sha256_file(path) == sha256_file(path)
    assert len(sha256_file(path)) == 64


def test_registry_builds_artifact_records(tmp_path: Path):
    path = _artifact(tmp_path)
    registry = DatasetRegistryBuilder().build([path], name="demo", version="1")
    assert registry.artifact_count == 1
    assert registry.artifacts[0].sha256 == sha256_file(path)


def test_registry_write_and_read(tmp_path: Path):
    path = _artifact(tmp_path)
    builder = DatasetRegistryBuilder()
    registry = builder.build([path], name="demo", version="1")
    out, md = builder.write(registry, tmp_path / "registry.json", tmp_path / "registry.md")
    loaded = builder.read(out)
    assert loaded.name == "demo"
    assert md is not None and md.exists()


def test_registry_discover_directory(tmp_path: Path):
    _artifact(tmp_path / "data", "dataset.jsonl")
    registry = DatasetRegistryBuilder().discover([tmp_path / "data"], name="demo", version="1")
    assert registry.artifact_count == 1


def test_signature_roundtrip(tmp_path: Path):
    path = _artifact(tmp_path)
    signer = ArtifactSigner()
    sig_path = signer.sign_file_to_path(path, tmp_path / "dataset.sig.json", key="secret", key_id="test")
    verification = signer.verify_file(path, sig_path, key="secret")
    assert verification.valid


def test_signature_detects_wrong_key(tmp_path: Path):
    path = _artifact(tmp_path)
    signer = ArtifactSigner()
    sig_path = signer.sign_file_to_path(path, tmp_path / "dataset.sig.json", key="secret", key_id="test")
    verification = signer.verify_file(path, sig_path, key="wrong")
    assert not verification.valid


def test_sbom_from_registry(tmp_path: Path):
    path = _artifact(tmp_path)
    registry = DatasetRegistryBuilder().build([path], name="demo", version="1")
    sbom = SBOMGenerator().from_registry(registry)
    assert sbom.name == "demo"
    assert len(sbom.components) == 1


def test_sbom_write_markdown(tmp_path: Path):
    path = _artifact(tmp_path)
    sbom = SBOMGenerator().from_paths([path], name="demo", version="1")
    out, md = SBOMGenerator().write(sbom, tmp_path / "sbom.json", tmp_path / "sbom.md")
    assert out.exists()
    assert md is not None and md.exists()


def test_release_bundle_creates_zip_and_signature(tmp_path: Path):
    path = _artifact(tmp_path)
    report = ReleaseBundleBuilder().build(
        [path],
        tmp_path / "release.zip",
        name="demo",
        version="1",
        signing_key="secret",
    )
    assert Path(report.bundle_path).exists()
    assert Path(report.signature_path).exists()
    with zipfile.ZipFile(report.bundle_path) as bundle:
        assert "registry.json" in bundle.namelist()
        assert "sbom.json" in bundle.namelist()
        assert "release-manifest.json" in bundle.namelist()


def test_release_bundle_report_markdown(tmp_path: Path):
    path = _artifact(tmp_path)
    report = ReleaseBundleBuilder().build([path], tmp_path / "release.zip", name="demo", version="1")
    markdown = report.to_markdown()
    assert "Release Bundle Report" in markdown
    assert "does_not_train_models" in markdown


def test_cli_registry(tmp_path: Path, capsys):
    path = _artifact(tmp_path)
    rc = main(["registry", str(path), "--name", "demo", "--version", "1"])
    assert rc == 0
    assert '"artifact_count": 1' in capsys.readouterr().out


def test_cli_sign_and_verify(tmp_path: Path, capsys):
    path = _artifact(tmp_path)
    sig = tmp_path / "sig.json"
    rc = main(["sign", "--artifact", str(path), "--key", "secret", "--output", str(sig)])
    assert rc == 0
    rc = main(["sign", "--verify", "--artifact", str(path), "--signature", str(sig), "--key", "secret"])
    assert rc == 0
    assert '"valid": true' in capsys.readouterr().out


def test_cli_sbom(tmp_path: Path, capsys):
    path = _artifact(tmp_path)
    rc = main(["sbom", str(path), "--name", "demo", "--version", "1"])
    assert rc == 0
    assert '"sbom_format": "PeachTree-SBOM"' in capsys.readouterr().out


def test_cli_bundle(tmp_path: Path, capsys):
    path = _artifact(tmp_path)
    out = tmp_path / "release.zip"
    rc = main(["bundle", str(path), "--output", str(out), "--name", "demo", "--version", "1", "--signing-key", "secret"])
    assert rc == 0
    assert out.exists()
    assert '"artifact_count": 1' in capsys.readouterr().out
