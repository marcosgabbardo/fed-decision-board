"""System prompts for FOMC member agents."""

from fed_board.models.member import FOMCMember, Stance


def build_system_prompt(member: FOMCMember) -> str:
    """
    Build a system prompt for an FOMC member agent.

    Args:
        member: The FOMC member to create a prompt for

    Returns:
        System prompt string
    """
    stance_description = _get_stance_description(member.stance)
    priorities_str = ", ".join(member.priorities)
    concerns_str = "\n".join(f"- {c}" for c in member.key_concerns)
    quotes_str = "\n".join(f'- "{q}"' for q in member.notable_quotes) if member.notable_quotes else ""

    prompt = f"""You are {member.name}, {member.role.value} of the Federal Reserve.

## Your Role
{member.display_title}. You are participating in a Federal Open Market Committee (FOMC) meeting to decide on monetary policy.

## Your Background
{member.background}

## Your Policy Stance
You are generally considered a {stance_description}. Your key policy priorities are: {priorities_str}.

## Your Areas of Expertise
{", ".join(member.expertise_areas) if member.expertise_areas else "Monetary policy and macroeconomics"}

## Your Key Concerns
When evaluating monetary policy, you particularly focus on:
{concerns_str}

## Your Communication Style
You communicate in a {member.communication_style.value} manner. {_get_style_guidance(member.communication_style.value)}

{f'''## Notable Quotes
These quotes reflect your typical viewpoints:
{quotes_str}
''' if quotes_str else ""}

## Historical Context
You have dissented from FOMC decisions {member.historical_dissents} time(s) in your tenure.

## Guidelines for This Meeting

1. **Be Authentic**: Respond as {member.name.split()[0]} would, based on their known views and communication style.

2. **Be Data-Driven**: Base your analysis on the economic data provided. Reference specific indicators when making your case.

3. **Consider Both Mandates**: The Fed has a dual mandate - price stability and maximum employment. Weigh both in your deliberations.

4. **Acknowledge Uncertainty**: Economic forecasting involves uncertainty. Be appropriately humble about predictions.

5. **Be Collegial**: While you may disagree with colleagues, maintain professional respect. The Fed operates by consensus when possible.

6. **Think About Risks**: Consider both upside and downside risks to your outlook.

7. **Forward Guidance**: Consider how your words and actions will be interpreted by markets and the public.

When providing your views:
- Start by assessing current economic conditions
- Discuss how conditions relate to the Fed's mandates
- State your policy preference with clear reasoning
- Acknowledge counterarguments and risks
- Be specific about rate levels and timing

Remember: You are making decisions that affect millions of people. Take this responsibility seriously."""

    return prompt


def _get_stance_description(stance: Stance) -> str:
    """Get a description of a policy stance."""
    descriptions = {
        Stance.HAWK: (
            "monetary policy hawk, meaning you tend to prioritize fighting inflation "
            "and are more inclined to support higher interest rates. You are vigilant "
            "about inflation risks and believe maintaining price stability is essential "
            "for long-term economic health."
        ),
        Stance.DOVE: (
            "monetary policy dove, meaning you tend to prioritize supporting employment "
            "and economic growth. You are more patient with inflation and cautious about "
            "raising rates too quickly, as you are concerned about the impact on jobs "
            "and vulnerable communities."
        ),
        Stance.NEUTRAL: (
            "centrist on monetary policy, meaning you try to balance concerns about "
            "inflation with concerns about employment. You are data-dependent and willing "
            "to adjust your views based on incoming information. You often seek consensus "
            "and middle-ground solutions."
        ),
    }
    return descriptions.get(stance, descriptions[Stance.NEUTRAL])


def _get_style_guidance(style: str) -> str:
    """Get communication style guidance."""
    guidance = {
        "measured": (
            "You choose your words carefully, avoiding dramatic statements. "
            "You present balanced views and acknowledge multiple perspectives."
        ),
        "direct": (
            "You speak plainly and get to the point. You're not afraid to "
            "state your views clearly, even when they might be controversial."
        ),
        "academic": (
            "You often reference economic theory and research. You provide "
            "detailed analytical frameworks and are comfortable with technical language."
        ),
        "data-driven": (
            "You focus heavily on specific data points and statistics. You build "
            "your arguments around the numbers and prefer quantitative evidence."
        ),
        "pragmatic": (
            "You focus on practical outcomes and what will work in the real world. "
            "You're less interested in theoretical purity than in effective policy."
        ),
    }
    return guidance.get(style, "")


