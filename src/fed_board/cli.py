"""Command-line interface for Fed Decision Board."""

import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from fed_board import __version__

app = typer.Typer(
    name="fed-board",
    help="AI-powered FOMC meeting simulator using Claude",
    add_completion=True,
)
console = Console()


# Pricing per 1M tokens (as of Jan 2025)
MODEL_PRICING = {
    "claude-opus-4-5-20251101": {"input": 15.00, "output": 75.00, "name": "Opus 4.5"},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00, "name": "Sonnet 4"},
    "claude-haiku-3-5-20241022": {"input": 0.80, "output": 4.00, "name": "Haiku 3.5"},
}

# Estimated tokens per member in a simulation
TOKENS_PER_MEMBER = {
    "input": 3500,   # Deliberation + vote + projection prompts
    "output": 1800,  # Responses
}


def estimate_cost(model: str, num_members: int) -> dict:
    """
    Estimate the cost of running a simulation.

    Returns dict with input_tokens, output_tokens, and estimated_cost_usd.
    """
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["claude-opus-4-5-20251101"])

    input_tokens = TOKENS_PER_MEMBER["input"] * num_members
    output_tokens = TOKENS_PER_MEMBER["output"] * num_members

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    return {
        "model_name": pricing["name"],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "num_members": num_members,
    }


def confirm_cost(cost_estimate: dict, skip_confirm: bool = False) -> bool:
    """
    Display cost estimate and ask for confirmation.

    Returns True if user confirms, False otherwise.
    """
    if skip_confirm:
        return True

    console.print()
    console.print(
        Panel(
            f"[bold yellow]Cost Estimate[/bold yellow]\n\n"
            f"Model: [cyan]{cost_estimate['model_name']}[/cyan]\n"
            f"Members: [cyan]{cost_estimate['num_members']}[/cyan]\n\n"
            f"Estimated tokens:\n"
            f"  Input:  ~{cost_estimate['input_tokens']:,} tokens\n"
            f"  Output: ~{cost_estimate['output_tokens']:,} tokens\n\n"
            f"Estimated cost:\n"
            f"  Input:  ${cost_estimate['input_cost']:.3f}\n"
            f"  Output: ${cost_estimate['output_cost']:.3f}\n"
            f"  [bold]Total:  ${cost_estimate['total_cost']:.2f}[/bold]\n\n"
            f"[dim]* Actual costs may vary based on response length[/dim]",
            title="Anthropic API Cost",
            border_style="yellow",
        )
    )

    confirm = typer.confirm(
        "Do you want to proceed with this simulation?",
        default=False,
    )

    return confirm


class OutputFormat(str, Enum):
    """Output format options."""

    MD = "md"
    PDF = "pdf"
    ALL = "all"


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"Fed Decision Board v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Fed Decision Board - AI-powered FOMC meeting simulator."""
    pass


