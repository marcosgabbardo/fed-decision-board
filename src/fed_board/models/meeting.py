"""FOMC meeting data models."""

from datetime import date, datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from fed_board.data.indicators import EconomicIndicators
from fed_board.models.member import FOMCMember, MemberVotePreference


class RateDecision(str, Enum):
    """Type of rate decision."""

    RAISE = "raise"
    HOLD = "hold"
    CUT = "cut"

    def __str__(self) -> str:
        return self.value


class Vote(BaseModel):
    """Individual vote cast by an FOMC member."""

    member_name: str = Field(
        ...,
        description="Name of the voting member",
    )
    vote_for_decision: bool = Field(
        ...,
        description="Whether the member voted for the majority decision",
    )
    preferred_rate: Annotated[
        float,
        Field(
            description="The rate this member voted for",
            ge=0,
            le=20,
        ),
    ]
    is_dissent: bool = Field(
        default=False,
        description="Whether this was a dissenting vote",
    )
    dissent_reason: str | None = Field(
        default=None,
        description="Reason for dissent if applicable",
    )
    statement: str = Field(
        default="",
        description="Brief statement explaining the vote",
    )


class Decision(BaseModel):
    """The final FOMC rate decision."""

    rate_decision: RateDecision = Field(
        ...,
        description="Type of rate decision (raise/hold/cut)",
    )
    rate_change_bps: Annotated[
        int,
        Field(
            description="Change in basis points",
            ge=-100,
            le=100,
        ),
    ]
    new_rate_lower: Annotated[
        float,
        Field(
            description="New target rate range lower bound",
            ge=0,
            le=20,
        ),
    ]
    new_rate_upper: Annotated[
        float,
        Field(
            description="New target rate range upper bound",
            ge=0,
            le=20,
        ),
    ]
    previous_rate_lower: Annotated[
        float,
        Field(
            description="Previous target rate range lower bound",
            ge=0,
            le=20,
        ),
    ]
    previous_rate_upper: Annotated[
        float,
        Field(
            description="Previous target rate range upper bound",
            ge=0,
            le=20,
        ),
    ]

    @computed_field
    @property
    def rate_range_str(self) -> str:
        """Format the rate range as a string."""
        return f"{self.new_rate_lower:.2f}-{self.new_rate_upper:.2f}%"

    @computed_field
    @property
    def previous_rate_range_str(self) -> str:
        """Format the previous rate range as a string."""
        return f"{self.previous_rate_lower:.2f}-{self.previous_rate_upper:.2f}%"


class RateProjection(BaseModel):
    """Individual member's rate projection for the dot plot."""

    member_name: str = Field(
        ...,
        description="Name of the projecting member",
    )
    year_end_2025: Annotated[
        float,
        Field(
            description="Projected rate at end of 2025",
            ge=0,
            le=20,
        ),
    ]
    year_end_2026: Annotated[
        float,
        Field(
            description="Projected rate at end of 2026",
            ge=0,
            le=20,
        ),
    ]
    year_end_2027: Annotated[
        float,
        Field(
            description="Projected rate at end of 2027",
            ge=0,
            le=20,
        ),
    ]
    longer_run: Annotated[
        float,
        Field(
            description="Longer-run projected rate",
            ge=0,
            le=20,
        ),
    ]


class MarketImpact(BaseModel):
    """Estimated market impact of the decision."""

    treasury_10y_change_bps: Annotated[
        int,
        Field(
            description="Expected change in 10Y Treasury yield (bps)",
        ),
    ]
    treasury_2y_change_bps: Annotated[
        int,
        Field(
            description="Expected change in 2Y Treasury yield (bps)",
        ),
    ]
    sp500_change_pct: Annotated[
        float,
        Field(
            description="Expected change in S&P 500 (%)",
        ),
    ]
    dxy_change_pct: Annotated[
        float,
        Field(
            description="Expected change in Dollar Index (%)",
        ),
    ]
    rationale: str = Field(
        default="",
        description="Explanation of the market impact estimate",
    )


