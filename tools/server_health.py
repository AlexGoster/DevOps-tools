"""Server health check tool."""

import socket
import ssl
import datetime
from typing import Dict, Any
import psutil


def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def get_system_stats() -> Dict[str, Any]:
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
            "used_gb": round(psutil.disk_usage("/").used / (1024**3), 2),
            "percent": psutil.disk_usage("/").percent,
        },
        "uptime_seconds": datetime.datetime.now().timestamp() - psutil.boot_time(),
    }


def check_ssl_expiry(domain: str) -> Dict[str, Any]:
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            expires = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            days_left = (expires - datetime.datetime.now()).days
            return {
                "domain": domain,
                "issuer": dict(x[0] for x in cert["issuer"]),
                "expires": expires.isoformat(),
                "days_left": days_left,
                "valid": days_left > 0,
            }


def health_check(host: str, ports: list = None) -> Dict[str, Any]:
    if ports is None:
        ports = [80, 443, 22, 3306, 5432, 6379, 8080]

    results = {
        "host": host,
        "timestamp": datetime.datetime.now().isoformat(),
        "system": get_system_stats(),
        "ports": {},
    }

    for port in ports:
        results["ports"][port] = {
            "open": check_port(host, port),
            "service": {80: "HTTP", 443: "HTTPS", 22: "SSH", 3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis", 8080: "Alt-HTTP"}.get(port, "Unknown"),
        }

    return results