@app.command()
def simulate(
    month: Annotated[
        str,
        typer.Option(
            "--month",
            "-m",
            help="Meeting month in YYYY-MM format",
        ),
    ],
    members: Annotated[
        Optional[str],
        typer.Option(
            "--members",
            help="Comma-separated list of member short names (e.g., powell,waller,bowman)",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help="Show detailed output",
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip cost confirmation prompt",
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            "-d",
            help="Enable debug mode with API call logging",
        ),
    ] = False,
    concurrency: Annotated[
        int,
        typer.Option(
            "--concurrency",
            "-c",
            help="Number of concurrent API calls (1=sequential, default)",
        ),
    ] = 1,
) -> None:
    """Run an FOMC meeting simulation."""
    import logging
    import os

    from fed_board.agents.base import FOMCAgent
    from fed_board.agents.orchestrator import MeetingOrchestrator
    from fed_board.agents.personas import get_member_by_name, get_voting_members
    from fed_board.config import get_settings

    # Set API concurrency level
    FOMCAgent.set_max_concurrent_calls(concurrency)

    # Enable debug mode via environment variable
    if debug:
        os.environ["FED_BOARD_DEBUG"] = "1"
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )

    # Validate month format
    try:
        year = datetime.strptime(month, "%Y-%m").year
    except ValueError:
        console.print("[red]Error: Month must be in YYYY-MM format[/red]")
        raise typer.Exit(1)

    # Parse members and count them
    member_list = None
    if members:
        member_list = [m.strip().lower() for m in members.split(",")]
        # Validate member names
        valid_members = [get_member_by_name(m) for m in member_list]
        valid_members = [m for m in valid_members if m is not None]
        num_members = len(valid_members)
        if num_members == 0:
            console.print("[red]Error: No valid member names provided[/red]")
            raise typer.Exit(1)
    else:
        # Count voting members for the year
        num_members = len(get_voting_members(year))

    settings = get_settings()
    settings.ensure_directories()

    mode_str = "sequential" if concurrency == 1 else f"{concurrency} concurrent"
    console.print(
        Panel(
            f"[bold]FOMC Meeting Simulation[/bold]\n\n"
            f"Month: {month}\n"
            f"Members: {members if members else f'All voting members ({num_members})'}\n"
            f"Mode: {mode_str}",
            title="Fed Decision Board",
            border_style="blue",
        )
    )

    # Estimate cost and ask for confirmation
    cost_estimate = estimate_cost(settings.anthropic_model, num_members)
    if not confirm_cost(cost_estimate, skip_confirm=yes):
        console.print("[yellow]Simulation cancelled.[/yellow]")
        raise typer.Exit(0)

    def progress_callback(message: str, percentage: float) -> None:
        """Update progress display."""
        if verbose:
            console.print(f"  {message}")

    orchestrator = MeetingOrchestrator(
        settings=settings,
        progress_callback=progress_callback if verbose else None,
        debug=debug,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Running simulation...", total=None)

        try:
            result = asyncio.run(orchestrator.run_meeting(month, member_list))
        except Exception as e:
            console.print(f"[red]Error running simulation: {e}[/red]")
            raise typer.Exit(1)

        progress.update(task, completed=True)

    # Display results
    decision = result.decision
    console.print()

    # Economic indicators panel
    if result.economic_indicators:
        from fed_board.data.indicators import Trend

        ind = result.economic_indicators
        inf = ind.inflation
        emp = ind.employment
        act = ind.activity
        mkt = ind.markets
        exp = ind.expectations
        trends = ind.trends

        def fmt(v: float | None, suffix: str = "", signed: bool = False) -> str:
            if v is None:
                return "[dim]N/A[/dim]"
            if signed:
                return f"{v:+.1f}{suffix}"
            return f"{v:.1f}{suffix}"

        def trend_arrow(key: str) -> str:
            """Get colored trend arrow for a key."""
            if key not in trends:
                return ""
            t = trends[key]
            if t.trend == Trend.RISING:
                return " [green]↑[/green]"
            elif t.trend == Trend.FALLING:
                return " [red]↓[/red]"
            elif t.trend == Trend.STABLE:
                return " [yellow]→[/yellow]"
            return ""

        def prev_vals(key: str) -> str:
            """Get previous values for context."""
            if key not in trends:
                return ""
            t = trends[key]
            vals = []
            if t.previous is not None:
                vals.append(f"{t.previous:.1f}")
            if t.two_periods_ago is not None:
                vals.append(f"{t.two_periods_ago:.1f}")
            if vals:
                return f" [dim](prev: {', '.join(vals)})[/dim]"
            return ""

        indicators_text = (
            f"[bold cyan]Inflation[/bold cyan]\n"
            f"  Core PCE: {fmt(inf.core_pce_yoy, '%')}{trend_arrow('core_pce_yoy')}{prev_vals('core_pce_yoy')}\n"
            f"  CPI: {fmt(inf.cpi_yoy, '%')}{trend_arrow('cpi_yoy')}{prev_vals('cpi_yoy')}  |  Core CPI: {fmt(inf.core_cpi_yoy, '%')}{trend_arrow('core_cpi_yoy')}\n\n"
            f"[bold cyan]Labor Market[/bold cyan]\n"
            f"  Unemployment: {fmt(emp.unemployment_rate, '%')}{trend_arrow('unemployment_rate')}{prev_vals('unemployment_rate')}\n"
            f"  Wage Growth: {fmt(emp.wage_growth_yoy, '%')}{trend_arrow('wage_growth_yoy')}  |  Participation: {fmt(emp.labor_force_participation, '%')}{trend_arrow('labor_force_participation')}\n\n"
            f"[bold cyan]Activity[/bold cyan]\n"
            f"  GDP Growth: {fmt(act.gdp_growth, '%', signed=True)}{trend_arrow('gdp_growth')}{prev_vals('gdp_growth')}\n"
            f"  Retail Sales: {fmt(act.retail_sales_mom, '%', signed=True)}{trend_arrow('retail_sales_mom')}  |  Industrial: {fmt(act.industrial_production_yoy, '%', signed=True)}{trend_arrow('industrial_production_yoy')}\n\n"
            f"[bold cyan]Markets[/bold cyan]\n"
            f"  Fed Funds: {mkt.current_rate_range or '[dim]N/A[/dim]'}  |  10Y: {fmt(mkt.treasury_10y, '%')}{trend_arrow('treasury_10y')}  |  2Y: {fmt(mkt.treasury_2y, '%')}{trend_arrow('treasury_2y')}\n\n"
            f"[bold cyan]Expectations[/bold cyan]\n"
            f"  5Y Breakeven: {fmt(exp.breakeven_5y, '%')}{trend_arrow('breakeven_5y')}  |  10Y Breakeven: {fmt(exp.breakeven_10y, '%')}{trend_arrow('breakeven_10y')}  |  Sentiment: {fmt(exp.michigan_sentiment)}{trend_arrow('michigan_sentiment')}"
        )

        console.print(
            Panel(
                indicators_text,
                title=f"Economic Indicators (as of {ind.as_of_date})",
                border_style="cyan",
            )
        )
        console.print()

    # Decision panel
    if decision.rate_change_bps > 0:
        action = f"[red]RAISE[/red] by {decision.rate_change_bps} bps"
    elif decision.rate_change_bps < 0:
        action = f"[green]CUT[/green] by {abs(decision.rate_change_bps)} bps"
    else:
        action = "[yellow]HOLD[/yellow]"

    console.print(
        Panel(
            f"[bold]Decision:[/bold] {action}\n"
            f"[bold]New Target Range:[/bold] {decision.rate_range_str}\n"
            f"[bold]Vote:[/bold] {result.vote_summary}",
            title="Meeting Result",
            border_style="green" if decision.rate_change_bps <= 0 else "red",
        )
    )

    # Vote table
    if verbose:
        table = Table(title="Individual Votes")
        table.add_column("Member", style="cyan")
        table.add_column("Vote", style="green")
        table.add_column("Preferred Rate")

        for vote in result.votes:
            vote_str = "[green]For[/green]" if vote.vote_for_decision else "[red]Against[/red]"
            table.add_row(vote.member_name, vote_str, f"{vote.preferred_rate:.2f}%")

        console.print(table)

    # Save result
    filepath = asyncio.run(orchestrator.save_result(result))
    console.print(f"\n[dim]Simulation saved to: {filepath}[/dim]")


@app.command()
def minutes(
    month: Annotated[
        str,
        typer.Option(
            "--month",
            "-m",
            help="Meeting month in YYYY-MM format",
        ),
    ],
    format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            help="Output format",
        ),
    ] = OutputFormat.MD,
) -> None:
    """Generate meeting minutes from a simulation."""
    from fed_board.agents.orchestrator import MeetingOrchestrator
    from fed_board.config import get_settings
    from fed_board.outputs.minutes import MinutesGenerator
    from fed_board.outputs.pdf import PDFGenerator

    settings = get_settings()
    orchestrator = MeetingOrchestrator(settings=settings)

    # Load simulation result
    result = orchestrator.load_result(month)
    if result is None:
        console.print(f"[red]No simulation found for {month}. Run 'simulate' first.[/red]")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Generating minutes...", total=None)

        if format == OutputFormat.ALL:
            pdf_gen = PDFGenerator(settings)
            outputs = pdf_gen.generate_all_formats(result)
            progress.update(task, completed=True)
            console.print("[green]Generated minutes in all formats:[/green]")
            for fmt, path in outputs.items():
                console.print(f"  - {fmt}: {path}")
        elif format == OutputFormat.PDF:
            pdf_gen = PDFGenerator(settings)
            path = pdf_gen.generate_pdf(result)
            progress.update(task, completed=True)
            console.print(f"[green]Generated PDF: {path}[/green]")
        else:
            min_gen = MinutesGenerator(settings)
            path = min_gen.save_markdown(result)
            progress.update(task, completed=True)
            console.print(f"[green]Generated Markdown: {path}[/green]")


