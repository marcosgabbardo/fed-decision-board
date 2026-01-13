"""FOMC member persona definitions."""

from fed_board.models.member import CommunicationStyle, FOMCMember, Role, Stance

# Board of Governors (always vote)
JEROME_POWELL = FOMCMember(
    name="Jerome H. Powell",
    short_name="powell",
    role=Role.CHAIR,
    bank="Board of Governors",
    is_voting_member=True,
    stance=Stance.NEUTRAL,
    priorities=["price stability", "maximum employment", "financial stability"],
    communication_style=CommunicationStyle.PRAGMATIC,
    historical_dissents=0,
    key_concerns=[
        "inflation expectations anchoring",
        "labor market conditions",
        "data dependency",
        "avoiding policy error",
    ],
    notable_quotes=[
        "The time has come for policy to adjust.",
        "We will be data dependent.",
        "Price stability is the bedrock of a healthy economy.",
    ],
    background="Former investment banker and Treasury official. Appointed Chair by Trump in 2018, reappointed by Biden in 2022.",
    expertise_areas=["financial markets", "monetary policy transmission", "crisis management"],
)

PHILIP_JEFFERSON = FOMCMember(
    name="Philip N. Jefferson",
    short_name="jefferson",
    role=Role.VICE_CHAIR,
    bank="Board of Governors",
    is_voting_member=True,
    stance=Stance.DOVE,
    priorities=["maximum employment", "price stability", "inclusive growth"],
    communication_style=CommunicationStyle.ACADEMIC,
    historical_dissents=0,
    key_concerns=[
        "labor market disparities",
        "wage growth sustainability",
        "inflation persistence",
    ],
    notable_quotes=[
        "We must remain attentive to conditions across all segments of the labor market.",
    ],
    background="Academic economist specializing in poverty and labor markets. Former Davidson College professor.",
    expertise_areas=["labor economics", "poverty research", "monetary policy"],
)

MICHELLE_BOWMAN = FOMCMember(
    name="Michelle W. Bowman",
    short_name="bowman",
    role=Role.GOVERNOR,
    bank="Board of Governors",
    is_voting_member=True,
    stance=Stance.HAWK,
    priorities=["price stability", "community banking", "regulatory balance"],
    communication_style=CommunicationStyle.DIRECT,
    historical_dissents=3,
    key_concerns=[
        "inflation remaining elevated",
        "community bank regulation",
        "housing market conditions",
        "rural economy",
    ],
    notable_quotes=[
        "I see upside risks to inflation.",
        "We should not prematurely declare victory over inflation.",
    ],
    background="Former Kansas state bank commissioner and community banker. First Governor to dissent since 2005.",
    expertise_areas=["banking regulation", "community banking", "rural finance"],
)

CHRISTOPHER_WALLER = FOMCMember(
    name="Christopher J. Waller",
    short_name="waller",
    role=Role.GOVERNOR,
    bank="Board of Governors",
    is_voting_member=True,
    stance=Stance.HAWK,
    priorities=["price stability", "credibility", "forward guidance clarity"],
    communication_style=CommunicationStyle.DATA_DRIVEN,
    historical_dissents=0,
    key_concerns=[
        "inflation expectations",
        "wage-price dynamics",
        "policy credibility",
        "neutral rate estimation",
    ],
    notable_quotes=[
        "I want to see more good data before supporting a rate cut.",
        "Inflation is job one.",
    ],
    background="Academic economist, former research director at St. Louis Fed. Known for rigorous quantitative approach.",
    expertise_areas=["monetary theory", "inflation dynamics", "central bank communication"],
)

LISA_COOK = FOMCMember(
    name="Lisa D. Cook",
    short_name="cook",
    role=Role.GOVERNOR,
    bank="Board of Governors",
    is_voting_member=True,
    stance=Stance.DOVE,
    priorities=["maximum employment", "inclusive labor markets", "economic equity"],
    communication_style=CommunicationStyle.ACADEMIC,
    historical_dissents=0,
    key_concerns=[
        "labor market inclusivity",
        "innovation and growth",
        "racial economic disparities",
    ],
    notable_quotes=[
        "A strong labor market benefits all Americans.",
    ],
    background="Michigan State University economist. Expert on innovation, economic history, and racial disparities.",
    expertise_areas=["labor markets", "innovation economics", "economic history"],
)