class DissentAnalysis(BaseModel):
    """Analysis of dissenting votes."""

    dissenter_name: str = Field(
        ...,
        description="Name of the dissenting member",
    )
    dissenter_stance: str = Field(
        ...,
        description="Hawk/dove/neutral stance",
    )
    majority_decision: str = Field(
        ...,
        description="What the majority voted for",
    )
    dissenter_preference: str = Field(
        ...,
        description="What the dissenter voted for",
    )
    reasoning: str = Field(
        ...,
        description="Detailed reasoning for the dissent",
    )
    historical_context: str = Field(
        default="",
        description="Context about this member's dissent history",
    )


class Meeting(BaseModel):
    """Represents an FOMC meeting."""

    meeting_date: date = Field(
        ...,
        description="Date of the meeting (first day if multi-day)",
    )
    meeting_end_date: date | None = Field(
        default=None,
        description="End date if multi-day meeting",
    )
    is_scheduled: bool = Field(
        default=True,
        description="Whether this is a regularly scheduled meeting",
    )

    @computed_field
    @property
    def month_str(self) -> str:
        """Get the month string for this meeting (YYYY-MM)."""
        return self.meeting_date.strftime("%Y-%m")

    @computed_field
    @property
    def display_date(self) -> str:
        """Get a formatted display date."""
        if self.meeting_end_date:
            return f"{self.meeting_date.strftime('%B %d')}-{self.meeting_end_date.strftime('%d, %Y')}"
        return self.meeting_date.strftime("%B %d, %Y")


class MeetingResult(BaseModel):
    """Complete results of an FOMC meeting simulation."""

    meeting: Meeting = Field(
        ...,
        description="Meeting information",
    )
    economic_indicators: EconomicIndicators | None = Field(
        default=None,
        description="Economic indicators used for the meeting",
    )
    decision: Decision = Field(
        ...,
        description="Final rate decision",
    )
    votes: list[Vote] = Field(
        default_factory=list,
        description="Individual votes from each member",
    )
    vote_preferences: list[MemberVotePreference] = Field(
        default_factory=list,
        description="Detailed vote preferences and reasoning",
    )
    rate_projections: list[RateProjection] = Field(
        default_factory=list,
        description="Rate projections for dot plot",
    )
    dissent_analyses: list[DissentAnalysis] = Field(
        default_factory=list,
        description="Analysis of any dissenting votes",
    )
    market_impact: MarketImpact | None = Field(
        default=None,
        description="Estimated market impact",
    )
    statement_summary: str = Field(
        default="",
        description="Summary of the policy statement",
    )
    participants_discussion: str = Field(
        default="",
        description="Summary of participants' views",
    )
    economic_outlook: str = Field(
        default="",
        description="Staff economic outlook summary",
    )
    simulation_metadata: dict = Field(
        default_factory=dict,
        description="Metadata about the simulation run",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this simulation was created",
    )
    model_used: str = Field(
        default="",
        description="AI model used for the simulation",
    )

    @computed_field
    @property
    def vote_count_for(self) -> int:
        """Count votes for the decision."""
        return sum(1 for v in self.votes if v.vote_for_decision)

    @computed_field
    @property
    def vote_count_against(self) -> int:
        """Count dissenting votes."""
        return sum(1 for v in self.votes if not v.vote_for_decision)

    @computed_field
    @property
    def vote_summary(self) -> str:
        """Get a summary of the vote."""
        if self.vote_count_against == 0:
            return f"Unanimous ({self.vote_count_for}-0)"
        dissenters = [v.member_name for v in self.votes if v.is_dissent]
        return f"{self.vote_count_for}-{self.vote_count_against} ({', '.join(dissenters)} dissented)"

    @computed_field
    @property
    def has_dissents(self) -> bool:
        """Check if there were any dissenting votes."""
        return self.vote_count_against > 0