@app.command()
def dotplot(
    year: Annotated[
        int,
        typer.Option(
            "--year",
            "-y",
            help="Year for the dot plot",
        ),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output file path",
        ),
    ] = None,
) -> None:
    """Generate a dot plot from simulations."""
    from fed_board.agents.orchestrator import MeetingOrchestrator
    from fed_board.config import get_settings
    from fed_board.outputs.dotplot import DotPlotGenerator

    settings = get_settings()
    orchestrator = MeetingOrchestrator(settings=settings)

    # Find simulations for the year
    all_projections = []
    for month_num in range(1, 13):
        month_str = f"{year}-{month_num:02d}"
        result = orchestrator.load_result(month_str)
        if result and result.rate_projections:
            all_projections.extend(result.rate_projections)

    if not all_projections:
        console.print(f"[red]No projections found for {year}. Run simulations first.[/red]")
        raise typer.Exit(1)

    dotplot_gen = DotPlotGenerator(settings)
    output_path = dotplot_gen.generate_dotplot(all_projections, year, output)

    console.print(f"[green]Generated dot plot: {output_path}[/green]")

    # Show summary stats
    stats = dotplot_gen.generate_summary_stats(all_projections)
    table = Table(title="Rate Projection Summary")
    table.add_column("Period")
    table.add_column("Median")
    table.add_column("Range")
    table.add_column("Count")

    for period, s in stats.items():
        table.add_row(
            period,
            f"{s['median']:.2f}%",
            f"{s['min']:.2f}% - {s['max']:.2f}%",
            str(s["count"]),
        )

    console.print(table)


@app.command()
def dissents(
    year: Annotated[
        Optional[int],
        typer.Option(
            "--year",
            "-y",
            help="Filter by year",
        ),
    ] = None,
    member: Annotated[
        Optional[str],
        typer.Option(
            "--member",
            "-m",
            help="Filter by member name",
        ),
    ] = None,
) -> None:
    """Analyze dissenting votes."""
    from fed_board.agents.orchestrator import MeetingOrchestrator
    from fed_board.config import get_settings

    settings = get_settings()
    orchestrator = MeetingOrchestrator(settings=settings)

    # Collect dissents
    all_dissents = []
    years_to_check = [year] if year else range(2020, 2030)

    for y in years_to_check:
        for month_num in range(1, 13):
            month_str = f"{y}-{month_num:02d}"
            result = orchestrator.load_result(month_str)
            if result and result.dissent_analyses:
                for d in result.dissent_analyses:
                    if member is None or member.lower() in d.dissenter_name.lower():
                        all_dissents.append((month_str, d))

    if not all_dissents:
        console.print("[yellow]No dissents found matching criteria.[/yellow]")
        return

    table = Table(title="Dissent Analysis")
    table.add_column("Meeting")
    table.add_column("Member")
    table.add_column("Stance")
    table.add_column("Majority")
    table.add_column("Preferred")

    for meeting, d in all_dissents:
        table.add_row(
            meeting,
            d.dissenter_name,
            d.dissenter_stance,
            d.majority_decision,
            d.dissenter_preference,
        )

    console.print(table)

    if len(all_dissents) > 0:
        console.print(f"\n[bold]Total dissents: {len(all_dissents)}[/bold]")


@app.command()
def history(
    year: Annotated[
        Optional[int],
        typer.Option(
            "--year",
            "-y",
            help="Filter by year",
        ),
    ] = None,
    export: Annotated[
        Optional[str],
        typer.Option(
            "--export",
            help="Export format (csv)",
        ),
    ] = None,
    detailed: Annotated[
        bool,
        typer.Option(
            "--detailed",
            help="Include additional columns in CSV export",
        ),
    ] = False,
    votes: Annotated[
        bool,
        typer.Option(
            "--votes",
            help="Export individual votes instead of summary",
        ),
    ] = False,
) -> None:
    """View simulation history."""
    from fed_board.agents.orchestrator import MeetingOrchestrator
    from fed_board.config import get_settings

    settings = get_settings()
    orchestrator = MeetingOrchestrator(settings=settings)

    # Find all simulations
    simulations = []
    years_to_check = [year] if year else range(2020, 2030)

    for y in years_to_check:
        for month_num in range(1, 13):
            month_str = f"{y}-{month_num:02d}"
            result = orchestrator.load_result(month_str)
            if result:
                simulations.append(result)

    if not simulations:
        console.print("[yellow]No simulations found.[/yellow]")
        return

    table = Table(title="Simulation History")
    table.add_column("Meeting")
    table.add_column("Decision")
    table.add_column("Rate Range")
    table.add_column("Vote")
    table.add_column("Model")

    for result in simulations:
        decision = result.decision
        if decision.rate_change_bps > 0:
            dec_str = f"[red]+{decision.rate_change_bps}bps[/red]"
        elif decision.rate_change_bps < 0:
            dec_str = f"[green]{decision.rate_change_bps}bps[/green]"
        else:
            dec_str = "[yellow]HOLD[/yellow]"

        table.add_row(
            result.meeting.month_str,
            dec_str,
            decision.rate_range_str,
            result.vote_summary,
            result.model_used.split("-")[0] if result.model_used else "N/A",
        )

    console.print(table)

    if export == "csv":
        import csv

        if votes:
            # Export individual votes
            csv_path = settings.data_dir / "votes.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Meeting", "Member", "Vote", "Preferred_Rate",
                    "Is_Dissent", "Dissent_Reason", "Statement"
                ])
                for r in simulations:
                    for v in r.votes:
                        writer.writerow([
                            r.meeting.month_str,
                            v.member_name,
                            "for" if v.vote_for_decision else "against",
                            f"{v.preferred_rate:.2f}",
                            v.is_dissent,
                            v.dissent_reason or "",
                            v.statement[:200] if v.statement else "",
                        ])
            console.print(f"\n[green]Exported {sum(len(r.votes) for r in simulations)} votes to: {csv_path}[/green]")

        elif detailed:
            # Detailed export with additional columns
            csv_path = settings.data_dir / "history_detailed.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Meeting", "Decision", "Change_BPS", "Rate_Lower", "Rate_Upper",
                    "Vote_For", "Vote_Against", "Dissenters", "Model", "Created_At"
                ])
                for r in simulations:
                    d = r.decision
                    dissenters = ", ".join(v.member_name for v in r.votes if v.is_dissent)
                    writer.writerow([
                        r.meeting.month_str,
                        d.rate_decision.value,
                        d.rate_change_bps,
                        d.new_rate_lower,
                        d.new_rate_upper,
                        r.vote_count_for,
                        r.vote_count_against,
                        dissenters,
                        r.model_used,
                        r.created_at.isoformat() if r.created_at else "",
                    ])
            console.print(f"\n[green]Exported to: {csv_path}[/green]")

        else:
            # Basic export
            csv_path = settings.data_dir / "history.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Meeting", "Decision", "Rate_Lower", "Rate_Upper", "Vote", "Model"])
                for r in simulations:
                    d = r.decision
                    writer.writerow([
                        r.meeting.month_str,
                        d.rate_decision.value,
                        d.new_rate_lower,
                        d.new_rate_upper,
                        r.vote_summary,
                        r.model_used,
                    ])
            console.print(f"\n[green]Exported to: {csv_path}[/green]")


