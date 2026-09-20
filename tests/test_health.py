"""Tests for health checker."""

import pytest
from tools.server_health import check_port, get_system_stats


def test_check_port_open():
    result = check_port("localhost", 80)
    assert isinstance(result, bool)


def test_check_port_closed():
    result = check_port("localhost", 99999)
    assert result is False


def test_system_stats():
    stats = get_system_stats()
    assert "cpu_percent" in stats
    assert "memory" in stats
    assert "disk" in stats
    assert 0 <= stats["cpu_percent"] <= 100
