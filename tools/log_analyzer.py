"""Log file analyzer."""

import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional


class LogAnalyzer:
    LOG_PATTERN = re.compile(
        r'(?P<ip>[\d.]+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<path>\S+) HTTP/[\d.]+" (?P<status>\d+) (?P<size>\d+)'
    )

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.entries: List[dict] = []
        self._parse()

    def _parse(self) -> None:
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = self.LOG_PATTERN.match(line)
                if match:
                    self.entries.append(match.groupdict())

    def summary(self) -> Dict:
        statuses = Counter(e["status"] for e in self.entries)
        paths = Counter(e["path"] for e in self.entries)
        ips = Counter(e["ip"] for e in self.entries)

        return {
            "total_requests": len(self.entries),
            "status_codes": dict(statuses),
            "top_paths": paths.most_common(10),
            "top_ips": ips.most_common(10),
            "error_rate": round(
                sum(1 for e in self.entries if e["status"].startswith("5")) / max(len(self.entries), 1) * 100, 2
            ),
        }

    def filter_errors(self) -> List[dict]:
        return [e for e in self.entries if e["status"].startswith(("4", "5"))]

    def filter_by_path(self, path_pattern: str) -> List[dict]:
        pattern = re.compile(path_pattern)
        return [e for e in self.entries if pattern.match(e["path"])]
