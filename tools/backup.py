"""Automated backup tool."""

import os
import shutil
import datetime
from pathlib import Path
from typing import Optional


def backup_directory(source: str, destination: str, exclude: list = None) -> dict:
    source_path = Path(source)
    dest_path = Path(destination)

    if not source_path.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{source_path.name}_{timestamp}"
    backup_path = dest_path / backup_name

    dest_path.mkdir(parents=True, exist_ok=True)

    if source_path.is_dir():
        shutil.copytree(source, backup_path, ignore=shutil.ignore_patterns(*(exclude or [])))
    else:
        backup_path = dest_path / f"{source_path.name}_{timestamp}{source_path.suffix}"
        shutil.copy2(source, backup_path)

    size = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
    files = sum(1 for _ in backup_path.rglob("*") if _.is_file())

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
        if item.is_dir():
            mtime = datetime.datetime.fromtimestamp(item.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(item)
                removed += 1

    return removed
