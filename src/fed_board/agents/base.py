"""Base FOMC agent class for interacting with Claude."""

import asyncio
import json
import logging
import os
import random
import re
import time
from typing import Any, ClassVar

import anthropic

from fed_board.agents.prompts.system import (
    build_deliberation_prompt,
    build_projection_prompt,
    build_system_prompt,
    build_vote_prompt,
)
from fed_board.config import Settings, get_settings
from fed_board.data.indicators import EconomicIndicators
from fed_board.models.meeting import RateProjection, Vote
from fed_board.models.member import FOMCMember, MemberVotePreference

# Configure logging
logger = logging.getLogger(__name__)


class FOMCAgentError(Exception):
    """Exception raised for FOMC agent errors."""

    pass


class FOMCAgent:
    """An AI agent representing an FOMC member."""

    # Class-level semaphore to limit concurrent API calls across all agents
    # This prevents rate limit errors when running many agents in parallel
    _api_semaphore: ClassVar[asyncio.Semaphore | None] = None
    _max_concurrent_calls: ClassVar[int] = 3  # Max concurrent API calls

    @classmethod
    def _get_semaphore(cls) -> asyncio.Semaphore:
        """Get or create the shared API semaphore."""
        if cls._api_semaphore is None:
            cls._api_semaphore = asyncio.Semaphore(cls._max_concurrent_calls)
        return cls._api_semaphore

    @classmethod
    def set_max_concurrent_calls(cls, max_calls: int) -> None:
        """Set the maximum number of concurrent API calls."""
        cls._max_concurrent_calls = max_calls
        cls._api_semaphore = None  # Reset to recreate with new limit

    def __init__(
        self,
        member: FOMCMember,
        settings: Settings | None = None,
        debug: bool = False,
    ) -> None:
        """
        Initialize an FOMC agent.

        Args:
            member: The FOMC member this agent represents
            settings: Application settings (uses defaults if not provided)
            debug: Enable debug logging
        """
        self.member = member
        self.settings = settings or get_settings()
        self.debug = debug or os.getenv("FED_BOARD_DEBUG", "").lower() in ("1", "true")

        # Use AsyncAnthropic for proper async support
        self.client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        self.model = self.settings.anthropic_model
        self.system_prompt = build_system_prompt(member)
        self._conversation_history: list[dict[str, str]] = []

        if self.debug:
            logger.setLevel(logging.DEBUG)
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                ))
                logger.addHandler(handler)

    @property
    def name(self) -> str:
        """Get the member's name."""
        return self.member.name

    @property
    def short_name(self) -> str:
        """Get the member's short name."""
        return self.member.short_name

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self._conversation_history = []

    async def deliberate(
        self,
        indicators: EconomicIndicators,
        previous_speakers: list[tuple[str, str]] | None = None,
    ) -> str:
        """
        Have the agent deliberate on current economic conditions.

        Args:
            indicators: Current economic indicators
            previous_speakers: List of (speaker_name, statement) tuples

        Returns:
            The agent's deliberation statement
        """
        economic_briefing = indicators.to_briefing()
        user_prompt = build_deliberation_prompt(economic_briefing, previous_speakers)

        response = await self._call_api(user_prompt)

        # Store in conversation history
        self._conversation_history.append({"role": "user", "content": user_prompt})
        self._conversation_history.append({"role": "assistant", "content": response})

        return response

    async def vote(
        self,
        chair_proposal: str,
        current_rate_lower: float,
        current_rate_upper: float,
    ) -> Vote:
        """
        Have the agent cast a vote on the Chair's proposal.

        Args:
            chair_proposal: The Chair's proposed policy action
            current_rate_lower: Current fed funds target range lower bound
            current_rate_upper: Current fed funds target range upper bound

        Returns:
            Vote object with the agent's vote
        """
        user_prompt = build_vote_prompt(chair_proposal, current_rate_lower, current_rate_upper)
        response = await self._call_api(user_prompt)

        # Parse the JSON response
        vote_data = self._extract_json(response)

        if vote_data is None:
            raise FOMCAgentError(f"Failed to parse vote response from {self.name}")

        vote_for = vote_data.get("vote", "").lower() == "for"
        preferred_lower = vote_data.get("preferred_rate_lower", current_rate_lower)
        preferred_upper = vote_data.get("preferred_rate_upper", current_rate_upper)

        # Determine if this is a dissent
        is_dissent = not vote_for

        return Vote(
            member_name=self.name,
            vote_for_decision=vote_for,
            preferred_rate=(preferred_lower + preferred_upper) / 2,
            is_dissent=is_dissent,
            dissent_reason=vote_data.get("dissent_reason") if is_dissent else None,
            statement=vote_data.get("statement", ""),
        )

    async def get_vote_preference(
        self,
        indicators: EconomicIndicators,
    ) -> MemberVotePreference:
        """
        Get the agent's full vote preference with detailed reasoning.

        Args:
            indicators: Current economic indicators

        Returns:
            MemberVotePreference with detailed reasoning
        """
        # First deliberate if we haven't already
        if not self._conversation_history:
            await self.deliberate(indicators)

        # The last assistant response should have the deliberation
        deliberation = self._conversation_history[-1]["content"] if self._conversation_history else ""

        # Ask for a specific vote preference
        vote_prompt = """Based on your analysis above, please provide your specific policy recommendation in JSON format:

```json
{
    "rate_change_bps": <change in basis points, e.g., -25, 0, 25>,
    "target_rate_lower": <lower bound of target range>,
    "target_rate_upper": <upper bound of target range>,
    "reasoning": "<detailed reasoning for your vote>",
    "key_factors": ["<factor 1>", "<factor 2>", ...],
    "confidence": <0.0 to 1.0>
}
```"""

        response = await self._call_api(vote_prompt)
        pref_data = self._extract_json(response)

        if pref_data is None:
            # Fall back to defaults
            current_rate = indicators.markets.fed_funds_target_upper or 5.0
            return MemberVotePreference(
                member=self.member,
                preferred_rate_change=0,
                preferred_rate_target=current_rate,
                reasoning=deliberation,
                key_factors=[],
                confidence=0.5,
            )

        return MemberVotePreference(
            member=self.member,
            preferred_rate_change=pref_data.get("rate_change_bps", 0),
            preferred_rate_target=(
                pref_data.get("target_rate_lower", 5.0) + pref_data.get("target_rate_upper", 5.25)
            )
            / 2,
            reasoning=pref_data.get("reasoning", deliberation),
            key_factors=pref_data.get("key_factors", []),
            confidence=pref_data.get("confidence", 0.7),
        )

    async def get_projections(
        self,
        indicators: EconomicIndicators,
    ) -> RateProjection:
        """
        Get the agent's rate projections for the dot plot.

        Args:
            indicators: Current economic indicators

        Returns:
            RateProjection for the dot plot
        """
        economic_briefing = indicators.to_briefing()
        current_rate = indicators.markets.fed_funds_rate or 5.0
        user_prompt = build_projection_prompt(economic_briefing, current_rate)

        response = await self._call_api(user_prompt)
        proj_data = self._extract_json(response)

        if proj_data is None:
            # Fall back to reasonable defaults based on stance
            default_projections = self._get_default_projections(current_rate)
            return RateProjection(member_name=self.name, **default_projections)

        return RateProjection(
            member_name=self.name,
            year_end_2025=proj_data.get("year_end_2025", current_rate),
            year_end_2026=proj_data.get("year_end_2026", current_rate - 0.5),
            year_end_2027=proj_data.get("year_end_2027", current_rate - 1.0),
            longer_run=proj_data.get("longer_run", 2.5),
        )

    async def _call_api(
        self,
        user_message: str,
        max_retries: int = 5,
        base_delay: float = 10.0,
    ) -> str:
        """
        Call the Anthropic API with the given message.

        Includes automatic retry with exponential backoff for rate limits.
        Uses a class-level semaphore to limit concurrent API calls (default: 3).

        Args:
            user_message: The user message to send
            max_retries: Maximum number of retries for rate limit errors
            base_delay: Base delay in seconds for exponential backoff

        Returns:
            The assistant's response text
        """
        messages = self._conversation_history + [{"role": "user", "content": user_message}]
        semaphore = self._get_semaphore()

        if self.debug:
            logger.debug(f"[{self.short_name}] Waiting for API slot...")

        last_error: Exception | None = None
        elapsed = 0.0

        for attempt in range(max_retries + 1):
            # Acquire semaphore to limit concurrent calls
            async with semaphore:
                if self.debug:
                    logger.debug(f"[{self.short_name}] Calling API with model={self.model}")
                    logger.debug(f"[{self.short_name}] Message length: {len(user_message)} chars")

                start_time = time.time()

                try:
                    response = await self.client.messages.create(
                        model=self.model,
                        max_tokens=2000,
                        system=self.system_prompt,
                        messages=messages,
                    )

                    elapsed = time.time() - start_time

                    if self.debug:
                        usage = response.usage
                        logger.debug(
                            f"[{self.short_name}] API response in {elapsed:.1f}s - "
                            f"input_tokens={usage.input_tokens}, output_tokens={usage.output_tokens}"
                        )

                    return response.content[0].text

                except anthropic.RateLimitError as e:
                    elapsed = time.time() - start_time
                    last_error = e
                    # Continue to retry logic below

                except anthropic.APIError as e:
                    elapsed = time.time() - start_time
                    logger.error(f"[{self.short_name}] API error after {elapsed:.1f}s: {e}")
                    raise FOMCAgentError(f"API call failed for {self.name}: {e}") from e

            # Outside semaphore block - wait before retrying (only for rate limits)
            if last_error is not None:
                if attempt < max_retries:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 5)
                    logger.warning(
                        f"[{self.short_name}] Rate limit hit after {elapsed:.1f}s. "
                        f"Retry {attempt + 1}/{max_retries} in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    last_error = None  # Reset for next attempt
                else:
                    logger.error(
                        f"[{self.short_name}] Rate limit error after {max_retries} retries: {last_error}"
                    )
                    raise FOMCAgentError(
                        f"API rate limit exceeded for {self.name} after {max_retries} retries: {last_error}"
                    ) from last_error

        # This shouldn't be reached, but just in case
        raise FOMCAgentError(f"API call failed for {self.name}: {last_error}")

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """
        Extract JSON from a response that may contain markdown code blocks.

        Args:
            text: The response text

        Returns:
            Parsed JSON dict or None if parsing fails
        """
        # Try to find JSON in code blocks first
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try parsing the entire text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _get_default_projections(self, current_rate: float) -> dict[str, float]:
        """Get default projections based on member stance."""
        from fed_board.models.member import Stance

        if self.member.stance == Stance.HAWK:
            return {
                "year_end_2025": current_rate,
                "year_end_2026": current_rate - 0.25,
                "year_end_2027": current_rate - 0.5,
                "longer_run": 3.0,
            }
        elif self.member.stance == Stance.DOVE:
            return {
                "year_end_2025": current_rate - 0.5,
                "year_end_2026": current_rate - 1.0,
                "year_end_2027": current_rate - 1.5,
                "longer_run": 2.5,
            }
        else:  # NEUTRAL
            return {
                "year_end_2025": current_rate - 0.25,
                "year_end_2026": current_rate - 0.75,
                "year_end_2027": current_rate - 1.0,
                "longer_run": 2.75,
            }

    def get_model_info(self) -> dict[str, str]:
        """Get information about the AI model being used."""
        return {
            "model": self.model,
            "member": self.name,
            "provider": "Anthropic",
        }
