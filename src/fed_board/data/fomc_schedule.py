"""FOMC meeting schedule data."""

from datetime import date

# Official FOMC meeting dates (announcement day - typically day 2 of 2-day meetings)
# Source: Federal Reserve website
FOMC_MEETINGS: dict[int, list[str]] = {
    2023: [
        "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14",
        "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    ],
    2024: [
        "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
        "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    ],
    2025: [
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
        "2025-07-30", "2025-09-17", "2025-11-05", "2025-12-17",
    ],
    2026: [
        "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16",
    ],
}


def get_fomc_meeting_date(month: str) -> date | None:
    """
    Get the actual FOMC meeting date for a given month.

    Args:
        month: Month in YYYY-MM format

    Returns:
        The meeting date, or None if no meeting in that month
    """
    year, month_num = map(int, month.split("-"))
    meetings = FOMC_MEETINGS.get(year, [])

    for meeting_str in meetings:
        meeting_date = date.fromisoformat(meeting_str)
        if meeting_date.month == month_num:
            return meeting_date

    return None


def get_fomc_months(year: int) -> list[str]:
    """
    Get list of months with FOMC meetings for a given year.

    Args:
        year: The year (e.g., 2024)

    Returns:
        List of month strings in YYYY-MM format
    """
    meetings = FOMC_MEETINGS.get(year, [])
    return [date.fromisoformat(m).strftime("%Y-%m") for m in meetings]


def get_all_fomc_dates(year: int) -> list[date]:
    """
    Get all FOMC meeting dates for a given year.

    Args:
        year: The year (e.g., 2024)

    Returns:
        List of meeting dates
    """
    meetings = FOMC_MEETINGS.get(year, [])
    return [date.fromisoformat(m) for m in meetings]


def is_fomc_month(month: str) -> bool:
    """
    Check if a month has an FOMC meeting.

    Args:
        month: Month in YYYY-MM format

    Returns:
        True if there's a meeting in that month
    """
    return get_fomc_meeting_date(month) is not None


def get_next_fomc_meeting(from_date: date | None = None) -> tuple[str, date] | None:
    """
    Get the next FOMC meeting date from a given date.

    Args:
        from_date: Reference date (defaults to today)

    Returns:
        Tuple of (month string, meeting date) or None if not found
    """
    if from_date is None:
        from_date = date.today()

    for year in range(from_date.year, from_date.year + 2):
        for meeting_str in FOMC_MEETINGS.get(year, []):
            meeting_date = date.fromisoformat(meeting_str)
            if meeting_date > from_date:
                return meeting_date.strftime("%Y-%m"), meeting_date

    return None