@app.command()
def members() -> None:
    """List all FOMC members and their profiles."""
    from fed_board.agents.personas import FOMC_MEMBERS

    table = Table(title="FOMC Members")
    table.add_column("Name", style="cyan")
    table.add_column("Short Name")
    table.add_column("Role")
    table.add_column("Stance")
    table.add_column("Bank")

    for member in FOMC_MEMBERS:
        stance_color = {
            "hawk": "red",
            "dove": "green",
            "neutral": "yellow",
        }.get(str(member.stance), "white")

        table.add_row(
            member.name,
            member.short_name,
            str(member.role.value),
            f"[{stance_color}]{member.stance}[/{stance_color}]",
            member.bank[:30] + "..." if len(member.bank) > 30 else member.bank,
        )

    console.print(table)


@app.command()
def estimate(
    members: Annotated[
        Optional[str],
        typer.Option(
            "--members",
            help="Comma-separated list of member short names",
        ),
    ] = None,
    year: Annotated[
        int,
        typer.Option(
            "--year",
            "-y",
            help="Year for voting member count",
        ),
    ] = 2025,
) -> None:
    """Estimate API cost for a simulation without running it."""
    from fed_board.agents.personas import get_member_by_name, get_voting_members
    from fed_board.config import get_settings

    settings = get_settings()

    # Count members
    if members:
        member_list = [m.strip().lower() for m in members.split(",")]
        valid_members = [get_member_by_name(m) for m in member_list]
        valid_members = [m for m in valid_members if m is not None]
        num_members = len(valid_members)
    else:
        num_members = len(get_voting_members(year))

    cost_estimate = estimate_cost(settings.anthropic_model, num_members)

    console.print(
        Panel(
            f"[bold]Cost Estimate[/bold]\n\n"
            f"Model: [cyan]{cost_estimate['model_name']}[/cyan] ({settings.anthropic_model})\n"
            f"Members: [cyan]{cost_estimate['num_members']}[/cyan]\n\n"
            f"[bold]Estimated tokens:[/bold]\n"
            f"  Input:  ~{cost_estimate['input_tokens']:,} tokens\n"
            f"  Output: ~{cost_estimate['output_tokens']:,} tokens\n\n"
            f"[bold]Estimated cost:[/bold]\n"
            f"  Input:  ${cost_estimate['input_cost']:.3f}\n"
            f"  Output: ${cost_estimate['output_cost']:.3f}\n"
            f"  [bold green]Total:  ${cost_estimate['total_cost']:.2f}[/bold green]\n\n"
            f"[dim]* Actual costs may vary based on response length\n"
            f"* Use --members to estimate for specific members[/dim]",
            title="Anthropic API Cost Estimate",
            border_style="green",
        )
    )

    # Show pricing table
    console.print()
    table = Table(title="Model Pricing (per 1M tokens)")
    table.add_column("Model")
    table.add_column("Input")
    table.add_column("Output")
    table.add_column("Est. Cost (12 members)")

    for model_id, pricing in MODEL_PRICING.items():
        est = estimate_cost(model_id, 12)
        current = " [green](current)[/green]" if model_id == settings.anthropic_model else ""
        table.add_row(
            f"{pricing['name']}{current}",
            f"${pricing['input']:.2f}",
            f"${pricing['output']:.2f}",
            f"${est['total_cost']:.2f}",
        )

    console.print(table)


@app.command("config")
def config_cmd(
    action: Annotated[
        str,
        typer.Argument(help="Action: 'show' or 'set'"),
    ] = "show",
    key: Annotated[
        Optional[str],
        typer.Argument(help="Config key to set"),
    ] = None,
    value: Annotated[
        Optional[str],
        typer.Argument(help="Value to set"),
    ] = None,
) -> None:
    """Show or set configuration."""
    from fed_board.config import get_settings

    if action == "show":
        settings = get_settings()
        console.print(
            Panel(
                f"[bold]Configuration[/bold]\n\n"
                f"Anthropic API Key: {'*' * 8}...{settings.anthropic_api_key[-4:]}\n"
                f"FRED API Key: {'*' * 8}...{settings.fred_api_key[-4:]}\n"
                f"Model: {settings.anthropic_model}\n"
                f"Data Directory: {settings.data_dir}\n"
                f"Log Level: {settings.log_level}",
                title="Current Settings",
                border_style="blue",
            )
        )
    elif action == "set":
        if not key or not value:
            console.print("[red]Usage: fed-board config set <key> <value>[/red]")
            raise typer.Exit(1)
        console.print(
            "[yellow]Configuration is set via environment variables or .env file.[/yellow]"
        )
        console.print(f"To set {key.upper()}, add to your .env file: {key.upper()}={value}")
    else:
        console.print(f"[red]Unknown action: {action}. Use 'show' or 'set'.[/red]")


@app.command("cache")
def cache_cmd(
    action: Annotated[
        str,
        typer.Argument(help="Action: 'clear' or 'stats'"),
    ] = "stats",
) -> None:
    """Manage FRED data cache."""
    from fed_board.config import get_settings
    from fed_board.data.fred import FREDClient

    settings = get_settings()
    fred_client = FREDClient(settings=settings)

    if action == "clear":
        count = fred_client.clear_cache()
        console.print(f"[green]Cleared {count} cached files.[/green]")
    elif action == "stats":
        stats = fred_client.get_cache_stats()
        console.print(
            Panel(
                f"[bold]Cache Statistics[/bold]\n\n"
                f"Directory: {stats['cache_dir']}\n"
                f"Total files: {stats['total_files']}\n"
                f"Total size: {stats['total_size_bytes'] / 1024:.1f} KB\n"
                f"Valid entries: {stats['valid_entries']}\n"
                f"Expired entries: {stats['expired_entries']}",
                title="FRED Cache",
                border_style="cyan",
            )
        )
    else:
        console.print(f"[red]Unknown action: {action}. Use 'clear' or 'stats'.[/red]")


