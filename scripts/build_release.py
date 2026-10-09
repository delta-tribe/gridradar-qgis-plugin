#!/usr/bin/env python3
"""Build the GridRadar QGIS plugin release ZIP.

The ZIP holds the plugin source as is: one archive for every platform.

    ./scripts/build-release.sh
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PLUGIN_DIR_NAME = "gridradar_qgis_plugin"

EXCLUDE_DIR_NAMES = {
    ".git",
    ".github",
    ".vscode",
    "__pycache__",
    "scripts",
    "dist",
    "build",
    ".eggs",
    ".build-venv",
    "tests",
}

EXCLUDE_REL_PATHS = {
    Path("core/debug.py"),
}

EXCLUDE_FILE_NAMES = {
    ".gitignore",
    "requirements.txt",
    "README.md",
}

EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".zip", ".egg-info"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_version(plugin_root: Path) -> str:
    metadata = (plugin_root / "metadata.txt").read_text(encoding="utf-8")
    match = re.search(r"^version=(.+)$", metadata, re.MULTILINE)
    if not match:
        raise SystemExit("metadata.txt: version= not found")
    return match.group(1).strip()


def detect_qgis_python(explicit: str | None) -> str:
    if explicit:
        return explicit
    for candidate in ("/usr/bin/python3", shutil.which("python3") or ""):
        if not candidate:
            continue
        try:
            subprocess.run(
                [candidate, "-c", "import qgis.core"],
                check=True,
                capture_output=True,
            )
            return candidate
        except (subprocess.CalledProcessError, OSError):
            continue
    return sys.executable


def should_copy(path: Path, plugin_root: Path) -> bool:
    rel = path.relative_to(plugin_root)
    if any(part in EXCLUDE_DIR_NAMES for part in rel.parts):
        return False
    if rel in EXCLUDE_REL_PATHS:
        return False
    if path.name in EXCLUDE_FILE_NAMES:
        return False
    if any(path.name.endswith(suffix) for suffix in EXCLUDE_SUFFIXES):
        return False
    if path.is_dir() and path.name.endswith(".egg-info"):
        return False
    return True


def copy_plugin_tree(plugin_root: Path, destination: Path) -> int:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    copied = 0
    for src in sorted(plugin_root.rglob("*")):
        if not should_copy(src, plugin_root):
            continue
        rel = src.relative_to(plugin_root)
        dst = destination / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    return copied


def verify_import(staging_parent: Path, python_exe: str) -> None:
    code = """
import sys
sys.path.insert(0, %r)
from gridradar_qgis_plugin import classFactory
assert callable(classFactory)
print("import ok")
""" % str(staging_parent)
    subprocess.run([python_exe, "-B", "-c", code], check=True)


def create_zip(staging: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(staging.rglob("*")):
            if file_path.is_file():
                arcname = Path(PLUGIN_DIR_NAME) / file_path.relative_to(staging)
                zf.write(file_path, arcname)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python",
        help="Python for import smoke test (default: auto-detect via qgis.core)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root() / "dist",
        help="Directory for staging folder and zip (default: dist/)",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Only write the staging folder, skip zip archive",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip post-build import smoke test",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plugin_root = repo_root()
    version = read_version(plugin_root)
    qgis_python = detect_qgis_python(args.python)

    out_dir = args.output_dir.resolve()
    staging = out_dir / PLUGIN_DIR_NAME
    zip_path = out_dir / f"{PLUGIN_DIR_NAME}-{version}.zip"

    print(f"source:  {plugin_root}")
    print(f"verify:  {qgis_python}")
    print(f"staging: {staging}")

    copied = copy_plugin_tree(plugin_root, staging)

    if not args.no_verify:
        verify_import(out_dir, qgis_python)

    if not args.no_zip:
        create_zip(staging, zip_path)

    print("")
    print(f"files copied: {copied}")
    if not args.no_zip:
        print(f"release zip:  {zip_path}")


if __name__ == "__main__":
    main()
