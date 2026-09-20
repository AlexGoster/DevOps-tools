"""Deployment automation tool.

Handles git operations, dependency installation, service restarts,
and rollback capabilities for simple deployments.
"""

import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class DeployConfig:
    """Deployment configuration."""

    repository: str = "."
    branch: str = "main"
    service_name: str = "app"
    pre_deploy: Optional[str] = None
    post_deploy: Optional[str] = None
    pip_requirements: str = "requirements.txt"
    python_executable: str = "python3"
    max_retries: int = 3
    rollback_enabled: bool = True

    @classmethod
    def from_yaml(cls, path: str) -> "DeployConfig":
        """Load configuration from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        deploy_data = data.get("deploy", {})
        return cls(**{k: v for k, v in deploy_data.items() if k in cls.__dataclass_fields__})


@dataclass
class DeployResult:
    """Result of a deployment operation."""

    success: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)
    steps_completed: list[str] = field(default_factory=list)
    commit_hash: Optional[str] = None
    previous_commit: Optional[str] = None
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    rolled_back: bool = False

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "steps_completed": self.steps_completed,
            "commit_hash": self.commit_hash,
            "previous_commit": self.previous_commit,
            "duration_seconds": round(self.duration_seconds, 2),
            "errors": self.errors,
            "rolled_back": self.rolled_back,
        }


class Deployer:
    """Handles application deployment operations."""

    def __init__(self, config: DeployConfig):
        """Initialize deployer with configuration."""
        self.config = config
        self._repo_path = os.path.abspath(config.repository)

    def _run(self, cmd: list[str], cwd: Optional[str] = None, env: Optional[dict] = None) -> tuple[int, str, str]:
        """Execute shell command.

        Args:
            cmd: Command and arguments.
            cwd: Working directory.
            env: Additional environment variables.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=cwd or self._repo_path,
                env={**os.environ, **(env or {})},
            )
            return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as exc:
            return 1, "", str(exc)

    def get_current_commit(self) -> Optional[str]:
        """Get current commit hash."""
        code, out, _ = self._run(["git", "rev-parse", "HEAD"])
        return out if code == 0 else None

    def get_current_branch(self) -> Optional[str]:
        """Get current branch name."""
        code, out, _ = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return out if code == 0 else None

    def stash_changes(self) -> bool:
        """Stash any uncommitted changes."""
        code, _, _ = self._run(["git", "stash", "push", "-m", "deploy-stash"])
        return code == 0

    def restore_stash(self) -> bool:
        """Restore stashed changes."""
        code, _, _ = self._run(["git", "stash", "pop"])
        return code == 0

    def git_fetch(self) -> bool:
        """Fetch latest changes from remote."""
        code, _, stderr = self._run(["git", "fetch", "--all", "--prune"])
        if code != 0:
            raise RuntimeError(f"Git fetch failed: {stderr}")
        return True

    def git_pull(self) -> bool:
        """Pull latest changes from remote branch."""
        code, _, stderr = self._run(["git", "pull", "origin", self.config.branch])
        if code != 0:
            raise RuntimeError(f"Git pull failed: {stderr}")
        return True

    def checkout_branch(self) -> bool:
        """Checkout target branch."""
        code, _, stderr = self._run(["git", "checkout", self.config.branch])
        if code != 0:
            raise RuntimeError(f"Git checkout failed: {stderr}")
        return True

    def install_dependencies(self) -> bool:
        """Install Python dependencies from requirements file."""
        req_path = os.path.join(self._repo_path, self.config.pip_requirements)

        if not os.path.exists(req_path):
            return True

        cmd = [self.config.python_executable, "-m", "pip", "install", "-r", req_path]
        code, _, stderr = self._run(cmd)
        if code != 0:
            raise RuntimeError(f"Pip install failed: {stderr}")
        return True

    def run_script(self, script_path: str) -> bool:
        """Execute a shell script.

        Args:
            script_path: Path to the script (relative to repo or absolute).

        Returns:
            True on success.

        Raises:
            RuntimeError if script fails.
        """
        if not os.path.isabs(script_path):
            script_path = os.path.join(self._repo_path, script_path)

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")

        os.chmod(script_path, 0o755)
        code, stdout, stderr = self._run([script_path])

        if code != 0:
            raise RuntimeError(f"Script {script_path} failed (exit {code}): {stderr}")

        return True

    def restart_service(self) -> bool:
        """Restart the application service via systemctl."""
        cmd = ["systemctl", "restart", self.config.service_name]
        code, _, stderr = self._run(cmd)
        if code != 0:
            raise RuntimeError(f"Service restart failed: {stderr}")
        return True

    def check_service_running(self) -> bool:
        """Check if service is running."""
        cmd = ["systemctl", "is-active", self.config.service_name]
        code, stdout, _ = self._run(cmd)
        return code == 0 and stdout.strip() == "active"

    def rollback(self, commit_hash: str) -> bool:
        """Rollback to a previous commit.

        Args:
            commit_hash: Commit hash to rollback to.

        Returns:
            True on success.
        """
        code, _, stderr = self._run(["git", "checkout", commit_hash])
        if code != 0:
            raise RuntimeError(f"Rollback checkout failed: {stderr}")

        self.install_dependencies()
        self.restart_service()
        return True

    def deploy(self) -> DeployResult:
        """Execute full deployment workflow.

        Returns:
            DeployResult with deployment details.
        """
        start_time = time.time()
        result = DeployResult()

        try:
            # Save current commit for rollback
            result.previous_commit = self.get_current_commit()

            # Fetch latest changes
            self.git_fetch()
            result.steps_completed.append("fetch")

            # Checkout branch
            self.checkout_branch()
            result.steps_completed.append("checkout")

            # Stash local changes
            self.stash_changes()
            result.steps_completed.append("stash")

            # Pull latest
            self.git_pull()
            result.steps_completed.append("pull")

            # Pre-deploy hook
            if self.config.pre_deploy:
                self.run_script(self.config.pre_deploy)
                result.steps_completed.append("pre_deploy")

            # Install dependencies
            self.install_dependencies()
            result.steps_completed.append("install")

            # Post-deploy hook
            if self.config.post_deploy:
                self.run_script(self.config.post_deploy)
                result.steps_completed.append("post_deploy")

            # Restart service
            self.restart_service()
            result.steps_completed.append("restart")

            # Verify service
            time.sleep(2)
            if not self.check_service_running():
                raise RuntimeError("Service failed to start after restart")

            result.steps_completed.append("verify")
            result.commit_hash = self.get_current_commit()

        except Exception as exc:
            result.errors.append(str(exc))
            result.success = False

            # Attempt rollback
            if self.config.rollback_enabled and result.previous_commit:
                try:
                    self.rollback(result.previous_commit)
                    result.rolled_back = True
                except Exception as rb_exc:
                    result.errors.append(f"Rollback failed: {rb_exc}")

        finally:
            result.duration_seconds = time.time() - start_time

        return result
