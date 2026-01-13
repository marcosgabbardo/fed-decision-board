"""Fetch actual Fed decisions from FRED API."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fed_board.data.fred import FREDClient


@dataclass
class ActualDecision:
    """Represents an actual Fed decision."""

    meeting_date: date
    rate_lower: float
    rate_upper: float
    previous_lower: float
    previous_upper: float
    change_bps: int
    decision_type: str  # "RAISE", "CUT", "HOLD"

    @property
    def rate_range_str(self) -> str:
        """Format the rate range as a string."""
        return f"{self.rate_lower:.2f}%-{self.rate_upper:.2f}%"

    @property
    def previous_range_str(self) -> str:
        """Format the previous rate range as a string."""
        return f"{self.previous_lower:.2f}%-{self.previous_upper:.2f}%"

    @property
    def change_str(self) -> str:
        """Format the change as a string."""
        if self.change_bps > 0:
            return f"+{self.change_bps} bps"
        elif self.change_bps < 0:
            return f"{self.change_bps} bps"
        else:
            return "0 bps"


async def get_actual_decision(
    fred_client: "FREDClient",
    meeting_date: date,
) -> ActualDecision | None:
    """
    Fetch the actual Fed decision from FRED for a given meeting date.

    This queries the DFEDTARU (upper) and DFEDTARL (lower) series to find
    the target rate before and after the meeting.

    Args:
        fred_client: FREDClient instance
        meeting_date: The date of the FOMC meeting

    Returns:
        ActualDecision with the rate change, or None if data unavailable
    """
    # Query range: a few days before to a few days after the meeting
    start_date = meeting_date - timedelta(days=7)
    end_date = meeting_date + timedelta(days=5)

    try:
        # Fetch upper and lower target rates
        upper_obs = await fred_client.get_series(
            "DFEDTARU",
            start_date=start_date,
            end_date=end_date,
            limit=50,
            sort_order="asc",
            use_cache=True,
        )
        lower_obs = await fred_client.get_series(
            "DFEDTARL",
            start_date=start_date,
            end_date=end_date,
            limit=50,
            sort_order="asc",
            use_cache=True,
        )

        if not upper_obs or not lower_obs:
            return None

        # Find the rate before and after the meeting date
        # The rate changes are announced on the meeting date
        prev_upper = None
        prev_lower = None
        new_upper = None
        new_lower = None

        for obs in upper_obs:
            obs_date = date.fromisoformat(obs["date"])
            value = float(obs["value"]) if obs["value"] != "." else None

            if value is None:
                continue

            if obs_date < meeting_date:
                prev_upper = value
            elif obs_date >= meeting_date and new_upper is None:
                new_upper = value

        for obs in lower_obs:
            obs_date = date.fromisoformat(obs["date"])
            value = float(obs["value"]) if obs["value"] != "." else None

            if value is None:
                continue

            if obs_date < meeting_date:
                prev_lower = value
            elif obs_date >= meeting_date and new_lower is None:
                new_lower = value

        # If we couldn't find the rates, return None
        if any(v is None for v in [prev_upper, prev_lower, new_upper, new_lower]):
            return None

        # Calculate the change in basis points
        # Use midpoint comparison
        prev_mid = (prev_upper + prev_lower) / 2
        new_mid = (new_upper + new_lower) / 2
        change_bps = int(round((new_mid - prev_mid) * 100))

        # Determine decision type
        if change_bps > 0:
            decision_type = "RAISE"
        elif change_bps < 0:
            decision_type = "CUT"
        else:
            decision_type = "HOLD"

        return ActualDecision(
            meeting_date=meeting_date,
            rate_lower=new_lower,
            rate_upper=new_upper,
            previous_lower=prev_lower,
            previous_upper=prev_upper,
            change_bps=change_bps,
            decision_type=decision_type,
        )

    except Exception:
        return None


async def get_actual_decisions_for_year(
    fred_client: "FREDClient",
    year: int,
) -> list[ActualDecision]:
    """
    Fetch all actual Fed decisions for a given year.

    Args:
        fred_client: FREDClient instance
        year: The year to fetch decisions for

    Returns:
        List of ActualDecision objects
    """
    from fed_board.data.fomc_schedule import get_all_fomc_dates

    decisions = []
    meeting_dates = get_all_fomc_dates(year)

    for meeting_date in meeting_dates:
        # Skip future meetings
        if meeting_date > date.today():
            continue

        decision = await get_actual_decision(fred_client, meeting_date)
        if decision:
            decisions.append(decision)

    return decisions
