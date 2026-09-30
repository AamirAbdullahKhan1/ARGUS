import typer

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from argus.data_loader import (
    get_incident_by_id,
    load_incidents,
)
from argus.engine.investigation import InvestigationEngine


app = typer.Typer(
    help="ARGUS: AI-Driven Incident Response Agent",
    no_args_is_help=False,
)

console = Console()


def display_banner():
    """Display the ARGUS banner."""

    banner = Text()
    banner.append("ARGUS\n", style="bold cyan")
    banner.append(
        "AI-Driven Incident Response Agent\n",
        style="bold white",
    )
    banner.append(
        "Powered by Groq | GPT-OSS-20B",
        style="dim",
    )

    console.print(
        Panel(
            banner,
            border_style="cyan",
            padding=(1, 4),
        )
    )


def handle_event(event: str, details: dict):
    """Display investigation progress in the terminal."""

    if event == "investigation_started":
        console.print(
            f"\n[bold cyan]Starting investigation:[/bold cyan] "
            f"{details.get('incident_id')}"
        )

    elif event == "decision_started":
        console.print(
            "\n[bold blue]LLM:[/bold blue] "
            "Analyzing incident and collected evidence..."
        )

    elif event == "decision_received":
        decision = details["decision"]

        console.print(
            f"[bold green]Decision:[/bold green] "
            f"{decision['action']}"
        )

        if decision["action"] == "call_tool":
            console.print(
                f"[cyan]Selected tool:[/cyan] "
                f"{decision['tool']}"
            )

        console.print(
            f"[dim]Reason: {decision.get('reason', '')}[/dim]"
        )

    elif event == "tool_started":
        console.print(
            f"\n[bold yellow]Executing tool:[/bold yellow] "
            f"{details['tool']}"
        )

        console.print(
            f"[dim]Arguments: {details['arguments']}[/dim]"
        )

    elif event == "tool_completed":
        if details["success"]:
            console.print(
                f"[bold green]✓ Tool completed:[/bold green] "
                f"{details['tool']}"
            )
        else:
            console.print(
                f"[bold red]✗ Tool failed:[/bold red] "
                f"{details['tool']}"
            )

    elif event == "investigation_completed":
        console.print(
            "\n[bold green]Investigation completed.[/bold green]"
        )

    elif event == "investigation_failed":
        console.print(
            "\n[bold red]Investigation failed:[/bold red] "
            f"{details.get('reason', 'Unknown error')}"
        )


def display_incident(incident: dict):
    """Display the incident details."""

    table = Table(
        title="Incident Details",
        show_header=False,
        border_style="cyan",
    )

    table.add_column("Field", style="bold cyan")
    table.add_column("Value")

    table.add_row(
        "Incident ID",
        str(incident.get("incident_id", "N/A")),
    )
    table.add_row(
        "Type",
        str(incident.get("event_type", "N/A")),
    )
    table.add_row(
        "Severity",
        str(incident.get("severity", "N/A")).upper(),
    )
    table.add_row(
        "Username",
        str(incident.get("username", "N/A")),
    )
    table.add_row(
        "Source IP",
        str(incident.get("source_ip", "N/A")),
    )
    table.add_row(
        "Description",
        str(incident.get("description", "N/A")),
    )

    console.print(table)


def display_report(state):
    """Display the final investigation report."""

    report = Table(
        title="Investigation Report",
        border_style="green" if state.status == "completed" else "red",
    )

    report.add_column("Field", style="bold cyan")
    report.add_column("Value")

    report.add_row("Investigation ID", state.investigation_id)
    report.add_row("Status", state.status.upper())
    report.add_row("Tool calls", str(state.tool_calls))
    report.add_row(
        "Executed tools",
        ", ".join(state.executed_tools) or "None",
    )
    report.add_row(
        "Recommendation",
        str(state.recommendation or "N/A").upper(),
    )
    report.add_row(
        "Reasoning",
        str(state.reasoning or "N/A"),
    )

    console.print()
    console.print(report)


@app.command()
def analyze(incident_id: str):
    """Analyze a specific security incident."""

    incident = get_incident_by_id(incident_id)

    if incident is None:
        console.print(
            f"[bold red]Incident not found:[/bold red] "
            f"{incident_id}"
        )
        raise typer.Exit(code=1)

    display_banner()
    display_incident(incident)

    console.print(
        "\n[bold cyan]Initializing ARGUS...[/bold cyan]"
    )

    try:
        engine = InvestigationEngine(
            event_callback=handle_event,
        )

        state = engine.investigate(incident)

        display_report(state)

        if state.status != "completed":
            raise typer.Exit(code=1)

    except typer.Exit:
        raise

    except Exception as exc:
        console.print(
            f"[bold red]Unexpected error:[/bold red] {exc}"
        )
        raise typer.Exit(code=1)


@app.command()
def start():
    """Launch the interactive ARGUS interface."""

    display_banner()

    while True:
        console.print("\n[bold cyan]Main Menu[/bold cyan]")
        console.print("1. Analyze an incident")
        console.print("2. List available incidents")
        console.print("3. Exit")

        choice = typer.prompt("Select an option")

        if choice == "1":
            incident_id = typer.prompt("Enter incident ID")
            analyze(incident_id)

        elif choice == "2":
            incidents = load_incidents()

            table = Table(title="Available Incidents")
            table.add_column("Incident ID")
            table.add_column("Type")
            table.add_column("Severity")
            table.add_column("Status")

            for incident in incidents:
                table.add_row(
                    str(incident.get("incident_id", "N/A")),
                    str(incident.get("event_type", "N/A")),
                    str(incident.get("severity", "N/A")).upper(),
                    str(incident.get("status", "N/A")),
                )

            console.print(table)

        elif choice == "3":
            console.print(
                "[bold cyan]Shutting down ARGUS. Goodbye![/bold cyan]"
            )
            break

        else:
            console.print(
                "[bold red]Invalid option. Try again.[/bold red]"
            )