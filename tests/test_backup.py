"""Tests for backup tool."""

import pytest
import tempfile
from pathlib import Path
from tools.backup import backup_directory


def test_backup_directory():
    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
        (Path(src) / "test.txt").write_text("hello")
        result = backup_directory(src, dst)
        assert result["files"] == 1
        assert result["size_mb"] >= 0