@app.command()
def impact(
    month: Annotated[
        Optional[str],
        typer.Option(
            "--month",
            "-m",
            help="Meeting month (YYYY-MM). Default: most recent simulation.",
        ),
    ] = None,
) -> None:
    """Display estimated market impact from a simulation."""
    from fed_board.agents.orchestrator import MeetingOrchestrator
    from fed_board.config import get_settings

    settings = get_settings()
    orchestrator = MeetingOrchestrator(settings=settings)

    # Find the most recent simulation if no month specified
    if month is None:
        simulations_dir = settings.simulations_dir
        if not simulations_dir.exists():
            console.print("[red]No simulations found. Run 'simulate' first.[/red]")
            raise typer.Exit(1)

        sim_files = sorted(simulations_dir.glob("*.json"), reverse=True)
        if not sim_files:
            console.print("[red]No simulations found. Run 'simulate' first.[/red]")
            raise typer.Exit(1)

        month = sim_files[0].stem  # e.g., "2025-01"

    result = orchestrator.load_result(month)
    if result is None:
        console.print(f"[red]No simulation found for {month}. Run 'simulate' first.[/red]")
        raise typer.Exit(1)

    if result.market_impact is None:
        console.print(f"[yellow]No market impact data available for {month}.[/yellow]")
        raise typer.Exit(1)

    impact_data = result.market_impact
    decision = result.decision

    # Build impact table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Asset", style="cyan")
    table.add_column("Expected Δ", justify="right")
    table.add_column("Direction")

    # S&P 500
    sp_change = impact_data.sp500_change_pct
    sp_dir = "[green]▲ Bullish[/green]" if sp_change > 0 else "[red]▼ Bearish[/red]" if sp_change < 0 else "[yellow]→ Neutral[/yellow]"
    table.add_row("S&P 500", f"{sp_change:+.2f}%", sp_dir)

    # 10Y Treasury
    t10_change = impact_data.treasury_10y_change_bps
    t10_dir = "[red]▲ Yields rise[/red]" if t10_change > 0 else "[green]▼ Yields fall[/green]" if t10_change < 0 else "[yellow]→ Unchanged[/yellow]"
    table.add_row("10Y Treasury", f"{t10_change:+d} bps", t10_dir)

    # 2Y Treasury
    t2_change = impact_data.treasury_2y_change_bps
    t2_dir = "[red]▲ Yields rise[/red]" if t2_change > 0 else "[green]▼ Yields fall[/green]" if t2_change < 0 else "[yellow]→ Unchanged[/yellow]"
    table.add_row("2Y Treasury", f"{t2_change:+d} bps", t2_dir)

    # Dollar Index
    dxy_change = impact_data.dxy_change_pct
    dxy_dir = "[cyan]▲ Strengthening[/cyan]" if dxy_change > 0 else "[magenta]▼ Weakening[/magenta]" if dxy_change < 0 else "[yellow]→ Stable[/yellow]"
    table.add_row("Dollar (DXY)", f"{dxy_change:+.2f}%", dxy_dir)

    # Decision summary
    if decision.rate_change_bps > 0:
        decision_str = f"[red]+{decision.rate_change_bps} bps[/red] (RAISE)"
    elif decision.rate_change_bps < 0:
        decision_str = f"[green]{decision.rate_change_bps} bps[/green] (CUT)"
    else:
        decision_str = "[yellow]0 bps[/yellow] (HOLD)"

    # Print header panel
    console.print()
    console.print(Panel(
        f"[bold]Decision:[/bold] {decision_str}\n"
        f"[bold]Rate:[/bold] {decision.previous_rate_lower:.2f}%-{decision.previous_rate_upper:.2f}% → {decision.new_rate_lower:.2f}%-{decision.new_rate_upper:.2f}%",
        title=f"Market Impact Estimate — {month}",
        border_style="blue",
    ))

    # Print impact table
    console.print()
    console.print(table)

    # Rationale
    if impact_data.rationale:
        console.print()
        console.print(Panel(
            impact_data.rationale,
            title="Rationale",
            border_style="dim",
        ))


