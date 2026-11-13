#!/usr/bin/env python3
"""Generate the Docker relationship data for one repository (repos/<name>.json) from the local Docker.

Usage:
    python3 generate.py <repository path> [--name DISPLAY_NAME] [--color '#rrggbb'] [--image REF ...]

How items are attributed to the repository:
    - Containers: those with a label value containing the repository path
      (Dev Containers' devcontainer.config_file, a Compose working folder, a containerlab topology, etc.),
      and those started from a vsc- derived image (see below)
    - Images: the image each of those containers was started from, images named
      vsc-<folder name>-<hash>[-features][-uid], images given with --image,
      and the bases of all of them (ancestors whose layer sequence is a prefix match)
Dependencies: only the standard library of the Python pinned in .python-version, plus the docker CLI.
    Run it with the Python in this folder's .venv (e.g. .venv/bin/python generate.py ../my-app).
    See "Set up" in README.md for how to create the environment.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCRIPT_DIR: Path = Path(__file__).resolve().parent


def check_environment() -> None:
    """Check that this is running in this folder's .venv with the Python version pinned in .python-version."""
    setup = "See \"Set up\" in README.md for how to create it."
    version_file: Path = SCRIPT_DIR / ".python-version"
    if not version_file.is_file():
        sys.exit(f"{version_file} not found. {setup}")
    expected: str = version_file.read_text(encoding="utf-8").strip()
    actual: str = platform.python_version()
    if actual != expected:
        sys.exit(f"Run this with Python {expected} (currently {actual}). {setup}")
    venv_dir: Path = SCRIPT_DIR / ".venv"
    if Path(sys.prefix).resolve() != venv_dir.resolve():
        sys.exit(f"Run this with {venv_dir}/bin/python (currently {sys.executable}). {setup}")


