from unittest.mock import Mock

import paramiko
import pytest

from utils.ssh import SSHClient


def test_ssh_loads_known_hosts_and_rejects_unknown_servers(monkeypatch):
    native = Mock()
    monkeypatch.setattr(paramiko, "SSHClient", lambda: native)
    SSHClient("test.invalid")
    native.load_system_host_keys.assert_called_once_with()
    native.load_host_keys.assert_not_called()
    policy = native.set_missing_host_key_policy.call_args.args[0]
    assert isinstance(policy, paramiko.RejectPolicy)
    key = Mock()
    key.get_fingerprint.return_value = b"dummy-fingerprint"
    key.get_name.return_value = "ssh-ed25519"
    with pytest.raises(paramiko.SSHException, match="not found in known_hosts"):
        policy.missing_host_key(native, "test.invalid", key)


def test_ssh_uses_explicit_known_hosts_and_client_key(monkeypatch):
    native = Mock()
    monkeypatch.setattr(paramiko, "SSHClient", lambda: native)
    with SSHClient("test.invalid", port=2222, username="test", key_path="dummy-key",
                   known_hosts_path="dummy-known-hosts"):
        pass
    native.load_host_keys.assert_called_once_with("dummy-known-hosts")
    native.connect.assert_called_once_with(hostname="test.invalid", port=2222,
                                           username="test", key_filename="dummy-key")
    native.close.assert_called_once_with()
