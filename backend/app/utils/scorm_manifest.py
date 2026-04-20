"""
SCORM 1.2 imsmanifest.xml: pick launch file from first <organization>,
first <item> whose referenced resource has adlcp:scormtype=\"sco\".
Falls back to first SCO resource in <resources> if no item matches.

Also extracts common metadata for persistence (title, identifier, version).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from pathlib import Path


def _local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _sco_attrs(resource_el: ET.Element) -> tuple[str | None, bool]:
    """Return (href, is_sco) for a <resource> element."""
    href = resource_el.get("href")
    is_sco = False
    for key, val in resource_el.attrib.items():
        if "scormtype" in key.lower() and val and "sco" in val.lower():
            is_sco = True
            break
    # Some packages omit adlcp:scormtype; treat resource with href as launch candidate
    if href and not is_sco:
        for key, val in resource_el.attrib.items():
            if _local(key) == "scormtype" and val and "sco" in val.lower():
                is_sco = True
                break
    return href, is_sco


def _build_resource_map(root: ET.Element) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for el in root.iter():
        if _local(el.tag) != "resource":
            continue
        rid = el.get("identifier")
        if not rid:
            continue
        href, is_sco = _sco_attrs(el)
        out[rid] = {"href": href, "is_sco": is_sco}
    return out


def _first_item_sco_href(
    parent: ET.Element, resource_map: dict[str, dict]
) -> str | None:
    """Depth-first: first item with identifierref pointing to a SCO resource with href."""
    for el in parent:
        if _local(el.tag) != "item":
            continue
        ref = el.get("identifierref")
        if ref and ref in resource_map:
            info = resource_map[ref]
            if info.get("is_sco") and info.get("href"):
                return info["href"]
        nested = _first_item_sco_href(el, resource_map)
        if nested:
            return nested
    return None


def _first_item_any_href(
    parent: ET.Element, resource_map: dict[str, dict]
) -> str | None:
    """Depth-first: first item whose resource has href (organization order)."""
    for el in parent:
        if _local(el.tag) != "item":
            continue
        ref = el.get("identifierref")
        if ref and ref in resource_map:
            info = resource_map[ref]
            if info.get("href"):
                return info["href"]
        nested = _first_item_any_href(el, resource_map)
        if nested:
            return nested
    return None


def find_scorm12_launch_href(unpacked_root: Path) -> tuple[Path, str] | None:
    """
    Returns (path_to_imsmanifest, href_relative_to_manifest_dir) or None.
    """
    manifest_path: Path | None = None
    for p in unpacked_root.rglob("imsmanifest.xml"):
        manifest_path = p
        break
    if not manifest_path:
        return None

    tree = ET.parse(manifest_path)
    root = tree.getroot()
    resource_map = _build_resource_map(root)

    org_el = None
    for el in root.iter():
        if _local(el.tag) == "organizations":
            org_el = el
            break

    href: str | None = None
    if org_el is not None:
        first_org = None
        for child in org_el:
            if _local(child.tag) == "organization":
                first_org = child
                break
        if first_org is not None:
            href = _first_item_sco_href(first_org, resource_map)
            if not href:
                href = _first_item_any_href(first_org, resource_map)

    if not href:
        for _rid, info in resource_map.items():
            if info.get("is_sco") and info.get("href"):
                href = info["href"]
                break

    if not href:
        for _rid, info in resource_map.items():
            if info.get("href"):
                href = info["href"]
                break

    if not href:
        return None

    return manifest_path, href


def launch_file_relative_to_unpacked(unpacked_root: Path) -> str | None:
    """
    Resolve launch file path relative to unpacked_root (POSIX slashes).
    """
    pair = find_scorm12_launch_href(unpacked_root)
    if not pair:
        return None
    manifest_path, href = pair
    manifest_dir = manifest_path.parent
    # href may contain subpaths
    launch_abs = (manifest_dir / href).resolve()
    unpacked_resolved = unpacked_root.resolve()
    try:
        launch_abs.relative_to(unpacked_resolved)
    except ValueError:
        return None
    rel = os.path.relpath(launch_abs, unpacked_resolved)
    return rel.replace("\\", "/")


def _manifest_root_metadata(root: ET.Element) -> tuple[str | None, str | None, str | None]:
    """identifier, version, defaultOrganization from <manifest>."""
    identifier = None
    version = None
    default_org = None
    for el in root.iter():
        if _local(el.tag) != "manifest":
            continue
        identifier = el.get("identifier")
        version = el.get("version")
        default_org = el.get("defaultOrganization") or el.get("defaultorganization")
        break
    return identifier, version, default_org


def _first_title_under_organizations(root: ET.Element) -> str | None:
    for el in root.iter():
        if _local(el.tag) != "organizations":
            continue
        for child in el.iter():
            if _local(child.tag) == "title" and child.text and child.text.strip():
                return child.text.strip()[:2000]
    for el in root.iter():
        if _local(el.tag) == "title" and el.text and el.text.strip():
            return el.text.strip()[:2000]
    return None


@dataclass
class ScormPackageParseResult:
    """Parsed SCORM package for DB + launch URL."""

    imsmanifest_relative: str  # relative to course storage root (e.g. unpacked/imsmanifest.xml)
    launch_relative_stored: str  # e.g. unpacked/res/index.html (under course root)
    manifest_title: str | None
    manifest_identifier: str | None
    schema_version: str | None


def parse_scorm_package(
    unpacked_root: Path, course_storage_root: Path
) -> ScormPackageParseResult | None:
    """
    Full parse: imsmanifest path, metadata, launch path stored as under course root.
    course_storage_root = storage/scorm/{course_id}/ (contains unpacked/).
    """
    manifest_path: Path | None = None
    for p in unpacked_root.rglob("imsmanifest.xml"):
        manifest_path = p
        break
    if not manifest_path:
        return None

    try:
        imsmanifest_relative = str(manifest_path.relative_to(course_storage_root)).replace(
            "\\", "/"
        )
    except ValueError:
        return None

    tree = ET.parse(manifest_path)
    root = tree.getroot()
    mid, ver, _ = _manifest_root_metadata(root)
    title = _first_title_under_organizations(root)

    pair = find_scorm12_launch_href(unpacked_root)
    if not pair:
        return None
    _, href = pair
    manifest_dir = manifest_path.parent
    launch_abs = (manifest_dir / href).resolve()
    unpacked_resolved = unpacked_root.resolve()
    try:
        launch_abs.relative_to(unpacked_resolved)
    except ValueError:
        return None
    rel_unpacked = os.path.relpath(launch_abs, unpacked_resolved).replace("\\", "/")
    stored_launch = f"unpacked/{rel_unpacked}"

    return ScormPackageParseResult(
        imsmanifest_relative=imsmanifest_relative,
        launch_relative_stored=stored_launch,
        manifest_title=title,
        manifest_identifier=mid,
        schema_version=ver,
    )