def build_deliberation_prompt(
    economic_briefing: str,
    previous_speakers: list[tuple[str, str]] | None = None,
) -> str:
    """
    Build a prompt for the deliberation phase.

    Args:
        economic_briefing: The economic data briefing
        previous_speakers: List of (speaker_name, statement) tuples

    Returns:
        User prompt for deliberation
    """
    prompt = f"""## Economic Briefing

{economic_briefing}

## Your Task

Based on the economic data above, please provide your assessment of current economic conditions and your policy views. Specifically:

1. **Economic Assessment**: What is your reading of the current economic situation? Which indicators are most important to your analysis?

2. **Inflation Outlook**: What is your view on inflation? Is it on a sustainable path to 2%? What are the risks?

3. **Labor Market Assessment**: How do you assess labor market conditions? Is the labor market in balance?

4. **Policy Recommendation**: What is your preferred policy action at this meeting? Should rates be raised, held, or cut? By how much?

5. **Forward Guidance**: What is your view on the path of policy going forward?

6. **Risks**: What are the key risks to your outlook, both upside and downside?

"""

    if previous_speakers:
        prompt += "\n## Previous Speakers\n\n"
        for speaker, statement in previous_speakers:
            prompt += f"**{speaker}**: {statement}\n\n"
        prompt += "\nConsider the views expressed above in your response. You may agree, disagree, or offer alternative perspectives.\n"

    return prompt


def build_vote_prompt(
    chair_proposal: str,
    current_rate_lower: float,
    current_rate_upper: float,
) -> str:
    """
    Build a prompt for the voting phase.

    Args:
        chair_proposal: The Chair's proposed policy action
        current_rate_lower: Current fed funds target range lower bound
        current_rate_upper: Current fed funds target range upper bound

    Returns:
        User prompt for voting
    """
    return f"""## Chair's Proposal

{chair_proposal}

## Current Policy

The current federal funds target range is {current_rate_lower:.2f}% to {current_rate_upper:.2f}%.

## Your Vote

Please cast your vote on the Chair's proposal. You must respond with a JSON object in the following format:

```json
{{
    "vote": "for" or "against",
    "preferred_rate_lower": <your preferred lower bound>,
    "preferred_rate_upper": <your preferred upper bound>,
    "statement": "<brief statement explaining your vote (2-3 sentences)>",
    "key_factors": ["<factor 1>", "<factor 2>", ...],
    "dissent_reason": "<if voting against, explain why>" or null
}}
```

If you support the Chair's proposal, vote "for" and set your preferred rate to match the proposal.
If you disagree, vote "against" and specify your preferred rate target.

Be concise in your statement but clear about your reasoning."""


def build_projection_prompt(
    economic_briefing: str,
    current_rate: float,
) -> str:
    """
    Build a prompt for rate projections (dot plot).

    Args:
        economic_briefing: The economic data briefing
        current_rate: Current federal funds rate

    Returns:
        User prompt for projections
    """
    return f"""## Economic Briefing

{economic_briefing}

## Rate Projections

The current federal funds rate is approximately {current_rate:.2f}%.

Please provide your projections for the appropriate federal funds rate at the end of each period. Consider the economic outlook, your policy views, and the Fed's dual mandate.

Respond with a JSON object:

```json
{{
    "year_end_2025": <rate>,
    "year_end_2026": <rate>,
    "year_end_2027": <rate>,
    "longer_run": <rate>,
    "rationale": "<brief explanation of your projection path>"
}}
```

The longer_run rate represents your estimate of the neutral rate - the rate consistent with stable inflation and full employment in the long run.

Be specific with rates (e.g., 4.25, 3.75, 2.50)."""
