from argus.tools import account_details
import typer


from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.table import Table
from argus.reporting.history import load_history
from argus.reporting.history import get_investigation
from argus.providers.jev_provider import JevDecisionProvider

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

    elif event == "history_saved":
        console.print("[green]Investigation saved to history.[/green]")

    elif event == "history_save_failed":
        console.print(
            f"[red]Failed to save investigation: "
            f"{details.get('error')}[/red]"
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
    report.add_row("Provider", state.provider.upper())
    report.add_row("Status", state.status.upper())
    report.add_row("Tool calls", str(state.tool_calls))
    report.add_row(
        "Executed tools",
        ", ".join(state.executed_tools) or "None",
    )

    if state.risk_score is not None:
        score = state.risk_score

        if score <= 2.0:
            risk_level = "Very Low"
        elif score <= 4.0:
            risk_level = "Low"
        elif score <= 6.0:
            risk_level = "Moderate"
        elif score <= 8.0:
            risk_level = "High"
        else:
            risk_level = "Critical"

        report.add_row("Risk Score", f"{score:.1f} / 10")
        report.add_row("Risk Level", risk_level)

        report.add_row(
            "Risk Reasoning",
            str(state.risk_reasoning or "N/A"),
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

    if state.provider.lower() == "jev":
        display_jev_details(getattr(state, "jev_responses", None))

def display_jev_details(jev_responses: dict):
    """Display the raw Jev assessment and recommendation."""

    if not jev_responses:
        return

    risk_response = jev_responses.get("risk_assessment")
    recommendation_response = jev_responses.get(
        "response_recommendation"
    )

    console.print("\n[bold cyan]Jev Analysis Details[/bold cyan]")

    if risk_response:
        console.print(
            Panel(
                str(risk_response),
                title="Jev Risk Assessment Response",
                border_style="magenta",
            )
        )

    if recommendation_response:
        console.print(
            Panel(
                str(recommendation_response),
                title="Jev Response Recommendation",
                border_style="magenta",
            )
        )

@app.command()
def analyze(
    incident_id: str,
    provider: str = typer.Option(
        "groq",
        "--provider",
        "-p",
        help="Decision provider: groq or jev",
    ),
):
    """Analyze a specific security incident."""

    provider = provider.lower()

    if provider not in {"groq", "jev"}:
        console.print(
            "[bold red]Invalid provider. "
            "Choose 'groq' or 'jev'.[/bold red]"
        )
        raise typer.Exit(code=1)

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
        f"\n[bold cyan]Initializing ARGUS "
        f"with {provider.upper()}...[/bold cyan]"
    )

    try:
        jev_provider = (
            JevDecisionProvider()
            if provider == "jev"
            else None
        )

        engine = InvestigationEngine(
            jev_provider=jev_provider,
            event_callback=handle_event,
            provider_name=provider,
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
        console.print("1. Start Investigation")
        console.print("2. Help")
        console.print("3. Previous Investigations")
        console.print("4. Exit")

        choice = typer.prompt("Select an option")

        if choice == "1":
            console.print("\n[bold cyan]Select Provider[/bold cyan]")
            console.print("1. Groq")
            console.print("2. Jev")
            console.print("3. Back")

            provider_choice = typer.prompt("Select provider")

            if provider_choice == "3":
                continue

            if provider_choice == "1":
                provider = "groq"
            elif provider_choice == "2":
                provider = "jev"
            else:
                console.print(
                    "[bold red]Invalid provider option.[/bold red]"
                )
                continue

            incident_id = typer.prompt(
                "Enter incident ID"
            )

            analyze(incident_id, provider)

        elif choice == "2":
            console.print(
                Panel(
                    "[bold cyan]ARGUS Help[/bold cyan]\n\n"
                    "ARGUS is an AI-driven incident response agent "
                    "that investigates security incidents using "
                    "available investigation tools.\n\n"
                    "[bold]Providers[/bold]\n"
                    "Groq: Handles investigation and final decisions.\n"
                    "Jev: Groq orchestrates the investigation, while "
                    "Jev provides the final risk assessment and "
                    "response recommendation.\n\n"
                    "[bold]Commands[/bold]\n"
                    "argus start: Open the interactive menu.\n"
                    "argus analyze INCIDENT_ID: Analyze an incident.\n"
                    "argus history: List previous investigations.\n"
                    "argus show INVESTIGATION_ID: View a report.",
                    title="Help",
                    border_style="cyan",
                )
            )

        elif choice == "3":
            history()

            records = load_history()

            if records:
                view_choice = typer.prompt(
                    "Enter an investigation ID to view "
                    "a report, or press Enter to return",
                    default="",
                ).strip()

                if view_choice:
                    show(view_choice)

        elif choice == "4":
            console.print(
                "[bold cyan]Shutting down ARGUS. Goodbye![/bold cyan]"
            )
            break

        else:
            console.print(
                "[bold red]Invalid option. Try again.[/bold red]"
            )

@app.command()
def history():
    """Display previous investigations."""

    records = load_history()

    if not records:
        console.print("[yellow]No investigation history found.[/yellow]")
        return

    table = Table(
        title="ARGUS Investigation History",
        show_lines=True
    )

    table.add_column("Investigation ID", style="cyan")
    table.add_column("Incident ID", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Provider", style="magenta")
    table.add_column("Risk Score", justify="center")
    table.add_column("Tools", justify="center")
    table.add_column("Recommendation", style="yellow")

    for record in records:
        incident = record.get("incident", {})

        table.add_row(
            record.get("investigation_id", "N/A")[:12],
            incident.get("incident_id", "N/A"),
            record.get("status", "unknown"),
            record.get("provider", "unknown").upper(),
            (
                f"{record['risk_score']:.1f}"
                if isinstance(record.get("risk_score"), (int, float))
                else "N/A"
            ),
            str(record.get("tool_calls", 0)),
            record.get("recommendation") or "N/A"
        )

    console.print(table)

@app.command()
def show(investigation_id: str):
    """Display a detailed investigation report."""

    record = get_investigation(investigation_id)

    if record is None:
        console.print(
            f"[red]Investigation '{investigation_id}' not found.[/red]"
        )
        raise typer.Exit(code=1)

    incident = record.get("incident", {})

    console.print()
    console.print(
        Panel(
            f"[bold cyan]Investigation ID:[/] "
            f"{record.get('investigation_id', 'N/A')}\n"
            f"[bold]Status:[/] {record.get('status', 'unknown')}\n"
            f"[bold]Incident ID:[/] "
            f"{incident.get('incident_id', 'N/A')}",
            title="ARGUS Investigation Report",
            border_style="cyan"
        )
    )

    incident_table = Table(title="Incident Details")
    incident_table.add_column("Field", style="cyan")
    incident_table.add_column("Value")

    for key, value in incident.items():
        incident_table.add_row(str(key), str(value))

    console.print(incident_table)

    console.print("\n[bold cyan]Investigation Timeline[/bold cyan]")
    console.print(f"Started: {record.get('started_at', 'N/A')}")
    console.print(f"Completed: {record.get('completed_at', 'N/A')}")
    console.print("\n[bold cyan]Executed Tools[/bold cyan]")

    tools = record.get("executed_tools", [])

    if tools:
        for index, tool in enumerate(tools, start=1):
            console.print(f"{index}. {tool}")
    else:
        console.print("[yellow]No tools were executed.[/yellow]")

    console.print("\n[bold cyan]Collected Evidence[/bold cyan]")

    evidence = record.get("evidence", [])

    if evidence:
        for item in evidence:
            console.print(
                Panel(
                    str(item.get("result", {})),
                    title=f"Tool: {item.get('tool', 'Unknown')}",
                    subtitle=f"Time: {item.get('timestamp', 'N/A')}",
                    border_style="blue"
                )
            )
    else:
        console.print("[yellow]No evidence collected.[/yellow]")

    # Risk Assessment
    console.print("\n[bold cyan]Risk Assessment[/bold cyan]")
    risk_score = record.get("risk_score")
    risk_reasoning = record.get("risk_reasoning")

    if risk_score is not None:
        if risk_score <= 2:
            risk_level = "Very Low"
        elif risk_score <= 4:
            risk_level = "Low"
        elif risk_score <= 6:
            risk_level = "Moderate"
        elif risk_score <= 8:
            risk_level = "High"
        else:
            risk_level = "Critical"

        risk_panel = (
            f"[bold]Risk Score:[/] {risk_score}/10\n"
            f"[bold]Risk Level:[/] {risk_level}\n\n"
            f"[bold]Assessment:[/]\n"
            f"{risk_reasoning or 'No explanation available.'}"
        )

        console.print(
            Panel(
                risk_panel,
                title="Risk Analysis",
                border_style="red"
            )
        )
    else:
        console.print(
            "[yellow]No risk assessment available.[/yellow]"
        )

    # Final Recommendation
    console.print("\n[bold cyan]Final Recommendation[/bold cyan]")
    console.print(
        Panel(
            f"[bold yellow]{record.get('recommendation') or 'N/A'}[/bold yellow]\n\n"
            f"{record.get('reasoning') or 'No explanation available.'}",
            border_style="yellow"
        )
    )
    if record.get("provider", "").lower() == "jev":
        display_jev_details(record.get("jev_responses"))
