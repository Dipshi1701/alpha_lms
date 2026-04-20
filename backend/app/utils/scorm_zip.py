"""
ZIP validation and safe extraction for SCORM packages.

- Validates magic bytes and zipfile integrity before extraction.
- Enforces maximum upload size (configurable).
- Extracts each file manually with zip-slip checks (no raw extractall).
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path


ZIP_MAGIC_PK = b"PK"


def validate_zip_bytes(data: bytes, max_bytes: int) -> None:
    """Reject invalid, empty, or oversized archives before writing to disk."""
    if not data:
        raise ValueError("Empty file")
    if len(data) > max_bytes:
        raise ValueError(f"ZIP exceeds maximum allowed size ({max_bytes // (1024 * 1024)} MB)")
    if len(data) < 4 or not data.startswith(ZIP_MAGIC_PK):
        raise ValueError("Not a valid ZIP file (missing PK header)")
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise ValueError("Not a valid ZIP archive")


def safe_extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """
    Extract ZIP to dest_dir. Each member is validated for zip-slip; files are
    written explicitly (no extractall) to avoid traversal issues.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest_dir.resolve()

    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise ValueError(f"Corrupt ZIP archive (bad member: {bad})")

        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if not name or name.startswith("/") or ".." in Path(name).parts:
                raise ValueError("Invalid ZIP entry path")
            target = dest_dir / name
            try:
                target.resolve().relative_to(dest_resolved)
            except ValueError as e:
                raise ValueError("ZIP path escapes destination (zip-slip)") from e

        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            target = dest_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(target, "wb") as dst:
                dst.write(src.read())
