"""Main CLI entry point."""

import click
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def cli():
    """DevOps Tools - Server administration utilities"""
    pass


@cli.command()
@click.option("--host", default="localhost", help="Host to check")
@click.option("--ports", default="80,443,22", help="Comma-separated ports")
def health(host, ports):
    """Check server health"""
    from tools.server_health import health_check
    try:
        port_list = [int(p.strip()) for p in ports.split(",")]
    except ValueError:
        raise click.BadParameter("Ports must be integers", param_hint="--ports") from None
    if any(not 1 <= port <= 65535 for port in port_list):
        raise click.BadParameter("Ports must be between 1 and 65535", param_hint="--ports")
    result = health_check(host, port_list)

    table = Table(title=f"Health Check: {host}")
    table.add_column("Port", style="cyan")
    table.add_column("Service", style="green")
    table.add_column("Status", style="bold")

    for port, info in result["ports"].items():
        status = "[green]OPEN[/green]" if info["open"] else "[red]CLOSED[/red]"
        table.add_row(str(port), info["service"], status)

    console.print(table)
    console.print(f"CPU: {result['system']['cpu_percent']}%")
    console.print(f"Memory: {result['system']['memory']['percent']}%")


@cli.command()
@click.option("--source", required=True, help="Source directory")
@click.option("--dest", required=True, help="Backup destination")
def backup(source, dest):
    """Create backup"""
    from tools.backup import backup_directory
    result = backup_directory(source, dest)
    console.print(f"[green]Backup created: {result['backup']}[/green]")
    console.print(f"Size: {result['size_mb']} MB, Files: {result['files']}")


@cli.command()
@click.option("--file", required=True, help="Log file path")
@click.option("--errors-only", is_flag=True, help="Show only errors")
def logs(file, errors_only):
    """Analyze log file"""
    from tools.log_analyzer import LogAnalyzer
    analyzer = LogAnalyzer(file)
    summary = analyzer.summary()

    console.print(f"Total requests: {summary['total_requests']}")
    console.print(f"Error rate: {summary['error_rate']}%")

    if errors_only:
        errors = analyzer.filter_errors()
        console.print(f"Errors: {len(errors)}")


@cli.command()
@click.option("--domain", required=True, help="Domain to check")
def ssl(domain):
    """Check SSL certificate"""
    from tools.server_health import check_ssl_expiry
    result = check_ssl_expiry(domain)
    color = "green" if result["valid"] else "red"
    console.print(f"SSL for {domain}: [{color}]expires {result['days_left']} days[/{color}]")


if __name__ == "__main__":
    cli()