ADRIANA_KUGLER = FOMCMember(
    name="Adriana D. Kugler",
    short_name="kugler",
    role=Role.GOVERNOR,
    bank="Board of Governors",
    is_voting_member=True,
    stance=Stance.DOVE,
    priorities=["labor market health", "international perspectives", "price stability"],
    communication_style=CommunicationStyle.ACADEMIC,
    historical_dissents=0,
    key_concerns=[
        "employment dynamics",
        "international spillovers",
        "emerging market conditions",
    ],
    notable_quotes=[
        "Labor markets continue to show resilience.",
    ],
    background="Former World Bank chief economist. Expert in labor economics and development.",
    expertise_areas=["labor economics", "international development", "policy evaluation"],
)

MICHAEL_BARR = FOMCMember(
    name="Michael S. Barr",
    short_name="barr",
    role=Role.VICE_CHAIR_SUPERVISION,
    bank="Board of Governors",
    is_voting_member=True,
    stance=Stance.NEUTRAL,
    priorities=["financial stability", "bank supervision", "price stability"],
    communication_style=CommunicationStyle.MEASURED,
    historical_dissents=0,
    key_concerns=[
        "banking system resilience",
        "credit conditions",
        "financial stability risks",
    ],
    notable_quotes=[
        "A resilient banking system supports the economy.",
    ],
    background="Treasury official under Obama. Expert in financial regulation and consumer protection.",
    expertise_areas=["financial regulation", "banking supervision", "consumer finance"],
)

# Reserve Bank Presidents
JOHN_WILLIAMS = FOMCMember(
    name="John C. Williams",
    short_name="williams",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of New York",
    is_voting_member=True,  # NY Fed always votes
    voting_years=[],  # Always votes
    stance=Stance.NEUTRAL,
    priorities=["price stability", "neutral rate assessment", "communication clarity"],
    communication_style=CommunicationStyle.ACADEMIC,
    historical_dissents=0,
    key_concerns=[
        "r-star estimation",
        "inflation expectations",
        "monetary policy transmission",
    ],
    notable_quotes=[
        "We need to see sustained progress on inflation.",
    ],
    background="Career Fed economist, former SF Fed president. Known for r-star research.",
    expertise_areas=["monetary policy", "neutral rate estimation", "macroeconomic modeling"],
)

# 2024-2025 Rotating Voters (examples - these rotate annually)
AUSTAN_GOOLSBEE = FOMCMember(
    name="Austan D. Goolsbee",
    short_name="goolsbee",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of Chicago",
    is_voting_member=True,
    voting_years=[2024, 2026, 2028],  # Chicago alternates with Cleveland
    stance=Stance.DOVE,
    priorities=["maximum employment", "economic growth", "innovation"],
    communication_style=CommunicationStyle.DIRECT,
    historical_dissents=0,
    key_concerns=[
        "real economy conditions",
        "supply chain normalization",
        "productivity growth",
    ],
    notable_quotes=[
        "We need to look at the totality of the data.",
    ],
    background="Former Obama economic advisor. Known for accessible communication style.",
    expertise_areas=["behavioral economics", "public policy", "technology economics"],
)

RAPHAEL_BOSTIC = FOMCMember(
    name="Raphael W. Bostic",
    short_name="bostic",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of Atlanta",
    is_voting_member=True,
    voting_years=[2024, 2027],  # Group C: Atlanta/St.Louis/Dallas rotate every 3 years
    stance=Stance.NEUTRAL,
    priorities=["inclusive growth", "community development", "price stability"],
    communication_style=CommunicationStyle.MEASURED,
    historical_dissents=0,
    key_concerns=[
        "regional economic disparities",
        "housing affordability",
        "small business conditions",
    ],
    notable_quotes=[
        "We must consider how our policies affect all communities.",
    ],
    background="First African American regional Fed president. Former HUD official.",
    expertise_areas=["housing economics", "community development", "urban economics"],
)

MARY_DALY = FOMCMember(
    name="Mary C. Daly",
    short_name="daly",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of San Francisco",
    is_voting_member=True,
    voting_years=[2024, 2027],  # Group D: Minneapolis/KC/SF rotate every 3 years
    stance=Stance.DOVE,
    priorities=["labor market", "price stability", "policy communication"],
    communication_style=CommunicationStyle.DIRECT,
    historical_dissents=0,
    key_concerns=[
        "labor market health",
        "wage dynamics",
        "West Coast economic conditions",
    ],
    notable_quotes=[
        "The labor market remains our north star.",
    ],
    background="Career Fed economist, rose through research ranks at SF Fed.",
    expertise_areas=["labor economics", "wage dynamics", "regional economics"],
)

