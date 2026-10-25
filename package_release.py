#!/usr/bin/env python3
"""Build deterministic installable Reader and GitHub source ZIP archives."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import zipfile

SOURCE_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = SOURCE_ROOT / "project-graphify-reader"
ARCHIVE_TIME = (2026, 10, 26, 0, 0, 0)


def write_archive(root: Path, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = sorted((p for p in root.rglob("*") if p.is_file()
                    and not any(part in {".git", "__pycache__", ".pytest_cache"}
                                for part in p.relative_to(root).parts)),
                   key=lambda p: p.relative_to(root).as_posix())
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for path in files:
            if path.is_symlink():
                raise ValueError(f"Symlink not permitted: {path}")
            member = f"{root.name}/{path.relative_to(root).as_posix()}"
            if not re.fullmatch(r"[A-Za-z0-9 _./(),-]+", member) or len(member) > 472:
                raise ValueError(f"Unsupported Claude ZIP name: {member}")
            if path.suffix.lower() in {".zip", ".plugin"}:
                raise ValueError(f"Nested archive: {path}")
            info = zipfile.ZipInfo(member, date_time=ARCHIVE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Bad ZIP CRC: {destination}")
        if root == SKILL_ROOT and f"{root.name}/SKILL.md" not in archive.namelist():
            raise ValueError("Standalone Reader skill has no SKILL.md")
    print(f"{destination}: {len(files)} files, {destination.stat().st_size} bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="1.0.1")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    write_archive(SKILL_ROOT, args.output_dir / f"project-graphify-reader-v{args.version}.zip")
    write_archive(SOURCE_ROOT,
                  args.output_dir / f"project-graphify-reader-github-source-v{args.version}.zip")


if __name__ == "__main__":
    main()
