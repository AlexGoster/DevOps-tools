"""SSH connection helper."""

import paramiko
from typing import Optional


class SSHClient:
    def __init__(self, host: str, port: int = 22, username: str = "", key_path: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.key_path = key_path
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self) -> None:
        kwargs = {"hostname": self.host, "port": self.port, "username": self.username}
        if self.key_path:
            kwargs["key_filename"] = self.key_path
        self.client.connect(**kwargs)

    def execute(self, command: str) -> tuple:
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode(), stdout.channel.recv_exit_status()

    def close(self) -> None:
        self.client.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
