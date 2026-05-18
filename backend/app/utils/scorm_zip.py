"""
ZIP validation and safe extraction for SCORM packages.

- Validates magic bytes and zipfile integrity before extraction.
- Enforces maximum upload size (configurable).
- Extracts each file manually with zip-slip checks (no raw extractall).
"""
from __future__ import annotations

import io
import hashlib
import re
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath


ZIP_MAGIC_PK = b"PK"


def _normalise_zip_name(name: str) -> str:
    """Return a portable POSIX-style zip entry path."""
    return name.replace("\\", "/").strip("/")


def _ascii_safe_segment(segment: str) -> str:
    """Convert one path segment to a filesystem-safe ASCII name."""
    normalised = unicodedata.normalize("NFKD", segment)
    ascii_name = normalised.encode("ascii", "ignore").decode("ascii")
    ascii_name = re.sub(r"[^A-Za-z0-9._ -]+", "_", ascii_name)
    ascii_name = re.sub(r"\s+", " ", ascii_name).strip(" .")
    return ascii_name or "file"


def _ascii_safe_zip_path(name: str) -> str:
    """Convert a zip path to an ASCII-only relative path."""
    parts = PurePosixPath(_normalise_zip_name(name)).parts
    return "/".join(_ascii_safe_segment(part) for part in parts)


def _dedupe_path(path: str, used: set[str]) -> str:
    """Avoid collisions after ASCII normalisation."""
    if path not in used:
        used.add(path)
        return path

    pure = PurePosixPath(path)
    stem = pure.stem or "file"
    suffix = pure.suffix
    parent = "" if str(pure.parent) == "." else f"{pure.parent}/"
    digest = hashlib.sha1(path.encode("utf-8", errors="ignore")).hexdigest()[:8]
    candidate = f"{parent}{stem}-{digest}{suffix}"

    counter = 2
    while candidate in used:
        candidate = f"{parent}{stem}-{digest}-{counter}{suffix}"
        counter += 1

    used.add(candidate)
    return candidate


def _validate_zip_entry_name(name: str) -> None:
    """Reject absolute, drive-based, empty, or traversal paths."""
    normalised = _normalise_zip_name(name)
    parts = PurePosixPath(normalised).parts
    if not normalised or normalised.startswith("/") or ".." in parts:
        raise ValueError("Invalid ZIP entry path")
    if any(part.endswith(":") for part in parts):
        raise ValueError("Invalid ZIP entry path")


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


def safe_extract_zip(zip_path: Path, dest_dir: Path) -> dict[str, str]:
    """
    Extract ZIP to dest_dir. Each member is validated for zip-slip; files are
    written explicitly (no extractall) to avoid traversal issues.

    Returns a mapping of original ZIP paths to the extracted ASCII-safe paths.
    This lets the manifest parser resolve launch hrefs even when the archive
    used non-ASCII filenames that cannot be created on ASCII-locale servers.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest_dir.resolve()

    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise ValueError(f"Corrupt ZIP archive (bad member: {bad})")

        filename_map: dict[str, str] = {}
        used_paths: set[str] = set()

        for info in zf.infolist():
            if info.is_dir():
                continue
            original_name = _normalise_zip_name(info.filename)
            _validate_zip_entry_name(original_name)

            safe_name = _dedupe_path(_ascii_safe_zip_path(original_name), used_paths)
            filename_map[original_name] = safe_name

            target = dest_dir / safe_name
            try:
                target.resolve().relative_to(dest_resolved)
            except ValueError as e:
                raise ValueError("ZIP path escapes destination (zip-slip)") from e

        for info in zf.infolist():
            if info.is_dir():
                continue
            original_name = _normalise_zip_name(info.filename)
            target = dest_dir / filename_map[original_name]
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(target, "wb") as dst:
                dst.write(src.read())

    return filename_map