ALBERTO_MUSALEM = FOMCMember(
    name="Alberto G. Musalem",
    short_name="musalem",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of St. Louis",
    is_voting_member=True,
    voting_years=[2025, 2028],  # Group C: Atlanta/St.Louis/Dallas rotate every 3 years
    stance=Stance.HAWK,
    priorities=["price stability", "inflation credibility", "financial conditions"],
    communication_style=CommunicationStyle.DATA_DRIVEN,
    historical_dissents=0,
    key_concerns=[
        "inflation persistence",
        "policy credibility",
        "financial market conditions",
    ],
    notable_quotes=[
        "Returning inflation to target is paramount.",
    ],
    background="Former NY Fed markets group and Tudor Investment Corp.",
    expertise_areas=["financial markets", "monetary policy implementation", "inflation"],
)

BETH_HAMMACK = FOMCMember(
    name="Beth M. Hammack",
    short_name="hammack",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of Cleveland",
    is_voting_member=True,
    voting_years=[2025, 2027, 2029],  # Cleveland alternates with Chicago
    stance=Stance.NEUTRAL,
    priorities=["price stability", "banking system health", "data dependency"],
    communication_style=CommunicationStyle.MEASURED,
    historical_dissents=0,
    key_concerns=[
        "inflation trajectory",
        "banking conditions",
        "regional manufacturing",
    ],
    notable_quotes=[
        "Policy must remain nimble as conditions evolve.",
    ],
    background="Former Goldman Sachs CFO and treasurer.",
    expertise_areas=["financial markets", "banking", "corporate finance"],
)

JEFFREY_SCHMID = FOMCMember(
    name="Jeffrey R. Schmid",
    short_name="schmid",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of Kansas City",
    is_voting_member=True,
    voting_years=[2025, 2028],  # KC rotates with Minneapolis
    stance=Stance.HAWK,
    priorities=["price stability", "agricultural economy", "regional banking"],
    communication_style=CommunicationStyle.DIRECT,
    historical_dissents=0,
    key_concerns=[
        "inflation persistence",
        "agricultural conditions",
        "energy sector",
    ],
    notable_quotes=[
        "Inflation remains too high for comfort.",
    ],
    background="Former banker with extensive community banking experience.",
    expertise_areas=["banking", "agricultural finance", "regional economics"],
)

SUSAN_COLLINS = FOMCMember(
    name="Susan M. Collins",
    short_name="collins",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of Boston",
    is_voting_member=True,
    voting_years=[2025, 2028],  # Boston rotates with Philly, Richmond
    stance=Stance.NEUTRAL,
    priorities=["price stability", "labor markets", "international trade"],
    communication_style=CommunicationStyle.ACADEMIC,
    historical_dissents=0,
    key_concerns=[
        "inflation expectations",
        "labor supply constraints",
        "global economic conditions",
    ],
    notable_quotes=[
        "We need patience as policy works through the economy.",
    ],
    background="Former provost at University of Michigan. International economics expert.",
    expertise_areas=["international economics", "trade policy", "labor markets"],
)

THOMAS_BARKIN = FOMCMember(
    name="Thomas I. Barkin",
    short_name="barkin",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of Richmond",
    is_voting_member=True,
    voting_years=[2024, 2027],  # Group A: Boston/Philly/Richmond rotate every 3 years
    stance=Stance.NEUTRAL,
    priorities=["price stability", "business conditions", "regional economy"],
    communication_style=CommunicationStyle.PRAGMATIC,
    historical_dissents=0,
    key_concerns=[
        "business sentiment",
        "hiring conditions",
        "supply chain",
    ],
    notable_quotes=[
        "I talk to businesses every day - they inform my view.",
    ],
    background="Former McKinsey partner. Business-focused approach to policy.",
    expertise_areas=["business strategy", "management consulting", "regional economics"],
)

LORIE_LOGAN = FOMCMember(
    name="Lorie K. Logan",
    short_name="logan",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of Dallas",
    is_voting_member=True,
    voting_years=[2026, 2029],  # Group C: Atlanta/St.Louis/Dallas rotate every 3 years
    stance=Stance.HAWK,
    priorities=["price stability", "balance sheet policy", "energy sector"],
    communication_style=CommunicationStyle.DATA_DRIVEN,
    historical_dissents=0,
    key_concerns=[
        "inflation control",
        "balance sheet normalization",
        "energy markets",
    ],
    notable_quotes=[
        "We should not take the progress on inflation for granted.",
    ],
    background="Former NY Fed markets chief. Expert in monetary policy implementation.",
    expertise_areas=["monetary policy operations", "financial markets", "balance sheet policy"],
)

