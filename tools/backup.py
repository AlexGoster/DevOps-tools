"""Automated backup tool."""

import os
import shutil
import datetime
import re
from pathlib import Path
from typing import Optional


def backup_directory(source: str, destination: str, exclude: list = None) -> dict:
    source_path = Path(source)
    dest_path = Path(destination)

    if not source_path.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    if source_path.is_dir() and dest_path.resolve().is_relative_to(source_path.resolve()):
        raise ValueError("Backup destination must be outside the source directory")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_name = f"{source_path.name}_{timestamp}"
    backup_path = dest_path / backup_name

    dest_path.mkdir(parents=True, exist_ok=True)

    if source_path.is_dir():
        shutil.copytree(source, backup_path, ignore=shutil.ignore_patterns(*(exclude or [])))
    else:
        backup_path = dest_path / f"{source_path.stem}_{timestamp}{source_path.suffix}"
        shutil.copy2(source, backup_path)

    copied_files = [backup_path] if backup_path.is_file() else [
        path for path in backup_path.rglob("*") if path.is_file()
    ]
    size = sum(path.stat().st_size for path in copied_files)
    files = len(copied_files)

    return {
        "source": str(source_path),
        "backup": str(backup_path),
        "size_mb": round(size / (1024 * 1024), 2),
        "files": files,
        "timestamp": timestamp,
    }


def cleanup_old_backups(destination: str, keep_days: int = 30) -> int:
    dest_path = Path(destination)
    cutoff = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    removed = 0

    for item in dest_path.iterdir():
        if item.is_dir() and not item.is_symlink() and re.fullmatch(
            r".+_\d{8}_\d{6}(?:_\d{6})?", item.name
        ):
            mtime = datetime.datetime.fromtimestamp(item.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(item)
                removed += 1

    return removed
