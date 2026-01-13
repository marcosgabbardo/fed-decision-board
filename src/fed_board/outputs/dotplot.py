"""Dot plot generator for rate projections."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from fed_board.config import Settings, get_settings
from fed_board.models.meeting import MeetingResult, RateProjection


class DotPlotGenerator:
    """Generates Fed-style dot plot charts."""

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize the dot plot generator.

        Args:
            settings: Application settings
        """
        self.settings = settings or get_settings()

    def generate_dotplot(
        self,
        projections: list[RateProjection],
        year: int,
        output_path: Path | None = None,
    ) -> Path:
        """
        Generate a dot plot from rate projections.

        Args:
            projections: List of rate projections
            year: Base year for the chart
            output_path: Output path for the image

        Returns:
            Path to the generated image
        """
        if output_path is None:
            output_dir = self.settings.dotplots_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{year}.png"

        # Extract data
        periods = [f"{year}", f"{year + 1}", f"{year + 2}", "Longer Run"]
        data = {
            periods[0]: [],
            periods[1]: [],
            periods[2]: [],
            periods[3]: [],
        }

        for proj in projections:
            data[periods[0]].append(proj.year_end_2025)
            data[periods[1]].append(proj.year_end_2026)
            data[periods[2]].append(proj.year_end_2027)
            data[periods[3]].append(proj.longer_run)

        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 6))

        # Set up the plot style similar to Fed dot plots
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")

        # Plot dots for each period
        for i, period in enumerate(periods):
            rates = data[period]
            # Add small jitter to x position to avoid overlapping dots
            x_positions = np.random.normal(i, 0.05, len(rates))

            ax.scatter(
                x_positions,
                rates,
                s=100,
                c="#004B87",  # Fed blue
                alpha=0.7,
                edgecolors="white",
                linewidths=0.5,
                zorder=3,
            )

        # Calculate and plot medians
        medians = [np.median(data[p]) for p in periods]
        ax.plot(
            range(len(periods)),
            medians,
            "r--",
            alpha=0.5,
            linewidth=1,
            label="Median",
            zorder=2,
        )

        # Configure axes
        ax.set_xticks(range(len(periods)))
        ax.set_xticklabels(periods, fontsize=11)
        ax.set_xlabel("", fontsize=12)

        # Y-axis configuration
        all_rates = [r for rates in data.values() for r in rates]
        if all_rates:
            y_min = max(0, min(all_rates) - 0.5)
            y_max = max(all_rates) + 0.5
        else:
            y_min, y_max = 0, 6

        ax.set_ylim(y_min, y_max)
        ax.set_ylabel("Federal Funds Rate (%)", fontsize=12)

        # Grid
        ax.yaxis.grid(True, linestyle="-", alpha=0.3, zorder=1)
        ax.xaxis.grid(False)

        # Add 2% target line
        ax.axhline(y=2.0, color="green", linestyle=":", alpha=0.5, linewidth=1)
        ax.text(
            len(periods) - 0.5,
            2.05,
            "2% Target",
            fontsize=8,
            color="green",
            alpha=0.7,
        )

        # Title
        ax.set_title(
            f"FOMC Participants' Assessments of Appropriate Monetary Policy\n"
            f"Midpoint of Target Range for the Federal Funds Rate",
            fontsize=13,
            fontweight="bold",
            pad=15,
        )

        # Add legend
        ax.legend(loc="upper right", fontsize=9)

        # Add disclaimer
        fig.text(
            0.5,
            0.02,
            "AI Simulation - Fed Decision Board | Not actual Federal Reserve projections",
            ha="center",
            fontsize=8,
            style="italic",
            alpha=0.6,
        )

        # Remove top and right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Tight layout
        plt.tight_layout(rect=[0, 0.05, 1, 1])

        # Save
        plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close()

        return output_path

    def generate_from_result(
        self,
        result: MeetingResult,
        output_path: Path | None = None,
    ) -> Path | None:
        """
        Generate a dot plot from a meeting result.

        Args:
            result: Meeting result with projections
            output_path: Output path for the image

        Returns:
            Path to the generated image, or None if no projections
        """
        if not result.rate_projections:
            return None

        year = result.meeting.meeting_date.year
        return self.generate_dotplot(result.rate_projections, year, output_path)

    def generate_summary_stats(
        self,
        projections: list[RateProjection],
    ) -> dict[str, dict[str, float]]:
        """
        Generate summary statistics for projections.

        Args:
            projections: List of rate projections

        Returns:
            Dict with statistics for each period
        """
        if not projections:
            return {}

        periods = {
            "2025": [p.year_end_2025 for p in projections],
            "2026": [p.year_end_2026 for p in projections],
            "2027": [p.year_end_2027 for p in projections],
            "longer_run": [p.longer_run for p in projections],
        }

        stats = {}
        for period, rates in periods.items():
            if rates:
                stats[period] = {
                    "median": float(np.median(rates)),
                    "mean": float(np.mean(rates)),
                    "min": float(min(rates)),
                    "max": float(max(rates)),
                    "range": float(max(rates) - min(rates)),
                    "count": len(rates),
                }

        return stats
