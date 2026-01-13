"""Tests for data models."""

from datetime import date

import pytest

from fed_board.models.meeting import Decision, Meeting, MeetingResult, RateDecision, Vote
from fed_board.models.member import (
    CommunicationStyle,
    FOMCMember,
    MemberVotePreference,
    Role,
    Stance,
)


class TestFOMCMember:
    """Tests for FOMCMember model."""

    def test_create_governor(self) -> None:
        """Test creating a Board Governor."""
        member = FOMCMember(
            name="Test Governor",
            short_name="test",
            role=Role.GOVERNOR,
            bank="Board of Governors",
            stance=Stance.NEUTRAL,
            priorities=["price stability", "employment"],
            communication_style=CommunicationStyle.MEASURED,
        )
        assert member.name == "Test Governor"
        assert member.is_governor is True
        assert member.is_reserve_bank_president is False

    def test_create_president(self) -> None:
        """Test creating a Reserve Bank President."""
        member = FOMCMember(
            name="Test President",
            short_name="testp",
            role=Role.PRESIDENT,
            bank="Federal Reserve Bank of Test",
            stance=Stance.HAWK,
            priorities=["inflation"],
            communication_style=CommunicationStyle.DIRECT,
            voting_years=[2024, 2027],
        )
        assert member.is_governor is False
        assert member.is_reserve_bank_president is True

    def test_voting_eligibility(self) -> None:
        """Test voting eligibility for different years."""
        member = FOMCMember(
            name="Test President",
            short_name="testp",
            role=Role.PRESIDENT,
            bank="Federal Reserve Bank of Test",
            stance=Stance.NEUTRAL,
            priorities=["stability"],
            communication_style=CommunicationStyle.MEASURED,
            voting_years=[2024, 2027],
        )
        assert member.is_voting_in_year(2024) is True
        assert member.is_voting_in_year(2025) is False
        assert member.is_voting_in_year(2027) is True

    def test_governor_always_votes(self) -> None:
        """Test that Governors always vote."""
        member = FOMCMember(
            name="Test Governor",
            short_name="testg",
            role=Role.GOVERNOR,
            bank="Board of Governors",
            stance=Stance.DOVE,
            priorities=["employment"],
            communication_style=CommunicationStyle.ACADEMIC,
        )
        assert member.is_voting_in_year(2024) is True
        assert member.is_voting_in_year(2025) is True
        assert member.is_voting_in_year(2030) is True


class TestMeeting:
    """Tests for Meeting model."""

    def test_single_day_meeting(self) -> None:
        """Test single day meeting."""
        meeting = Meeting(meeting_date=date(2024, 1, 15))
        assert meeting.month_str == "2024-01"
        assert "January 15, 2024" in meeting.display_date

    def test_multi_day_meeting(self) -> None:
        """Test multi-day meeting."""
        meeting = Meeting(
            meeting_date=date(2024, 1, 30),
            meeting_end_date=date(2024, 1, 31),
        )
        assert meeting.month_str == "2024-01"
        assert "30" in meeting.display_date
        assert "31" in meeting.display_date


class TestDecision:
    """Tests for Decision model."""

    def test_rate_raise(self) -> None:
        """Test rate raise decision."""
        decision = Decision(
            rate_decision=RateDecision.RAISE,
            rate_change_bps=25,
            new_rate_lower=5.25,
            new_rate_upper=5.50,
            previous_rate_lower=5.00,
            previous_rate_upper=5.25,
        )
        assert decision.rate_range_str == "5.25-5.50%"
        assert decision.rate_change_bps == 25

    def test_rate_hold(self) -> None:
        """Test rate hold decision."""
        decision = Decision(
            rate_decision=RateDecision.HOLD,
            rate_change_bps=0,
            new_rate_lower=5.00,
            new_rate_upper=5.25,
            previous_rate_lower=5.00,
            previous_rate_upper=5.25,
        )
        assert decision.rate_change_bps == 0
        assert decision.previous_rate_range_str == decision.rate_range_str

    def test_rate_cut(self) -> None:
        """Test rate cut decision."""
        decision = Decision(
            rate_decision=RateDecision.CUT,
            rate_change_bps=-25,
            new_rate_lower=4.75,
            new_rate_upper=5.00,
            previous_rate_lower=5.00,
            previous_rate_upper=5.25,
        )
        assert decision.rate_change_bps == -25


class TestVote:
    """Tests for Vote model."""

    def test_vote_for(self) -> None:
        """Test vote for the decision."""
        vote = Vote(
            member_name="Test Member",
            vote_for_decision=True,
            preferred_rate=5.25,
            is_dissent=False,
            statement="I support this action.",
        )
        assert vote.vote_for_decision is True
        assert vote.is_dissent is False

    def test_dissenting_vote(self) -> None:
        """Test dissenting vote."""
        vote = Vote(
            member_name="Test Dissenter",
            vote_for_decision=False,
            preferred_rate=5.50,
            is_dissent=True,
            dissent_reason="Inflation concerns",
            statement="I prefer a higher rate.",
        )
        assert vote.vote_for_decision is False
        assert vote.is_dissent is True
        assert vote.dissent_reason == "Inflation concerns"
