import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from tools.backup import backup_directory, cleanup_old_backups
from tools import server_health
from datetime import UTC, datetime, timedelta


def test_file_backup_and_repeat(tmp_path):
    source = tmp_path / "file.txt"
    source.write_text("hello")
    one = backup_directory(str(source), str(tmp_path / "backups"))
    two = backup_directory(str(source), str(tmp_path / "backups"))
    assert one["files"] == 1 and two["files"] == 1
    assert Path(one["backup"]).read_text() == "hello"
    assert one["backup"] != two["backup"]


def test_nested_backup_rejected_before_writing(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(ValueError):
        backup_directory(str(source), str(source / "backup"))
    assert not (source / "backup").exists()


def test_cleanup_preserves_unrelated_directory(tmp_path):
    unrelated = tmp_path / "important"
    unrelated.mkdir()
    backup = tmp_path / "source_20200101_120000"
    backup.mkdir()
    old = time.time() - 60 * 24 * 3600
    for path in (unrelated, backup):
        os.utime(path, (old, old))
    assert cleanup_old_backups(str(tmp_path), keep_days=30) == 1
    assert unrelated.exists()


def test_documented_cli_entrypoint(tmp_path):
    script = Path(__file__).parents[1] / "tools/cli.py"
    result = subprocess.run([sys.executable, str(script), "health", "--host", "127.0.0.1",
                             "--ports", "invalid"], cwd=tmp_path,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_certificate_with_less_than_one_day_is_still_valid(monkeypatch):
    class Socket:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def getpeercert(self):
            return {"notAfter": (datetime.now(UTC) + timedelta(hours=1)).strftime("%b %d %H:%M:%S %Y GMT"),
                    "issuer": ((('organizationName', 'Local test CA'),),)}
    class Context:
        def wrap_socket(self, *args, **kwargs):
            return Socket()
    monkeypatch.setattr(server_health.socket, "create_connection", lambda *args, **kwargs: Socket())
    monkeypatch.setattr(server_health.ssl, "create_default_context", lambda: Context())
    result = server_health.check_ssl_expiry("local.invalid")
    assert result["valid"] is True
    assert result["days_left"] == 0
