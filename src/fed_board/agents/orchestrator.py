"""Meeting orchestrator for coordinating FOMC simulations."""

import asyncio
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from fed_board.agents.base import FOMCAgent
from fed_board.agents.personas import FOMC_MEMBERS, get_member_by_name, get_voting_members
from fed_board.config import Settings, get_settings
from fed_board.data.fred import FREDClient
from fed_board.data.indicators import EconomicIndicators
from fed_board.models.meeting import (
    Decision,
    DissentAnalysis,
    MarketImpact,
    Meeting,
    MeetingResult,
    RateDecision,
    RateProjection,
    Vote,
)
from fed_board.models.member import FOMCMember, MemberVotePreference


class MeetingOrchestrator:
    """Orchestrates FOMC meeting simulations."""

    def __init__(
        self,
        settings: Settings | None = None,
        progress_callback: Callable[[str, float], None] | None = None,
        debug: bool = False,
    ) -> None:
        """
        Initialize the meeting orchestrator.

        Args:
            settings: Application settings
            progress_callback: Optional callback for progress updates (message, percentage)
            debug: Enable debug logging for API calls
        """
        self.settings = settings or get_settings()
        self.fred_client = FREDClient(settings=self.settings)
        self.progress_callback = progress_callback
        self.debug = debug
        self._agents: dict[str, FOMCAgent] = {}

    def _report_progress(self, message: str, percentage: float) -> None:
        """Report progress to the callback if set."""
        if self.progress_callback:
            self.progress_callback(message, percentage)

    def _get_or_create_agent(self, member: FOMCMember) -> FOMCAgent:
        """Get or create an agent for a member."""
        if member.short_name not in self._agents:
            self._agents[member.short_name] = FOMCAgent(
                member, self.settings, debug=self.debug
            )
        return self._agents[member.short_name]

    async def run_meeting(
        self,
        meeting_month: str,
        member_names: list[str] | None = None,
    ) -> MeetingResult:
        """
        Run a full FOMC meeting simulation.

        Args:
            meeting_month: Month in YYYY-MM format
            member_names: Optional list of member short names to include
                         (defaults to all voting members)

        Returns:
            Complete MeetingResult
        """
        # Parse meeting date
        year, month = map(int, meeting_month.split("-"))
        meeting_date = date(year, month, 15)  # Use mid-month as meeting date
        meeting = Meeting(meeting_date=meeting_date)

        self._report_progress("Initializing meeting...", 0.0)

        # Determine participants
        if member_names:
            members = [get_member_by_name(name) for name in member_names]
            members = [m for m in members if m is not None]
        else:
            members = get_voting_members(year)

        if not members:
            raise ValueError("No valid members specified for the meeting")

        # Create agents for all members
        agents = [self._get_or_create_agent(m) for m in members]
        for agent in agents:
            agent.reset_conversation()

        # Step 1: Fetch economic data
        self._report_progress("Fetching economic data from FRED...", 0.1)
        indicators = await self.fred_client.get_economic_indicators(as_of_date=meeting_date)

        # Step 2: Staff presentation (economic briefing)
        self._report_progress("Preparing staff presentation...", 0.15)
        economic_briefing = indicators.to_briefing()

        # Step 3: Go-around deliberation
        self._report_progress("Beginning deliberation...", 0.2)
        deliberations: list[tuple[str, str]] = []
        vote_preferences: list[MemberVotePreference] = []

        # Chair goes last, so reorder to put Powell at the end
        ordered_agents = self._reorder_for_deliberation(agents)

        for i, agent in enumerate(ordered_agents):
            progress = 0.2 + (0.4 * (i + 1) / len(ordered_agents))
            self._report_progress(f"{agent.name} is speaking...", progress)

            # Pass previous speakers' statements
            statement = await agent.deliberate(indicators, deliberations)
            deliberations.append((agent.name, statement))

            # Get vote preference
            preference = await agent.get_vote_preference(indicators)
            vote_preferences.append(preference)

        # Step 4: Chair's proposal
        self._report_progress("Chair formulating proposal...", 0.65)
        chair_agent = self._get_chair_agent(agents)
        proposal, proposed_rate = self._formulate_chair_proposal(vote_preferences, indicators)

        # Step 5: Voting (parallel - all members vote simultaneously)
        self._report_progress("Collecting votes (parallel)...", 0.7)
        current_lower = indicators.markets.fed_funds_target_lower or 5.0
        current_upper = indicators.markets.fed_funds_target_upper or 5.25

        vote_tasks = [
            agent.vote(proposal, current_lower, current_upper)
            for agent in agents
        ]
        votes: list[Vote] = await asyncio.gather(*vote_tasks)
        self._report_progress("All votes recorded.", 0.85)

        # Step 6: Determine final decision
        self._report_progress("Finalizing decision...", 0.85)
        decision = self._determine_decision(votes, proposed_rate, current_lower, current_upper)

        # Step 7: Get projections for dot plot (parallel)
        self._report_progress("Collecting rate projections (parallel)...", 0.9)
        projections = await self._collect_projections(agents, indicators)

        # Step 8: Analyze dissents
        dissent_analyses = self._analyze_dissents(votes, decision, members)

        # Step 9: Estimate market impact
        market_impact = self._estimate_market_impact(decision, indicators)

        # Step 10: Generate summaries
        self._report_progress("Generating summaries...", 0.95)
        statement_summary = self._generate_statement_summary(decision, indicators)
        participants_discussion = self._summarize_deliberations(deliberations)
        economic_outlook = self._generate_economic_outlook(indicators)

        self._report_progress("Meeting complete!", 1.0)

        return MeetingResult(
            meeting=meeting,
            economic_indicators=indicators,
            decision=decision,
            votes=votes,
            vote_preferences=vote_preferences,
            rate_projections=projections,
            dissent_analyses=dissent_analyses,
            market_impact=market_impact,
            statement_summary=statement_summary,
            participants_discussion=participants_discussion,
            economic_outlook=economic_outlook,
            simulation_metadata={
                "member_count": len(members),
                "member_names": [m.name for m in members],
                "model": self.settings.anthropic_model,
            },
            created_at=datetime.now(),
            model_used=self.settings.anthropic_model,
        )

    def _reorder_for_deliberation(self, agents: list[FOMCAgent]) -> list[FOMCAgent]:
        """Reorder agents so Chair speaks last."""
        chair = None
        others = []
        for agent in agents:
            if agent.member.role.value == "Chair":
                chair = agent
            else:
                others.append(agent)
        if chair:
            others.append(chair)
        return others

    def _get_chair_agent(self, agents: list[FOMCAgent]) -> FOMCAgent:
        """Get the Chair agent."""
        for agent in agents:
            if agent.member.role.value == "Chair":
                return agent
        # Fall back to first agent if no chair
        return agents[0]

    def _formulate_chair_proposal(
        self,
        preferences: list[MemberVotePreference],
        indicators: EconomicIndicators,
    ) -> tuple[str, float]:
        """
        Formulate the Chair's proposal based on member preferences.

        Returns:
            Tuple of (proposal text, proposed rate midpoint)
        """
        # Calculate median preferred rate
        rates = [p.preferred_rate_target for p in preferences]
        rates.sort()
        median_rate = rates[len(rates) // 2]

        # Round to nearest 0.25
        proposed_rate = round(median_rate * 4) / 4

        current_lower = indicators.markets.fed_funds_target_lower or 5.0
        current_upper = indicators.markets.fed_funds_target_upper or 5.25
        current_mid = (current_lower + current_upper) / 2

        change_bps = int((proposed_rate - current_mid) * 100)

        if change_bps > 0:
            action = f"raise the target range by {change_bps} basis points"
        elif change_bps < 0:
            action = f"lower the target range by {abs(change_bps)} basis points"
        else:
            action = "maintain the current target range"

        new_lower = proposed_rate - 0.125
        new_upper = proposed_rate + 0.125

        proposal = f"""The Chair proposes to {action}, setting the target range for the federal funds rate at {new_lower:.2f} to {new_upper:.2f} percent.

This decision reflects the Committee's assessment of current economic conditions and progress toward our dual mandate objectives.

The Committee will continue to monitor incoming data and remains prepared to adjust the stance of monetary policy as appropriate."""

        return proposal, proposed_rate

    def _determine_decision(
        self,
        votes: list[Vote],
        proposed_rate: float,
        current_lower: float,
        current_upper: float,
    ) -> Decision:
        """Determine the final decision based on votes."""
        # Count votes for the proposal
        for_votes = sum(1 for v in votes if v.vote_for_decision)
        against_votes = len(votes) - for_votes

        # Majority wins
        if for_votes >= against_votes:
            new_lower = proposed_rate - 0.125
            new_upper = proposed_rate + 0.125
        else:
            # If majority dissents, find the mode of preferred rates
            preferred_rates = [v.preferred_rate for v in votes if not v.vote_for_decision]
            rate_counts = Counter(preferred_rates)
            most_common_rate = rate_counts.most_common(1)[0][0]
            new_lower = most_common_rate - 0.125
            new_upper = most_common_rate + 0.125

        current_mid = (current_lower + current_upper) / 2
        new_mid = (new_lower + new_upper) / 2
        change_bps = int((new_mid - current_mid) * 100)

        if change_bps > 0:
            rate_decision = RateDecision.RAISE
        elif change_bps < 0:
            rate_decision = RateDecision.CUT
        else:
            rate_decision = RateDecision.HOLD

        return Decision(
            rate_decision=rate_decision,
            rate_change_bps=change_bps,
            new_rate_lower=new_lower,
            new_rate_upper=new_upper,
            previous_rate_lower=current_lower,
            previous_rate_upper=current_upper,
        )

    async def _collect_projections(
        self,
        agents: list[FOMCAgent],
        indicators: EconomicIndicators,
    ) -> list[RateProjection]:
        """Collect rate projections from all agents (parallel)."""

        async def safe_get_projection(agent: FOMCAgent) -> RateProjection | None:
            """Get projection with error handling."""
            try:
                return await agent.get_projections(indicators)
            except Exception:
                # Return None if API call fails
                return None

        projection_tasks = [safe_get_projection(agent) for agent in agents]
        results = await asyncio.gather(*projection_tasks)

        # Filter out None values (failed calls)
        return [p for p in results if p is not None]

    def _analyze_dissents(
        self,
        votes: list[Vote],
        decision: Decision,
        members: list[FOMCMember],
    ) -> list[DissentAnalysis]:
        """Analyze any dissenting votes."""
        analyses = []
        members_by_name = {m.name: m for m in members}

        for vote in votes:
            if vote.is_dissent:
                member = members_by_name.get(vote.member_name)
                analyses.append(
                    DissentAnalysis(
                        dissenter_name=vote.member_name,
                        dissenter_stance=str(member.stance) if member else "unknown",
                        majority_decision=decision.rate_range_str,
                        dissenter_preference=f"{vote.preferred_rate:.2f}%",
                        reasoning=vote.dissent_reason or vote.statement,
                        historical_context=(
                            f"This member has dissented {member.historical_dissents} time(s) previously."
                            if member
                            else ""
                        ),
                    )
                )
        return analyses

    def _estimate_market_impact(
        self,
        decision: Decision,
        indicators: EconomicIndicators,
    ) -> MarketImpact:
        """Estimate the market impact of the decision."""
        # Simple heuristic-based impact estimation
        change_bps = decision.rate_change_bps

        # Treasury yields typically move with fed funds
        treasury_10y_change = change_bps // 3  # 10Y less sensitive
        treasury_2y_change = change_bps // 2  # 2Y more sensitive

        # Equities typically inverse to rates
        sp500_change = -change_bps / 100

        # Dollar strengthens with rate hikes
        dxy_change = change_bps / 50

        if decision.rate_decision == RateDecision.HOLD:
            rationale = "With no change in rates, markets may have limited immediate reaction."
        elif decision.rate_decision == RateDecision.RAISE:
            rationale = (
                "Rate increases typically strengthen the dollar and put pressure on equities "
                "as borrowing costs rise."
            )
        else:
            rationale = (
                "Rate cuts typically support equities and weaken the dollar as monetary "
                "conditions ease."
            )

        return MarketImpact(
            treasury_10y_change_bps=treasury_10y_change,
            treasury_2y_change_bps=treasury_2y_change,
            sp500_change_pct=sp500_change,
            dxy_change_pct=dxy_change,
            rationale=rationale,
        )

    def _generate_statement_summary(
        self,
        decision: Decision,
        indicators: EconomicIndicators,
    ) -> str:
        """Generate a summary of the policy statement."""
        if decision.rate_decision == RateDecision.HOLD:
            action = "decided to maintain"
        elif decision.rate_decision == RateDecision.RAISE:
            action = f"decided to raise by {decision.rate_change_bps} basis points"
        else:
            action = f"decided to lower by {abs(decision.rate_change_bps)} basis points"

        return f"""The Federal Open Market Committee {action} the target range for the federal funds rate at {decision.rate_range_str}.

The Committee seeks to achieve maximum employment and inflation at the rate of 2 percent over the longer run. Recent indicators suggest that economic activity has continued to expand at a solid pace. Job gains have remained strong, and the unemployment rate has remained low. Inflation remains elevated.

In determining the extent of additional policy adjustments, the Committee will take into account the cumulative tightening of monetary policy, the lags with which monetary policy affects economic activity and inflation, and economic and financial developments."""

    def _summarize_deliberations(
        self,
        deliberations: list[tuple[str, str]],
    ) -> str:
        """Summarize the participants' discussion."""
        # Extract key themes from deliberations
        lines = []
        for name, statement in deliberations:
            # Take first few sentences as summary
            sentences = statement.split(".")[:3]
            summary = ". ".join(sentences).strip()
            if summary:
                lines.append(f"**{name}**: {summary}...")

        return "\n\n".join(lines) if lines else "Participants discussed current economic conditions."

    def _generate_economic_outlook(
        self,
        indicators: EconomicIndicators,
    ) -> str:
        """Generate the staff economic outlook summary."""
        inflation_status = "elevated" if (indicators.inflation.core_pce_yoy or 3) > 2.5 else "moderating"
        labor_status = (
            "strong" if (indicators.employment.unemployment_rate or 4) < 4.5 else "softening"
        )

        return f"""The staff economic outlook projects continued moderate growth in real GDP over the coming year. The labor market remains {labor_status} with unemployment near historically low levels. Inflation remains {inflation_status} but is expected to gradually return toward the Committee's 2 percent objective.

Key risks to the outlook include persistence of elevated inflation, potential for tighter financial conditions, and geopolitical uncertainties. The staff projects inflation will continue to moderate as supply chain pressures ease and demand growth slows."""

    async def save_result(
        self,
        result: MeetingResult,
        output_dir: Path | None = None,
    ) -> Path:
        """
        Save the meeting result to JSON.

        Args:
            result: The meeting result to save
            output_dir: Output directory (defaults to settings simulations_dir)

        Returns:
            Path to the saved file
        """
        if output_dir is None:
            output_dir = self.settings.simulations_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{result.meeting.month_str}.json"
        filepath = output_dir / filename

        with open(filepath, "w") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, default=str)

        return filepath

    def load_result(self, meeting_month: str) -> MeetingResult | None:
        """
        Load a saved meeting result.

        Args:
            meeting_month: Month in YYYY-MM format

        Returns:
            MeetingResult or None if not found
        """
        filepath = self.settings.simulations_dir / f"{meeting_month}.json"
        if not filepath.exists():
            return None

        with open(filepath, "r") as f:
            data = json.load(f)

        return MeetingResult(**data)