def docker(*args: str) -> str:
    result = subprocess.run(["docker", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"docker {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def inspect_all(kind: str, ids: list[str]) -> list[dict[str, Any]]:
    if not ids:
        return []
    return json.loads(docker(kind, "inspect", *ids))


def normalize_path(text: str) -> str:
    """Normalize Windows UNC notation (\\\\wsl.localhost\\Ubuntu\\home\\…) so it can be compared with Linux paths."""
    return text.replace("\\", "/").lower()


def mentions_path(value: str, repo_path: str) -> bool:
    """Whether the repository path appears in the value, including a boundary right after the folder name."""
    text = normalize_path(value)
    start = text.find(repo_path)
    while start != -1:
        end = start + len(repo_path)
        if end == len(text) or text[end] in "/\"' ":
            return True
        start = text.find(repo_path, start + 1)
    return False


def iso(value: str) -> str:
    """Trim Docker's nanosecond timestamp to ISO 8601 (UTC) with second precision."""
    match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", value)
    return f"{match.group(1)}Z" if match else value


def main() -> None:
    check_environment()
    parser = argparse.ArgumentParser(description="Generate per-repository Docker relationship data")
    parser.add_argument("repo", help="Path of the repository")
    parser.add_argument("--name", help="Display name (defaults to the folder name)")
    parser.add_argument("--color", help="Legend color #rrggbb (assigned automatically by the HTML if omitted)")
    parser.add_argument("--image", action="append", default=[], help="Image used only at run time (can be given multiple times)")
    args = parser.parse_args()

    repo_dir: Path = Path(args.repo).resolve()
    if not repo_dir.is_dir():
        sys.exit(f"Folder not found: {repo_dir}")
    name: str = args.name or repo_dir.name
    if args.color and not re.fullmatch(r"#[0-9a-fA-F]{6}", args.color):
        sys.exit("--color must be in #rrggbb format")
    repo_key: str = normalize_path(str(repo_dir))

    images: dict[str, dict[str, Any]] = {
        d["Id"]: d for d in inspect_all("image", docker("images", "-a", "-q", "--no-trunc").split())
    }
    containers: list[dict[str, Any]] = inspect_all("container", docker("ps", "-a", "-q", "--no-trunc").split())

    # 1) Containers of the repository
    repo_containers: list[dict[str, Any]] = [
        c for c in containers
        if any(mentions_path(v, repo_key) for v in (c["Config"].get("Labels") or {}).values())
    ]

    # 2) Seed images
    seeds: set[str] = {c["Image"] for c in repo_containers}
    # A Dev Containers derived image is named vsc-<folder name>-<64-digit hash>[-features][-uid]:<tag>.
    # A prefix match alone would let "my" pick up vsc-my-app-…, so also check the shape after the folder name
    vsc_name: re.Pattern[str] = re.compile(
        rf"vsc-{re.escape(repo_dir.name.lower())}-[0-9a-f]{{64}}(-features)?(-uid)?(:[^:/]+)?"
    )
    vsc_images: set[str] = {
        image_id for image_id, d in images.items()
        if any(vsc_name.fullmatch(tag) for tag in d.get("RepoTags") or [])
    }
    seeds |= vsc_images
    for ref in args.image:
        seeds.add(json.loads(docker("image", "inspect", ref))[0]["Id"])

    # 3) Parent = among the images whose layer sequence is a prefix of this image's layers, the one with the most layers
    def find_parent(image_id: str) -> Optional[str]:
        layers: list[str] = images[image_id]["RootFS"]["Layers"]
        best: Optional[str] = None
        for other_id, other in images.items():
            other_layers: list[str] = other["RootFS"]["Layers"]
            if other_id != image_id and len(other_layers) < len(layers) and layers[: len(other_layers)] == other_layers:
                if best is None or len(other_layers) > len(images[best]["RootFS"]["Layers"]):
                    best = other_id
        return best

    parents: dict[str, Optional[str]] = {}
    pending: list[str] = sorted(seeds)
    while pending:
        image_id = pending.pop()
        if image_id in parents or image_id not in images:
            continue
        parents[image_id] = find_parent(image_id)
        if parents[image_id]:
            pending.append(parents[image_id])

    has_child: set[str] = {p for p in parents.values() if p}

    def role(image_id: str) -> str:
        if parents[image_id]:
            return "derived"
        return "base" if image_id in has_child else "runtime"

    # 4) Containers = those identified by labels + those started from a derived image dedicated to this repository.
    #    Containers started from a shared image (one given with --image, Compose's postgres, etc.)
    #    could belong to another repository, so only those identified by labels are included
    picked: dict[str, dict[str, Any]] = {c["Id"]: c for c in repo_containers}
    for c in containers:
        if c["Image"] in vsc_images:
            picked.setdefault(c["Id"], c)

    data: dict[str, Any] = {
        "$schema": "../schema/repo-graph.schema.json",
        "schemaVersion": 1,
        "repository": {"name": name, "path": str(repo_dir), **({"color": args.color} if args.color else {})},
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "images": [
            {
                "id": image_id,
                "tags": images[image_id].get("RepoTags") or [],
                "role": role(image_id),
                "parent": parents[image_id],
                "layers": len(images[image_id]["RootFS"]["Layers"]),
                "size": images[image_id].get("Size", 0),
                "created": iso(images[image_id]["Created"]),
            }
            for image_id in sorted(parents, key=lambda i: len(images[i]["RootFS"]["Layers"]))
        ],
        "containers": [
            {
                "id": c["Id"],
                "name": c["Name"].lstrip("/"),
                "image": c["Image"],
                "state": c["State"]["Status"],
                "created": iso(c["Created"]),
            }
            for c in sorted(picked.values(), key=lambda c: c["Name"])
        ],
    }

    # The output always goes to repos/ in this folder (no option to change it, so that only one JSON file is ever written)
    out_dir: Path = SCRIPT_DIR / "repos"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file: Path = out_dir / f"{re.sub(r'[^A-Za-z0-9._-]+', '_', name)}.json"
    out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_file} (images: {len(data['images'])}, containers: {len(data['containers'])})")


if __name__ == "__main__":
    main()
