import typer
from argus.data_loader import get_incident_by_id

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

app = typer.Typer(
    name="argus",
    help="ARGUS: AI-Driven Incident Response Agent",
    no_args_is_help=True,
)

console = Console()


@app.command()
def start():
    """Start the ARGUS interactive agent."""

    title = Text("ARGUS", style="bold cyan", justify="center")
    subtitle = Text(
        "AI-Driven Incident Response Agent",
        style="white",
        justify="center",
    )

    console.print()
    console.print(
        Panel(
            f"{title}\n{subtitle}",
            border_style="cyan",
            padding=(1, 4),
        )
    )

    console.print("[cyan][*][/cyan] Initializing ARGUS...")

    console.print("[green][+][/green] CLI initialized")
    console.print("[green][+][/green] Ready for user input")

    console.print()
    console.print(
        "[bold green]ARGUS is online.[/bold green]"
    )
    console.print("Type [cyan]help[/cyan] for commands.")
    console.print("Type [cyan]exit[/cyan] to quit.")
    console.print()

    while True:
        try:
            command = console.input("[bold cyan]argus > [/bold cyan]")
            command = command.strip()

            if not command:
                continue

            if command.lower() in ("exit", "quit"):
                console.print("[yellow]Shutting down ARGUS...[/yellow]")
                break

            elif command.lower() == "help":
                console.print(
                    Panel(
                        "analyze <incident_id>  Investigate an incident\n"
                        "history                View past investigations\n"
                        "show <incident_id>     View an investigation report\n"
                        "help                   Show available commands\n"
                        "exit                   Exit ARGUS",
                        title="Available Commands",
                        border_style="cyan",
                    )
                )

            else:
                console.print(
                    "[yellow]Command not implemented yet.[/yellow]"
                )

        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down ARGUS...[/yellow]")
            break

        except EOFError:
            console.print("\n[yellow]Shutting down ARGUS...[/yellow]")
            break

@app.command()
def analyze(incident_id: str):
    """Retrieve an incident by its ID."""

    try:
        incident = get_incident_by_id(incident_id)

    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[bold red]Dataset error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    if incident is None:
        console.print(
            f"[bold red]Incident {incident_id} not found.[/bold red]"
        )
        raise typer.Exit(code=1)

    console.print()
    console.print(
        Panel(
            f"[bold cyan]Incident ID:[/bold cyan] {incident['incident_id']}\n"
            f"[bold cyan]Type:[/bold cyan] {incident['event_type']}\n"
            f"[bold cyan]Username:[/bold cyan] {incident['username']}\n"
            f"[bold cyan]Source IP:[/bold cyan] {incident['source_ip']}\n"
            f"[bold cyan]Timestamp:[/bold cyan] {incident['timestamp']}\n"
            f"[bold cyan]Severity:[/bold cyan] {incident['severity']}\n"
            f"[bold cyan]Status:[/bold cyan] {incident['status']}\n\n"
            f"[bold cyan]Description:[/bold cyan]\n"
            f"{incident['description']}",
            title="Incident Details",
            border_style="cyan",
        )
    )

if __name__ == "__main__":
    app()