@app.command()
def changes(
    month: Annotated[
        Optional[str],
        typer.Option(
            "--month",
            "-m",
            help="Compare to this simulation (YYYY-MM). Default: most recent.",
        ),
    ] = None,
) -> None:
    """Show economic indicator changes since a simulation."""
    from fed_board.agents.orchestrator import MeetingOrchestrator
    from fed_board.config import get_settings
    from fed_board.data.fred import FREDClient

    settings = get_settings()
    orchestrator = MeetingOrchestrator(settings=settings)
    fred_client = FREDClient(settings=settings)

    # Find the most recent simulation if no month specified
    if month is None:
        simulations_dir = settings.simulations_dir
        if not simulations_dir.exists():
            console.print("[red]No simulations found. Run 'simulate' first.[/red]")
            raise typer.Exit(1)

        sim_files = sorted(simulations_dir.glob("*.json"), reverse=True)
        if not sim_files:
            console.print("[red]No simulations found. Run 'simulate' first.[/red]")
            raise typer.Exit(1)

        month = sim_files[0].stem

    result = orchestrator.load_result(month)
    if result is None:
        console.print(f"[red]No simulation found for {month}. Run 'simulate' first.[/red]")
        raise typer.Exit(1)

    if result.economic_indicators is None:
        console.print(f"[yellow]No economic indicator data available for {month}.[/yellow]")
        raise typer.Exit(1)

    old_indicators = result.economic_indicators

    # Fetch current indicators
    console.print("[dim]Fetching current economic data from FRED...[/dim]")
    try:
        current_indicators = asyncio.run(fred_client.get_economic_indicators())
    except Exception as e:
        console.print(f"[red]Error fetching FRED data: {e}[/red]")
        raise typer.Exit(1)

    # Calculate days since simulation
    days_ago = (datetime.now().date() - result.created_at.date()).days

    # Key indicators to compare
    key_indicators = [
        ("Core PCE YoY", "inflation", "core_pce_yoy", "pp", False),  # Lower is better
        ("Unemployment", "employment", "unemployment_rate", "pp", False),  # Lower is better (but watch for too low)
        ("Fed Funds Rate", "markets", "fed_funds_rate", "pp", None),  # Neutral
        ("10Y Treasury", "markets", "treasury_10y", "bps", None),  # Neutral
        ("2Y Treasury", "markets", "treasury_2y", "bps", None),  # Neutral
        ("S&P 500", "markets", "sp500", "%", True),  # Higher is better
        ("Consumer Sentiment", "expectations", "consumer_sentiment", "pts", True),  # Higher is better
    ]

    table = Table(show_header=True, header_style="bold")
    table.add_column("Indicator", style="cyan")
    table.add_column("Then", justify="right")
    table.add_column("Now", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("Trend")

    notable_changes = []

    for name, category, field, fmt, higher_is_better in key_indicators:
        old_cat = getattr(old_indicators, category)
        new_cat = getattr(current_indicators, category)
        old_val = getattr(old_cat, field, None)
        new_val = getattr(new_cat, field, None)

        if old_val is None or new_val is None:
            continue

        delta = new_val - old_val

        # Format values and delta
        if fmt == "bps":
            old_str = f"{old_val:.2f}%"
            new_str = f"{new_val:.2f}%"
            delta_bps = delta * 100
            delta_str = f"{delta_bps:+.0f} bps"
            is_significant = abs(delta_bps) >= 10
        elif fmt == "pp":
            old_str = f"{old_val:.1f}%"
            new_str = f"{new_val:.1f}%"
            delta_str = f"{delta:+.2f} pp"
            is_significant = abs(delta) >= 0.1
        elif fmt == "%":
            old_str = f"{old_val:,.0f}"
            new_str = f"{new_val:,.0f}"
            pct_change = ((new_val - old_val) / old_val) * 100 if old_val != 0 else 0
            delta_str = f"{pct_change:+.1f}%"
            is_significant = abs(pct_change) >= 1
        else:  # pts
            old_str = f"{old_val:.1f}"
            new_str = f"{new_val:.1f}"
            delta_str = f"{delta:+.1f}"
            is_significant = abs(delta) >= 1

        # Determine trend arrow and color
        if delta > 0:
            trend = "↑"
            if higher_is_better is True:
                color = "green"
            elif higher_is_better is False:
                color = "red"
            else:
                color = "yellow"
        elif delta < 0:
            trend = "↓"
            if higher_is_better is True:
                color = "red"
            elif higher_is_better is False:
                color = "green"
            else:
                color = "yellow"
        else:
            trend = "→"
            color = "dim"

        trend_str = f"[{color}]{trend}[/{color}]"
        delta_colored = f"[{color}]{delta_str}[/{color}]"

        table.add_row(name, old_str, new_str, delta_colored, trend_str)

        # Track notable changes
        if is_significant:
            direction = "up" if delta > 0 else "down"
            notable_changes.append(f"{name} {direction}")

    # Print header
    console.print()
    console.print(Panel(
        f"[bold]Comparing to simulation:[/bold] {month}\n"
        f"[bold]Simulation date:[/bold] {result.created_at.strftime('%Y-%m-%d')} ({days_ago} days ago)\n"
        f"[bold]Current data as of:[/bold] {datetime.now().strftime('%Y-%m-%d')}",
        title="Economic Changes",
        border_style="cyan",
    ))

    # Print table
    console.print()
    console.print(table)

    # Print notable changes
    if notable_changes:
        console.print()
        console.print(f"[yellow]Notable:[/yellow] {', '.join(notable_changes[:3])}")


def _stance_bar(score: int, width: int = 10) -> str:
    """Create a visual bar showing hawk/dove position."""
    # Score -100 to +100 maps to empty (dove) to full (hawk)
    normalized = (score + 100) / 2  # 0 to 100
    filled = int((normalized / 100) * width)
    return "█" * filled + "░" * (width - filled)


def _calculate_stance_score(
    preferred_rate: float,
    decision_rate_lower: float,
    decision_rate_upper: float,
) -> int:
    """Calculate stance score for a single vote (-100 to +100)."""
    actual_mid = (decision_rate_lower + decision_rate_upper) / 2
    delta_bps = (preferred_rate - actual_mid) * 100
    # Normalize: max delta of 50 bps = score of 100
    return int(max(-100, min(100, delta_bps * 2)))


@app.command()
def stance(
    member: Annotated[
        Optional[str],
        typer.Option(
            "--member",
            "-m",
            help="Filter by member name (short name like 'powell', 'bowman')",
        ),
    ] = None,
    year: Annotated[
        Optional[int],
        typer.Option(
            "--year",
            "-y",
            help="Filter by year",
        ),
    ] = None,
) -> None:
    """Show member voting stance analysis based on simulation history."""
    from fed_board.agents.orchestrator import MeetingOrchestrator
    from fed_board.agents.personas import FOMC_MEMBERS, get_member_by_name
    from fed_board.config import get_settings
    from fed_board.models.member import Stance

    settings = get_settings()
    orchestrator = MeetingOrchestrator(settings=settings)

    # Collect all simulations
    simulations = []
    years_to_check = [year] if year else range(2020, 2030)

    for y in years_to_check:
        for month_num in range(1, 13):
            month_str = f"{y}-{month_num:02d}"
            result = orchestrator.load_result(month_str)
            if result:
                simulations.append(result)

    if not simulations:
        console.print("[yellow]No simulations found. Run 'simulate' first.[/yellow]")
        raise typer.Exit(1)

    # Build member stance data
    member_data: dict[str, dict] = {}

    for sim in simulations:
        for vote in sim.votes:
            name = vote.member_name
            if name not in member_data:
                # Find the member in FOMC_MEMBERS
                fomc_member = None
                for m in FOMC_MEMBERS:
                    if m.name == name:
                        fomc_member = m
                        break

                member_data[name] = {
                    "member": fomc_member,
                    "votes": [],
                    "decisions": [],
                    "scores": [],
                    "dissents": 0,
                    "months": [],
                }

            # Calculate score for this vote
            score = _calculate_stance_score(
                vote.preferred_rate,
                sim.decision.new_rate_lower,
                sim.decision.new_rate_upper,
            )

            member_data[name]["votes"].append(vote)
            member_data[name]["decisions"].append(sim.decision)
            member_data[name]["scores"].append(score)
            member_data[name]["months"].append(sim.meeting.month_str)
            if vote.is_dissent:
                member_data[name]["dissents"] += 1

    # Filter by member if specified
    if member:
        # Try to find the member
        target_member = get_member_by_name(member)
        if target_member is None:
            console.print(f"[red]Member '{member}' not found.[/red]")
            console.print("[dim]Use 'fed-board members' to see available members.[/dim]")
            raise typer.Exit(1)

        # Find in our collected data
        target_name = target_member.name
        if target_name not in member_data:
            console.print(f"[yellow]No voting data found for {target_name}.[/yellow]")
            raise typer.Exit(1)

        # Single member detailed view
        data = member_data[target_name]
        fomc_member = data["member"]
        avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        total_votes = len(data["votes"])

        # Stance description
        if avg_score > 20:
            stance_desc = "hawkish"
        elif avg_score < -20:
            stance_desc = "dovish"
        else:
            stance_desc = "neutral"

        # Header info
        stance_color = {
            Stance.HAWK: "red",
            Stance.DOVE: "green",
            Stance.NEUTRAL: "yellow",
        }.get(fomc_member.stance if fomc_member else Stance.NEUTRAL, "white")

        baseline_str = f"[{stance_color}]{fomc_member.stance.value.upper()}[/{stance_color}]" if fomc_member else "Unknown"
        role_str = fomc_member.role.value if fomc_member else "Unknown"

        console.print()
        console.print(Panel(
            f"[bold]Role:[/bold] {role_str}\n"
            f"[bold]Baseline Stance:[/bold] {baseline_str}\n"
            f"[bold]Calculated Score:[/bold] {avg_score:+.0f} ({stance_desc})\n"
            f"[bold]Total Votes:[/bold] {total_votes}\n"
            f"[bold]Dissents:[/bold] {data['dissents']}",
            title=target_name,
            border_style="cyan",
        ))

        # Voting history table
        table = Table(title="Voting History", show_header=True, header_style="bold")
        table.add_column("Meeting", style="cyan")
        table.add_column("Decision", justify="center")
        table.add_column("Preferred", justify="right")
        table.add_column("Dissent", justify="center")
        table.add_column("Score", justify="right")

        for i, (vote, decision, score, month) in enumerate(zip(
            data["votes"], data["decisions"], data["scores"], data["months"]
        )):
            # Format decision
            if decision.rate_change_bps > 0:
                dec_str = f"RAISE +{decision.rate_change_bps}"
            elif decision.rate_change_bps < 0:
                dec_str = f"CUT {decision.rate_change_bps}"
            else:
                dec_str = "HOLD"

            dissent_str = "[red]Yes[/red]" if vote.is_dissent else "[green]No[/green]"

            # Score color
            if score > 20:
                score_str = f"[red]{score:+d}[/red]"
            elif score < -20:
                score_str = f"[green]{score:+d}[/green]"
            else:
                score_str = f"[yellow]{score:+d}[/yellow]"

            table.add_row(
                month,
                dec_str,
                f"{vote.preferred_rate:.2f}%",
                dissent_str,
                score_str,
            )

        console.print()
        console.print(table)

        # Key concerns from member profile
        if fomc_member and fomc_member.key_concerns:
            console.print()
            concerns_text = "\n".join(f"  • {c}" for c in fomc_member.key_concerns[:5])
            console.print(Panel(
                concerns_text,
                title="Key Concerns",
                border_style="dim",
            ))

    else:
        # All members view
        # Sort by month range
        all_months = sorted(set(m for d in member_data.values() for m in d["months"]))
        first_month = all_months[0] if all_months else "N/A"
        last_month = all_months[-1] if all_months else "N/A"

        console.print()
        console.print(Panel(
            f"Based on {len(simulations)} simulation(s) ({first_month} to {last_month})\n\n"
            f"[dim]Score: -100 (dove) to +100 (hawk)[/dim]",
            title="FOMC Stance Tracker",
            border_style="cyan",
        ))

        # Table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Member", style="cyan", width=22)
        table.add_column("Baseline", justify="center")
        table.add_column("Score", justify="right")
        table.add_column("Votes", justify="right")
        table.add_column("Dissents", justify="right")
        table.add_column("Position")

        # Sort by score (hawks first)
        sorted_members = sorted(
            member_data.items(),
            key=lambda x: sum(x[1]["scores"]) / len(x[1]["scores"]) if x[1]["scores"] else 0,
            reverse=True,
        )

        for name, data in sorted_members:
            fomc_member = data["member"]
            avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
            total_votes = len(data["votes"])

            # Baseline stance color
            stance_color = {
                Stance.HAWK: "red",
                Stance.DOVE: "green",
                Stance.NEUTRAL: "yellow",
            }.get(fomc_member.stance if fomc_member else Stance.NEUTRAL, "white")

            baseline = f"[{stance_color}]{fomc_member.stance.value.capitalize()}[/{stance_color}]" if fomc_member else "?"

            # Score color
            if avg_score > 20:
                score_str = f"[red]{avg_score:+.0f}[/red]"
            elif avg_score < -20:
                score_str = f"[green]{avg_score:+.0f}[/green]"
            else:
                score_str = f"[yellow]{avg_score:+.0f}[/yellow]"

            # Dissents
            dissent_str = str(data["dissents"]) if data["dissents"] > 0 else "-"

            # Visual bar
            bar = _stance_bar(int(avg_score))

            # Truncate long names
            display_name = name[:20] + "..." if len(name) > 22 else name

            table.add_row(
                display_name,
                baseline,
                score_str,
                str(total_votes),
                dissent_str,
                bar,
            )

        console.print()
        console.print(table)


@app.command()
def compare(
    month: Annotated[
        Optional[str],
        typer.Option(
            "--month",
            "-m",
            help="Meeting month to compare (YYYY-MM)",
        ),
    ] = None,
    year: Annotated[
        Optional[int],
        typer.Option(
            "--year",
            "-y",
            help="Compare all meetings in a year",
        ),
    ] = None,
) -> None:
    """Compare simulation results with actual Fed decisions."""
    from fed_board.agents.orchestrator import MeetingOrchestrator
    from fed_board.config import get_settings
    from fed_board.data.fomc_schedule import (
        get_fomc_meeting_date,
        get_fomc_months,
        is_fomc_month,
    )
    from fed_board.data.fred import FREDClient
    from fed_board.data.historical_decisions import (
        get_actual_decision,
    )

    settings = get_settings()
    orchestrator = MeetingOrchestrator(settings=settings)
    fred_client = FREDClient(settings=settings)

    if year is not None:
        # Compare all meetings in a year
        fomc_months = get_fomc_months(year)
        if not fomc_months:
            console.print(f"[red]No FOMC meeting data for {year}.[/red]")
            raise typer.Exit(1)

        results = []
        for m in fomc_months:
            meeting_date = get_fomc_meeting_date(m)
            if meeting_date and meeting_date > datetime.now().date():
                continue  # Skip future meetings

            sim_result = orchestrator.load_result(m)
            if sim_result is None:
                continue

            actual = asyncio.run(get_actual_decision(fred_client, meeting_date))
            if actual is None:
                continue

            # Calculate accuracy
            sim_decision = sim_result.decision
            direction_match = (
                (sim_decision.rate_change_bps > 0 and actual.change_bps > 0) or
                (sim_decision.rate_change_bps < 0 and actual.change_bps < 0) or
                (sim_decision.rate_change_bps == 0 and actual.change_bps == 0)
            )
            magnitude_error = abs(sim_decision.rate_change_bps - actual.change_bps)

            results.append({
                "month": m,
                "sim_type": sim_decision.rate_decision.value,
                "sim_bps": sim_decision.rate_change_bps,
                "actual_type": actual.decision_type,
                "actual_bps": actual.change_bps,
                "direction_match": direction_match,
                "magnitude_error": magnitude_error,
            })

        if not results:
            console.print(f"[yellow]No simulations found for {year} FOMC meetings.[/yellow]")
            raise typer.Exit(1)

        # Display summary table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Meeting", style="cyan")
        table.add_column("Simulation", justify="center")
        table.add_column("Actual", justify="center")
        table.add_column("Match", justify="center")
        table.add_column("Error", justify="right")

        direction_correct = 0
        total_error = 0

        for r in results:
            # Format simulation result
            if r["sim_bps"] > 0:
                sim_str = f"RAISE +{r['sim_bps']}"
            elif r["sim_bps"] < 0:
                sim_str = f"CUT {r['sim_bps']}"
            else:
                sim_str = "HOLD"

            # Format actual result
            if r["actual_bps"] > 0:
                actual_str = f"RAISE +{r['actual_bps']}"
            elif r["actual_bps"] < 0:
                actual_str = f"CUT {r['actual_bps']}"
            else:
                actual_str = "HOLD"

            # Match indicator
            if r["direction_match"]:
                match_str = "[green]✓[/green]"
                direction_correct += 1
            else:
                match_str = "[red]✗[/red]"

            # Error
            error_str = f"{r['magnitude_error']} bps" if r["magnitude_error"] > 0 else "-"
            total_error += r["magnitude_error"]

            table.add_row(r["month"], sim_str, actual_str, match_str, error_str)

        console.print()
        console.print(Panel(
            f"Comparing {len(results)} FOMC meetings in {year}",
            title=f"Accuracy Summary — {year}",
            border_style="cyan",
        ))
        console.print()
        console.print(table)

        # Summary statistics
        accuracy_pct = (direction_correct / len(results)) * 100 if results else 0
        avg_error = total_error / len(results) if results else 0

        console.print()
        console.print(f"[bold]Direction Accuracy:[/bold] {direction_correct}/{len(results)} ({accuracy_pct:.0f}%)")
        console.print(f"[bold]Average Error:[/bold] {avg_error:.1f} bps")

    else:
        # Compare single meeting
        if month is None:
            # Use most recent simulation
            simulations_dir = settings.simulations_dir
            if not simulations_dir.exists():
                console.print("[red]No simulations found. Run 'simulate' first.[/red]")
                raise typer.Exit(1)

            sim_files = sorted(simulations_dir.glob("*.json"), reverse=True)
            if not sim_files:
                console.print("[red]No simulations found. Run 'simulate' first.[/red]")
                raise typer.Exit(1)

            month = sim_files[0].stem

        # Check if it's an FOMC month
        if not is_fomc_month(month):
            console.print(f"[yellow]No FOMC meeting in {month}.[/yellow]")
            year_num = int(month.split("-")[0])
            available_months = get_fomc_months(year_num)
            if available_months:
                console.print(f"[dim]FOMC meetings in {year_num}: {', '.join(available_months)}[/dim]")
            raise typer.Exit(1)

        meeting_date = get_fomc_meeting_date(month)

        # Check if meeting is in the future
        if meeting_date and meeting_date > datetime.now().date():
            console.print(f"[yellow]Cannot compare: {month} meeting hasn't occurred yet.[/yellow]")
            console.print(f"[dim]Meeting date: {meeting_date.strftime('%B %d, %Y')}[/dim]")
            raise typer.Exit(1)

        # Load simulation
        sim_result = orchestrator.load_result(month)
        if sim_result is None:
            console.print(f"[red]No simulation found for {month}. Run 'simulate --month {month}' first.[/red]")
            raise typer.Exit(1)

        # Fetch actual decision
        console.print("[dim]Fetching actual Fed decision from FRED...[/dim]")
        actual = asyncio.run(get_actual_decision(fred_client, meeting_date))

        if actual is None:
            console.print(f"[yellow]Could not fetch actual Fed decision for {month}.[/yellow]")
            raise typer.Exit(1)

        sim_decision = sim_result.decision

        # Calculate metrics
        direction_match = (
            (sim_decision.rate_change_bps > 0 and actual.change_bps > 0) or
            (sim_decision.rate_change_bps < 0 and actual.change_bps < 0) or
            (sim_decision.rate_change_bps == 0 and actual.change_bps == 0)
        )
        magnitude_error = abs(sim_decision.rate_change_bps - actual.change_bps)
        range_match = (
            abs(sim_decision.new_rate_lower - actual.rate_lower) < 0.01 and
            abs(sim_decision.new_rate_upper - actual.rate_upper) < 0.01
        )

        # Calculate score
        score = 0
        if direction_match:
            score += 50
        if magnitude_error == 0:
            score += 30
        elif magnitude_error <= 25:
            score += 15
        if range_match:
            score += 20

        # Build comparison table
        table = Table(show_header=True, header_style="bold")
        table.add_column("", style="dim")
        table.add_column("Simulation", justify="center")
        table.add_column("Actual Fed", justify="center")
        table.add_column("Match", justify="center")

        # Decision type
        sim_type = sim_decision.rate_decision.value
        actual_type = actual.decision_type
        type_match = "[green]✓[/green]" if sim_type == actual_type else "[red]✗[/red]"
        table.add_row("Decision", sim_type, actual_type, type_match)

        # Change in bps
        sim_change = f"{sim_decision.rate_change_bps:+d} bps"
        actual_change = f"{actual.change_bps:+d} bps"
        change_match = "[green]✓[/green]" if magnitude_error == 0 else f"[yellow]{magnitude_error} bps off[/yellow]"
        table.add_row("Change", sim_change, actual_change, change_match)

        # New range
        sim_range = sim_decision.rate_range_str
        actual_range = actual.rate_range_str
        range_match_str = "[green]✓[/green]" if range_match else "[red]✗[/red]"
        table.add_row("New Range", sim_range, actual_range, range_match_str)

        # Header panel
        console.print()
        console.print(Panel(
            f"[bold]FOMC Meeting:[/bold] {meeting_date.strftime('%B %d, %Y')}",
            title=f"Simulation vs Actual — {month}",
            border_style="blue",
        ))

        # Table
        console.print()
        console.print(table)

        # Score
        console.print()
        if score >= 80:
            score_color = "green"
        elif score >= 50:
            score_color = "yellow"
        else:
            score_color = "red"
        console.print(f"[bold {score_color}]Accuracy Score: {score}%[/bold {score_color}]")


if __name__ == "__main__":
    app()
