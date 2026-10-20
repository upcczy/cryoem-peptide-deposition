#!/usr/bin/env python3
"""Build the public candidate handbook, SHA-256 manifest and allowlisted ZIP.

Python 3.10+, standard library only. This helper writes package deliverables,
not experiment files. It never uploads, publishes, deletes extra installed
files, or grants permission to publish the license proposal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

NAME = "cryoem-peptide-deposition"
MODULES = [
    ("AGENTS.md", "Directory entry", "directory-entry"),
    ("SKILL.md", "Skill workflow", "skill-workflow"),
    ("references/onedep-field-guide.md", "OneDep field guide", "onedep-field-guide"),
    ("references/acquisition-metadata.md", "Acquisition metadata", "acquisition-metadata"),
    ("references/jeol-cryoarm300-default-profile.md", "Optional JEOL and grid defaults", "jeol-default-profile"),
    ("assets/new-deposition-template.md", "New deposition template", "new-deposition-template"),
    ("examples/synthetic-deposition.md", "Synthetic example", "synthetic-example"),
]
# This list is deliberately explicit. New package files require review here;
# merely placing a file under scripts/, tests/ or references/ is not enough.
OPTIONAL_FILES = (
    "README.md", "LICENSE-REVIEW.md", "LICENSE-MIT.proposed", "config.example.json",
    ".gitignore", ".gitattributes", "agents/openai.yaml", ".github/workflows/ci.yml",
    "scripts/inspect_inputs.py", "scripts/build_package.py",
    "tests/test_inspect_inputs.py", "tests/test_build_package.py",
    "tests/forward-case/actual.log", "tests/forward-case/new_movie.mdoc",
    "tests/forward-case/shottest.log",
)
GENERATED_FILES = ("deposition-handbook.md", "manifest.json")
ALLOWLIST = tuple(relative for relative, _, _ in MODULES) + ("VERSION",) + OPTIONAL_FILES + GENERATED_FILES
EXCLUDED_PARTS = frozenset({".git", "dist", "__pycache__", "records", "config", "config.local"})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_source(root: Path, relative: str) -> Path:
    path = root / relative
    if any(part in EXCLUDED_PARTS for part in Path(relative).parts):
        raise ValueError("Excluded path cannot be a payload member: " + relative)
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise ValueError("Payload resolves outside source root: " + relative) from error
    # Reject symlinked files/directories even when their current target is inside
    # the root, so portable builds do not depend on link traversal.
    for candidate in (path, *path.parents):
        if candidate == root:
            break
        if candidate.is_symlink():
            raise ValueError("Payload symlinks are not permitted: " + relative)
    return path


def payload_files(root: Path) -> list[Path]:
    files = []
    for relative in sorted(set(ALLOWLIST)):
        path = safe_source(root, relative)
        if path.is_file():
            files.append(path)
        elif path.exists():
            raise ValueError("Payload file is not a regular file: " + relative)
    return files


def read_version(root: Path) -> str:
    version = safe_source(root, "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", version):
        raise ValueError("VERSION must contain one semantic version such as 0.1.0")
    return version


def build_handbook(root: Path, version: str) -> Path:
    anchors = {(root / relative).resolve(): anchor for relative, _, anchor in MODULES}
    result = [
        "# Peptide cryo-EM deposition handbook", "", "Candidate version: " + version + ".",
        "Generated from the package Markdown. The example is synthetic; it is not a batch-default table.",
        "License proposal and publication remain subject to human review. See LICENSE-REVIEW.md.",
        "Read this single handbook for portable handoff, or use the individual modules in the full package.",
        "", "## Contents", "",
    ]
    result.extend("- [" + title + "](#" + anchor + ")" for _, title, anchor in MODULES)
    for relative, title, anchor in MODULES:
        path = safe_source(root, relative)
        body = path.read_text(encoding="utf-8")
        if relative == "SKILL.md":
            body = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", body, count=1, flags=re.S)

        def link_replace(match: re.Match) -> str:
            label, target = match.groups()
            plain = target.strip("<>")
            if re.match(r"^[a-z]+:", plain, flags=re.I) or plain.startswith("#"):
                return match.group(0)
            candidate = (path.parent / plain.split("#", 1)[0]).resolve()
            if candidate in anchors:
                return "[" + label + "](#" + anchors[candidate] + ")"
            if candidate.exists():
                try:
                    rebased = candidate.relative_to(root).as_posix()
                except ValueError:
                    return match.group(0)
                if "#" in plain:
                    rebased += "#" + plain.split("#", 1)[1]
                return "[" + label + "](" + rebased + ")"
            return match.group(0)

        body = re.sub(r"\[([^\]\n]+)\]\(([^)\n]+)\)", link_replace, body)
        lines, fence = [], None
        for line in body.splitlines():
            marker = re.match(r"^\s*(`{3,}|~{3,})", line)
            if marker:
                if fence is None:
                    fence = marker.group(1)[0]
                elif fence == marker.group(1)[0]:
                    fence = None
            if fence is None and line.startswith("#"):
                line = "#" + line
            lines.append(line)
        result.extend(["", '<a id="' + anchor + '"></a>', "", "## " + title, "", "\n".join(lines)])
    result.extend([
        "", "## Local tools", "",
        "Run `python scripts/inspect_inputs.py --help` for read-only evidence extraction.",
        "The inspector emits JSON, does not upload or edit inputs, and reads MRC headers only.",
        "Rebuild from reviewed source with `python scripts/build_package.py`.",
        "The manifest lists relative payload paths and SHA-256 hashes; it does not establish source authenticity.", "",
    ])
    output = safe_source(root, "deposition-handbook.md")
    output.write_text("\n".join(result), encoding="utf-8")
    return output


def existing_install_files(installed: Path) -> set[str]:
    # Extra files are reported, never removed, including ignored/private files.
    return {path.relative_to(installed).as_posix() for path in installed.rglob("*") if path.is_file()}


def install_payload(root: Path, installed: Path, files: list[Path]) -> None:
    if installed.name != NAME or installed == root or root in installed.parents or installed in root.parents:
        raise ValueError("install-dir must be a separate intended skill directory with the same name")
    expected = {path.relative_to(root).as_posix() for path in files}
    extras = existing_install_files(installed) - expected if installed.exists() else set()
    if extras:
        raise ValueError("Installed directory has extra files; no files copied or deleted: " + ", ".join(sorted(extras)))
    # Preflight target paths as well; a destination link must not redirect a copy.
    for source in files:
        relative = source.relative_to(root).as_posix()
        safe_source(installed, relative)
    installed.mkdir(parents=True, exist_ok=True)
    for source in files:
        destination = installed / source.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for source in files:
        if sha256(source) != sha256(installed / source.relative_to(root)):
            raise RuntimeError("Installed hash mismatch: " + source.relative_to(root).as_posix())


def verify_manifest(root: Path) -> list[Path]:
    files = payload_files(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    records = manifest["files"]
    names = [record["path"] for record in records]
    expected = {path.relative_to(root).as_posix() for path in files if path.name != "manifest.json"}
    if len(names) != len(set(names)) or set(names) != expected:
        raise ValueError("Manifest membership does not match allowlisted payload")
    if manifest["version"] != read_version(root):
        raise ValueError("Manifest version does not match VERSION")
    for record in records:
        relative = record["path"]
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or "\\" in relative:
            raise ValueError("Manifest must use portable relative paths")
        source = safe_source(root, relative)
        if source.stat().st_size != record["bytes"] or sha256(source) != record["sha256"]:
            raise ValueError("Manifest content mismatch: " + relative)
    return files


def verify_zip(root: Path, archive: Path, files: list[Path]) -> None:
    expected = {NAME + "/" + path.relative_to(root).as_posix() for path in files}
    with zipfile.ZipFile(archive) as check:
        if check.testzip() is not None:
            raise ValueError("ZIP CRC check failed")
        if len(check.namelist()) != len(expected) or set(check.namelist()) != expected:
            raise ValueError("ZIP membership does not match allowlisted payload")
        for source in files:
            name = NAME + "/" + source.relative_to(root).as_posix()
            if hashlib.sha256(check.read(name)).hexdigest() != sha256(source):
                raise ValueError("ZIP hash mismatch: " + name)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--install-dir", type=Path, help="Optional explicit installed-copy destination; never deletes extras")
    parser.add_argument("--zip-output", type=Path, help="Default: dist/cryoem-peptide-deposition-<VERSION>.zip")
    parser.add_argument("--verify-only", action="store_true", help="Read-only verify existing manifest and ZIP; do not rebuild or install")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if root.name != NAME or not (root / "SKILL.md").is_file():
            raise ValueError("root must be the intended cryoem-peptide-deposition source directory")
        for relative, _, _ in MODULES:
            if not safe_source(root, relative).is_file():
                raise ValueError("Missing module: " + relative)
        version = read_version(root)
        archive_candidate = args.zip_output if args.zip_output else root / "dist" / (NAME + "-" + version + ".zip")
        if archive_candidate.is_symlink():
            raise ValueError("ZIP output must not be a symlink")
        archive = archive_candidate.resolve()
        if not args.zip_output and root not in archive.parents:
            raise ValueError("Default dist/ output resolves outside the source root")
        if archive.suffix.lower() != ".zip":
            raise ValueError("ZIP output must have .zip extension")
        if archive == root or (root in archive.parents and root / "dist" not in archive.parents):
            raise ValueError("ZIP inside the source root must be under dist/")
        if args.verify_only:
            if args.install_dir:
                raise ValueError("--verify-only cannot be combined with --install-dir")
            files = verify_manifest(root)
            verify_zip(root, archive, files)
            output = {"skill": NAME, "version": version, "verified": True,
                      "payload_files": len(files), "manifest_hashes_match": True, "zip_hashes_match": True}
        else:
            handbook = build_handbook(root, version)
            manifest_path = safe_source(root, "manifest.json")
            manifest = {
                "skill": NAME, "version": version, "hash_algorithm": "SHA-256",
                "license_status": "pending-human-review",
                "license_proposal": "LICENSE-MIT.proposed", "license_review": "LICENSE-REVIEW.md",
                "publication_status": "local-candidate-not-published",
                "files": [
                    {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
                    for path in payload_files(root) if path != manifest_path
                ],
            }
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            files = verify_manifest(root)
            if args.install_dir:
                install_payload(root, args.install_dir.resolve(), files)
            archive.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output_zip:
                for source in files:
                    info = zipfile.ZipInfo(NAME + "/" + source.relative_to(root).as_posix(), (1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    output_zip.writestr(info, source.read_bytes())
            verify_zip(root, archive, files)
            output = {"skill": NAME, "version": version, "handbook": handbook.name,
                      "zip": archive.name, "payload_files": len(files), "manifest_hashes_match": True,
                      "zip_hashes_match": True, "installed_hashes_match": True if args.install_dir else None,
                      "license_status": "pending-human-review", "publication_status": "local-candidate-not-published"}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
