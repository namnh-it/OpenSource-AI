from pathlib import Path

from app.core import artifacts


def test_save_base64_writes_a_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(artifacts.get_settings().__class__, "artifact_dir", property(lambda _: tmp_path))
    filename, path = artifacts.save_base64("aGVsbG8=", prefix="test", content_type="text/plain")
    assert filename.endswith(".txt")
    assert path.read_bytes() == b"hello"
