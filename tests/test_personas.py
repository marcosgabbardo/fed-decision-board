"""Tests for FOMC member personas."""

import pytest

from fed_board.agents.personas import (
    FOMC_MEMBERS,
    get_member_by_name,
    get_members_by_stance,
    get_voting_members,
)
from fed_board.models.member import Stance


class TestPersonas:
    """Tests for FOMC member personas."""

    def test_all_members_defined(self) -> None:
        """Test that we have all expected members defined."""
        assert len(FOMC_MEMBERS) >= 12  # At least 12 for full FOMC

    def test_chair_exists(self) -> None:
        """Test that the Chair is defined."""
        chair = get_member_by_name("powell")
        assert chair is not None
        assert chair.role.value == "Chair"

    def test_get_member_by_short_name(self) -> None:
        """Test getting member by short name."""
        member = get_member_by_name("waller")
        assert member is not None
        assert member.name == "Christopher J. Waller"

    def test_get_member_by_full_name(self) -> None:
        """Test getting member by full name."""
        member = get_member_by_name("Michelle W. Bowman")
        assert member is not None
        assert member.short_name == "bowman"

    def test_get_member_by_last_name(self) -> None:
        """Test getting member by last name."""
        member = get_member_by_name("jefferson")
        assert member is not None
        assert "Jefferson" in member.name

    def test_nonexistent_member(self) -> None:
        """Test that nonexistent member returns None."""
        member = get_member_by_name("nonexistent")
        assert member is None

    def test_get_voting_members(self) -> None:
        """Test getting voting members for a year."""
        voters_2024 = get_voting_members(2024)
        assert len(voters_2024) >= 7  # At least all Governors

    def test_get_members_by_stance(self) -> None:
        """Test getting members by stance."""
        hawks = get_members_by_stance(Stance.HAWK)
        assert len(hawks) >= 1

        doves = get_members_by_stance(Stance.DOVE)
        assert len(doves) >= 1

        neutrals = get_members_by_stance(Stance.NEUTRAL)
        assert len(neutrals) >= 1

    def test_all_members_have_required_fields(self) -> None:
        """Test that all members have required fields."""
        for member in FOMC_MEMBERS:
            assert member.name
            assert member.short_name
            assert member.role
            assert member.bank
            assert member.stance
            assert len(member.priorities) >= 1
            assert member.communication_style

    def test_governors_always_vote(self) -> None:
        """Test that Governors can vote in any year."""
        for member in FOMC_MEMBERS:
            if member.is_governor:
                assert member.is_voting_in_year(2024) is True
                assert member.is_voting_in_year(2025) is True
                assert member.is_voting_in_year(2026) is True
