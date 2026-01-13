"""FOMC member data models."""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class Stance(str, Enum):
    """Policy stance of an FOMC member."""

    HAWK = "hawk"
    DOVE = "dove"
    NEUTRAL = "neutral"

    def __str__(self) -> str:
        return self.value


class Role(str, Enum):
    """Role of an FOMC member."""

    CHAIR = "Chair"
    VICE_CHAIR = "Vice Chair"
    VICE_CHAIR_SUPERVISION = "Vice Chair for Supervision"
    GOVERNOR = "Governor"
    PRESIDENT = "Reserve Bank President"

    def __str__(self) -> str:
        return self.value


class CommunicationStyle(str, Enum):
    """Communication style of an FOMC member."""

    MEASURED = "measured"
    DIRECT = "direct"
    ACADEMIC = "academic"
    DATA_DRIVEN = "data-driven"
    PRAGMATIC = "pragmatic"

    def __str__(self) -> str:
        return self.value


class FOMCMember(BaseModel):
    """Represents an FOMC member with their characteristics and voting history."""

    # Basic Information
    name: str = Field(
        ...,
        description="Full name of the member",
        examples=["Jerome H. Powell"],
    )
    short_name: str = Field(
        ...,
        description="Short identifier for CLI usage",
        examples=["powell"],
    )
    role: Role = Field(
        ...,
        description="Current role in the FOMC",
    )
    bank: str = Field(
        ...,
        description="Federal Reserve Bank or Board of Governors",
        examples=["Board of Governors", "Federal Reserve Bank of New York"],
    )

    # Voting Status
    is_voting_member: bool = Field(
        default=True,
        description="Whether this member currently has voting rights",
    )
    voting_years: list[int] = Field(
        default_factory=list,
        description="Years when this Reserve Bank president has voting rights",
    )

    # Policy Characteristics
    stance: Stance = Field(
        ...,
        description="General policy stance (hawk/dove/neutral)",
    )
    priorities: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=5,
            description="Key policy priorities",
            examples=[["price stability", "maximum employment"]],
        ),
    ]
    communication_style: CommunicationStyle = Field(
        ...,
        description="How this member typically communicates",
    )

    # Historical Context
    historical_dissents: int = Field(
        default=0,
        ge=0,
        description="Number of times this member has dissented from the majority",
    )
    key_concerns: list[str] = Field(
        default_factory=list,
        description="Specific economic concerns this member emphasizes",
        examples=[["inflation expectations", "wage-price spiral"]],
    )
    notable_quotes: list[str] = Field(
        default_factory=list,
        description="Notable quotes that capture the member's views",
    )

    # Background
    background: str = Field(
        default="",
        description="Brief professional background",
    )
    expertise_areas: list[str] = Field(
        default_factory=list,
        description="Areas of economic expertise",
    )

    def is_voting_in_year(self, year: int) -> bool:
        """Check if this member has voting rights in a given year."""
        if self.role in [Role.CHAIR, Role.VICE_CHAIR, Role.VICE_CHAIR_SUPERVISION, Role.GOVERNOR]:
            return self.is_voting_member
        # NY Fed President always votes
        if "New York" in self.bank:
            return True
        # Other Reserve Bank presidents rotate
        return year in self.voting_years

    @property
    def is_governor(self) -> bool:
        """Check if this member is a Board Governor."""
        return self.role in [
            Role.CHAIR,
            Role.VICE_CHAIR,
            Role.VICE_CHAIR_SUPERVISION,
            Role.GOVERNOR,
        ]

    @property
    def is_reserve_bank_president(self) -> bool:
        """Check if this member is a Reserve Bank President."""
        return self.role == Role.PRESIDENT

    @property
    def display_title(self) -> str:
        """Get the display title for this member."""
        if self.is_governor:
            return f"{self.role.value} {self.name}"
        return f"{self.name}, President of the {self.bank}"


class MemberVotePreference(BaseModel):
    """A member's preferred rate decision and reasoning."""

    member: FOMCMember
    preferred_rate_change: Annotated[
        float,
        Field(
            description="Preferred change in basis points (e.g., -25, 0, 25)",
            ge=-100,
            le=100,
        ),
    ]
    preferred_rate_target: Annotated[
        float,
        Field(
            description="Preferred target rate (e.g., 4.25)",
            ge=0,
            le=20,
        ),
    ]
    reasoning: str = Field(
        ...,
        description="Detailed reasoning for the vote",
    )
    key_factors: list[str] = Field(
        default_factory=list,
        description="Key economic factors influencing the decision",
    )
    confidence: Annotated[
        float,
        Field(
            default=0.8,
            ge=0,
            le=1,
            description="Confidence level in the decision",
        ),
    ]