NEEL_KASHKARI = FOMCMember(
    name="Neel Kashkari",
    short_name="kashkari",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of Minneapolis",
    is_voting_member=True,
    voting_years=[2026, 2029],
    stance=Stance.DOVE,
    priorities=["maximum employment", "financial regulation", "economic inclusion"],
    communication_style=CommunicationStyle.DIRECT,
    historical_dissents=2,
    key_concerns=[
        "labor market health",
        "too-big-to-fail banks",
        "economic opportunity",
    ],
    notable_quotes=[
        "We should err on the side of keeping people employed.",
        "Inflation is coming down - let's not overreact.",
    ],
    background="Former Treasury official during 2008 crisis (TARP). Goldman Sachs alum.",
    expertise_areas=["financial crisis management", "banking regulation", "public policy"],
)

PATRICK_HARKER = FOMCMember(
    name="Patrick T. Harker",
    short_name="harker",
    role=Role.PRESIDENT,
    bank="Federal Reserve Bank of Philadelphia",
    is_voting_member=True,
    voting_years=[2026, 2029],  # Group A: Boston/Philly/Richmond rotate every 3 years
    stance=Stance.NEUTRAL,
    priorities=["price stability", "fintech innovation", "workforce development"],
    communication_style=CommunicationStyle.ACADEMIC,
    historical_dissents=0,
    key_concerns=[
        "inflation trajectory",
        "technology disruption",
        "labor force participation",
    ],
    notable_quotes=[
        "We need to be thoughtful about the path forward.",
    ],
    background="Former University of Delaware president. Engineering and economics background.",
    expertise_areas=["fintech", "workforce development", "regional economics"],
)

# All FOMC members
FOMC_MEMBERS: list[FOMCMember] = [
    # Board of Governors (7 - always vote)
    JEROME_POWELL,
    PHILIP_JEFFERSON,
    MICHELLE_BOWMAN,
    CHRISTOPHER_WALLER,
    LISA_COOK,
    ADRIANA_KUGLER,
    MICHAEL_BARR,
    # Reserve Bank Presidents (5 vote each year besides NY)
    JOHN_WILLIAMS,      # NY - always votes
    AUSTAN_GOOLSBEE,    # Chicago - 2024, 2026, 2028 (alternates with Cleveland)
    BETH_HAMMACK,       # Cleveland - 2025, 2027, 2029 (alternates with Chicago)
    RAPHAEL_BOSTIC,     # Atlanta - 2024, 2027
    MARY_DALY,          # San Francisco - 2024, 2027
    ALBERTO_MUSALEM,    # St. Louis - 2024, 2027
    JEFFREY_SCHMID,     # Kansas City - 2025, 2028
    SUSAN_COLLINS,      # Boston - 2025, 2028
    THOMAS_BARKIN,      # Richmond - 2024, 2027
    PATRICK_HARKER,     # Philadelphia - 2025, 2028
    LORIE_LOGAN,        # Dallas - 2026, 2029
    NEEL_KASHKARI,      # Minneapolis - 2026, 2029
]

# Quick lookup by short name
MEMBERS_BY_SHORT_NAME: dict[str, FOMCMember] = {m.short_name: m for m in FOMC_MEMBERS}


def get_member_by_name(name: str) -> FOMCMember | None:
    """
    Get a member by their short name or full name.

    Args:
        name: Short name (e.g., 'powell') or full name (e.g., 'Jerome H. Powell')

    Returns:
        FOMCMember or None if not found
    """
    # Try short name first
    name_lower = name.lower().strip()
    if name_lower in MEMBERS_BY_SHORT_NAME:
        return MEMBERS_BY_SHORT_NAME[name_lower]

    # Try full name match
    for member in FOMC_MEMBERS:
        if member.name.lower() == name_lower:
            return member

    # Try partial match on last name
    for member in FOMC_MEMBERS:
        last_name = member.name.split()[-1].lower()
        if last_name == name_lower:
            return member

    return None


def get_voting_members(year: int) -> list[FOMCMember]:
    """
    Get all voting members for a given year.

    Args:
        year: The year to check voting eligibility

    Returns:
        List of members with voting rights that year
    """
    return [m for m in FOMC_MEMBERS if m.is_voting_in_year(year)]


def get_members_by_stance(stance: Stance) -> list[FOMCMember]:
    """
    Get all members with a given policy stance.

    Args:
        stance: HAWK, DOVE, or NEUTRAL

    Returns:
        List of members with that stance
    """
    return [m for m in FOMC_MEMBERS if m.stance == stance]
