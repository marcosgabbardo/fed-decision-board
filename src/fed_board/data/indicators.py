"""Economic indicators data models and FRED series mappings."""

from datetime import date
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, computed_field


class Trend(str, Enum):
    """Trend direction for an indicator."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value

    @property
    def arrow(self) -> str:
        """Get arrow symbol for the trend."""
        return {
            Trend.RISING: "↑",
            Trend.FALLING: "↓",
            Trend.STABLE: "→",
            Trend.UNKNOWN: "?",
        }[self]

    @property
    def color(self) -> str:
        """Get color for Rich formatting."""
        return {
            Trend.RISING: "green",
            Trend.FALLING: "red",
            Trend.STABLE: "yellow",
            Trend.UNKNOWN: "dim",
        }[self]


class IndicatorValue(BaseModel):
    """A single indicator with current value, history, and trend."""

    current: float | None = Field(default=None, description="Current/latest value")
    previous: float | None = Field(default=None, description="Previous period value")
    two_periods_ago: float | None = Field(default=None, description="Value from 2 periods ago")
    trend: Trend = Field(default=Trend.UNKNOWN, description="Trend direction")
    data_date: date | None = Field(default=None, description="Date of the current value")

    @classmethod
    def from_values(
        cls,
        values: list[float],
        dates: list[date] | None = None,
        threshold_pct: float = 0.5,
    ) -> "IndicatorValue":
        """
        Create an IndicatorValue from a list of values (most recent first).

        Args:
            values: List of values, most recent first
            dates: Optional list of dates corresponding to values
            threshold_pct: Percentage change threshold for stable vs rising/falling
        """
        if not values:
            return cls()

        current = values[0] if len(values) > 0 else None
        previous = values[1] if len(values) > 1 else None
        two_ago = values[2] if len(values) > 2 else None
        data_date = dates[0] if dates and len(dates) > 0 else None

        # Calculate trend
        trend = Trend.UNKNOWN
        if current is not None and previous is not None:
            if previous != 0:
                pct_change = ((current - previous) / abs(previous)) * 100
                if pct_change > threshold_pct:
                    trend = Trend.RISING
                elif pct_change < -threshold_pct:
                    trend = Trend.FALLING
                else:
                    trend = Trend.STABLE
            elif current > previous:
                trend = Trend.RISING
            elif current < previous:
                trend = Trend.FALLING
            else:
                trend = Trend.STABLE

        return cls(
            current=current,
            previous=previous,
            two_periods_ago=two_ago,
            trend=trend,
            data_date=data_date,
        )

    def format(self, suffix: str = "", signed: bool = False) -> str:
        """Format the value with trend indicator."""
        if self.current is None:
            return "N/A"
        if signed:
            val_str = f"{self.current:+.1f}{suffix}"
        else:
            val_str = f"{self.current:.1f}{suffix}"
        return f"{val_str} {self.trend.arrow}"

    def format_with_history(self, suffix: str = "", signed: bool = False) -> str:
        """Format with previous values shown."""
        if self.current is None:
            return "N/A"

        def fmt(v: float | None) -> str:
            if v is None:
                return "?"
            if signed:
                return f"{v:+.1f}"
            return f"{v:.1f}"

        current_str = fmt(self.current) + suffix
        history = []
        if self.previous is not None:
            history.append(fmt(self.previous))
        if self.two_periods_ago is not None:
            history.append(fmt(self.two_periods_ago))

        if history:
            return f"{current_str} {self.trend.arrow} (prev: {', '.join(history)})"
        return f"{current_str} {self.trend.arrow}"


# FRED series IDs for each indicator
FRED_SERIES: dict[str, str] = {
    # Inflation
    "cpi_yoy": "CPIAUCSL",  # Consumer Price Index for All Urban Consumers
    "core_cpi_yoy": "CPILFESL",  # CPI Less Food and Energy
    "pce_yoy": "PCEPI",  # Personal Consumption Expenditures Price Index
    "core_pce_yoy": "PCEPILFE",  # PCE Excluding Food and Energy
    # Employment
    "unemployment_rate": "UNRATE",  # Unemployment Rate
    "nonfarm_payrolls": "PAYEMS",  # Total Nonfarm Payrolls
    "labor_force_participation": "CIVPART",  # Labor Force Participation Rate
    "wage_growth_yoy": "CES0500000003",  # Average Hourly Earnings
    "job_openings": "JTSJOL",  # Job Openings: Total Nonfarm
    "initial_claims": "ICSA",  # Initial Claims
    # Economic Activity
    "gdp_growth": "A191RL1Q225SBEA",  # Real GDP Percent Change (QoQ annualized)
    "real_gdp_growth": "GDPC1",  # Real GDP Level
    "retail_sales_mom": "RSXFS",  # Retail Sales: Retail Trade
    "industrial_production": "INDPRO",  # Industrial Production Index
    "capacity_utilization": "TCU",  # Capacity Utilization
    "housing_starts": "HOUST",  # Housing Starts
    # Financial Markets
    "fed_funds_rate": "FEDFUNDS",  # Effective Federal Funds Rate
    "fed_funds_target_upper": "DFEDTARU",  # Fed Funds Target Range Upper
    "fed_funds_target_lower": "DFEDTARL",  # Fed Funds Target Range Lower
    "treasury_10y": "DGS10",  # 10-Year Treasury Constant Maturity Rate
    "treasury_2y": "DGS2",  # 2-Year Treasury Constant Maturity Rate
    "treasury_3m": "DGS3MO",  # 3-Month Treasury Constant Maturity Rate
    "sp500": "SP500",  # S&P 500 Index
    # Expectations & Sentiment
    "michigan_sentiment": "UMCSENT",  # University of Michigan Consumer Sentiment
    "breakeven_5y": "T5YIE",  # 5-Year Breakeven Inflation Rate
    "breakeven_10y": "T10YIE",  # 10-Year Breakeven Inflation Rate
}


# Data frequency for each series
FRED_FREQUENCIES: dict[str, str] = {
    # Monthly data
    "cpi_yoy": "monthly",
    "core_cpi_yoy": "monthly",
    "pce_yoy": "monthly",
    "core_pce_yoy": "monthly",
    "unemployment_rate": "monthly",
    "nonfarm_payrolls": "monthly",
    "labor_force_participation": "monthly",
    "wage_growth_yoy": "monthly",
    "job_openings": "monthly",
    "retail_sales_mom": "monthly",
    "industrial_production": "monthly",
    "capacity_utilization": "monthly",
    "housing_starts": "monthly",
    "michigan_sentiment": "monthly",
    # Quarterly data
    "gdp_growth": "quarterly",
    "real_gdp_growth": "quarterly",
    # Weekly data
    "initial_claims": "weekly",
    # Daily data
    "fed_funds_rate": "daily",
    "fed_funds_target_upper": "daily",
    "fed_funds_target_lower": "daily",
    "treasury_10y": "daily",
    "treasury_2y": "daily",
    "treasury_3m": "daily",
    "sp500": "daily",
    "breakeven_5y": "daily",
    "breakeven_10y": "daily",
}


class InflationIndicators(BaseModel):
    """Inflation-related economic indicators."""

    cpi_yoy: Annotated[
        float | None,
        Field(description="Consumer Price Index, Year-over-Year %"),
    ] = None
    core_cpi_yoy: Annotated[
        float | None,
        Field(description="Core CPI (ex food & energy), Year-over-Year %"),
    ] = None
    pce_yoy: Annotated[
        float | None,
        Field(description="PCE Price Index, Year-over-Year %"),
    ] = None
    core_pce_yoy: Annotated[
        float | None,
        Field(description="Core PCE (Fed's preferred measure), Year-over-Year %"),
    ] = None

    @computed_field
    @property
    def inflation_summary(self) -> str:
        """Generate a summary of inflation indicators."""
        parts = []
        if self.core_pce_yoy is not None:
            parts.append(f"Core PCE: {self.core_pce_yoy:.1f}%")
        if self.cpi_yoy is not None:
            parts.append(f"CPI: {self.cpi_yoy:.1f}%")
        return ", ".join(parts) if parts else "Data unavailable"


class EmploymentIndicators(BaseModel):
    """Employment-related economic indicators."""

    unemployment_rate: Annotated[
        float | None,
        Field(description="Unemployment Rate %"),
    ] = None
    nonfarm_payrolls: Annotated[
        float | None,
        Field(description="Nonfarm Payrolls (thousands)"),
    ] = None
    nonfarm_payrolls_change: Annotated[
        float | None,
        Field(description="Monthly change in Nonfarm Payrolls (thousands)"),
    ] = None
    labor_force_participation: Annotated[
        float | None,
        Field(description="Labor Force Participation Rate %"),
    ] = None
    wage_growth_yoy: Annotated[
        float | None,
        Field(description="Average Hourly Earnings, Year-over-Year %"),
    ] = None
    job_openings: Annotated[
        float | None,
        Field(description="Job Openings (thousands)"),
    ] = None
    initial_claims: Annotated[
        float | None,
        Field(description="Initial Jobless Claims"),
    ] = None

    @computed_field
    @property
    def employment_summary(self) -> str:
        """Generate a summary of employment indicators."""
        parts = []
        if self.unemployment_rate is not None:
            parts.append(f"Unemployment: {self.unemployment_rate:.1f}%")
        if self.nonfarm_payrolls_change is not None:
            parts.append(f"Jobs added: {self.nonfarm_payrolls_change:+.0f}K")
        if self.wage_growth_yoy is not None:
            parts.append(f"Wage growth: {self.wage_growth_yoy:.1f}%")
        return ", ".join(parts) if parts else "Data unavailable"


class ActivityIndicators(BaseModel):
    """Economic activity indicators."""

    gdp_growth: Annotated[
        float | None,
        Field(description="GDP Growth Rate (QoQ annualized) %"),
    ] = None
    real_gdp_growth: Annotated[
        float | None,
        Field(description="Real GDP Growth Rate %"),
    ] = None
    retail_sales_mom: Annotated[
        float | None,
        Field(description="Retail Sales, Month-over-Month %"),
    ] = None
    industrial_production: Annotated[
        float | None,
        Field(description="Industrial Production Index"),
    ] = None
    industrial_production_yoy: Annotated[
        float | None,
        Field(description="Industrial Production, Year-over-Year %"),
    ] = None
    capacity_utilization: Annotated[
        float | None,
        Field(description="Capacity Utilization %"),
    ] = None
    housing_starts: Annotated[
        float | None,
        Field(description="Housing Starts (thousands, annual rate)"),
    ] = None

    @computed_field
    @property
    def activity_summary(self) -> str:
        """Generate a summary of economic activity indicators."""
        parts = []
        if self.gdp_growth is not None:
            parts.append(f"GDP: {self.gdp_growth:+.1f}%")
        if self.retail_sales_mom is not None:
            parts.append(f"Retail sales: {self.retail_sales_mom:+.1f}% MoM")
        return ", ".join(parts) if parts else "Data unavailable"


class MarketIndicators(BaseModel):
    """Financial market indicators."""

    fed_funds_rate: Annotated[
        float | None,
        Field(description="Effective Federal Funds Rate %"),
    ] = None
    fed_funds_target_upper: Annotated[
        float | None,
        Field(description="Fed Funds Target Range Upper Bound %"),
    ] = None
    fed_funds_target_lower: Annotated[
        float | None,
        Field(description="Fed Funds Target Range Lower Bound %"),
    ] = None
    treasury_10y: Annotated[
        float | None,
        Field(description="10-Year Treasury Yield %"),
    ] = None
    treasury_2y: Annotated[
        float | None,
        Field(description="2-Year Treasury Yield %"),
    ] = None
    treasury_3m: Annotated[
        float | None,
        Field(description="3-Month Treasury Yield %"),
    ] = None
    sp500: Annotated[
        float | None,
        Field(description="S&P 500 Index Level"),
    ] = None
    sp500_ytd: Annotated[
        float | None,
        Field(description="S&P 500 Year-to-Date Return %"),
    ] = None

    @computed_field
    @property
    def yield_curve_spread(self) -> float | None:
        """Calculate 10Y-2Y spread (negative = inverted)."""
        if self.treasury_10y is not None and self.treasury_2y is not None:
            return self.treasury_10y - self.treasury_2y
        return None

    @computed_field
    @property
    def is_yield_curve_inverted(self) -> bool | None:
        """Check if yield curve is inverted."""
        spread = self.yield_curve_spread
        if spread is not None:
            return spread < 0
        return None

    @computed_field
    @property
    def current_rate_range(self) -> str | None:
        """Get current fed funds target range as string."""
        if self.fed_funds_target_lower is not None and self.fed_funds_target_upper is not None:
            return f"{self.fed_funds_target_lower:.2f}-{self.fed_funds_target_upper:.2f}%"
        return None


class ExpectationsIndicators(BaseModel):
    """Market expectations and sentiment indicators."""

    michigan_sentiment: Annotated[
        float | None,
        Field(description="University of Michigan Consumer Sentiment Index"),
    ] = None
    breakeven_5y: Annotated[
        float | None,
        Field(description="5-Year Breakeven Inflation Rate %"),
    ] = None
    breakeven_10y: Annotated[
        float | None,
        Field(description="10-Year Breakeven Inflation Rate %"),
    ] = None

    @computed_field
    @property
    def inflation_expectations_anchored(self) -> bool | None:
        """Check if inflation expectations appear anchored (near 2%)."""
        if self.breakeven_5y is not None:
            return 1.5 <= self.breakeven_5y <= 2.5
        return None


class EconomicIndicators(BaseModel):
    """Complete snapshot of economic indicators for FOMC decision-making."""

    # Data date
    as_of_date: date = Field(
        ...,
        description="Date of the economic snapshot",
    )

    # Indicator groups
    inflation: InflationIndicators = Field(
        default_factory=InflationIndicators,
        description="Inflation indicators",
    )
    employment: EmploymentIndicators = Field(
        default_factory=EmploymentIndicators,
        description="Employment indicators",
    )
    activity: ActivityIndicators = Field(
        default_factory=ActivityIndicators,
        description="Economic activity indicators",
    )
    markets: MarketIndicators = Field(
        default_factory=MarketIndicators,
        description="Financial market indicators",
    )
    expectations: ExpectationsIndicators = Field(
        default_factory=ExpectationsIndicators,
        description="Expectations and sentiment indicators",
    )

    # Trend data for key indicators
    trends: dict[str, IndicatorValue] = Field(
        default_factory=dict,
        description="Trend data with historical values for key indicators",
    )

    def _get_trend_str(self, key: str) -> str:
        """Get trend arrow for a key if available."""
        if key in self.trends and self.trends[key].trend != Trend.UNKNOWN:
            return f" {self.trends[key].trend.arrow}"
        return ""

    def _get_prev_str(self, key: str) -> str:
        """Get previous values string for a key if available."""
        if key not in self.trends:
            return ""
        t = self.trends[key]
        prev_vals = []
        if t.previous is not None:
            prev_vals.append(f"{t.previous:.1f}")
        if t.two_periods_ago is not None:
            prev_vals.append(f"{t.two_periods_ago:.1f}")
        if prev_vals:
            return f" (prev: {', '.join(prev_vals)})"
        return ""

    def to_briefing(self) -> str:
        """Generate a briefing document for FOMC members."""
        lines = [
            f"# Economic Briefing - As of {self.as_of_date.strftime('%B %d, %Y')}",
            "",
            "## Inflation",
            f"- Core PCE (Fed's preferred measure): {self._fmt(self.inflation.core_pce_yoy, '%')}{self._get_trend_str('core_pce_yoy')}{self._get_prev_str('core_pce_yoy')}",
            f"- Core CPI: {self._fmt(self.inflation.core_cpi_yoy, '%')}{self._get_trend_str('core_cpi_yoy')}{self._get_prev_str('core_cpi_yoy')}",
            f"- Headline CPI: {self._fmt(self.inflation.cpi_yoy, '%')}{self._get_trend_str('cpi_yoy')}{self._get_prev_str('cpi_yoy')}",
            f"- PCE Price Index: {self._fmt(self.inflation.pce_yoy, '%')}{self._get_trend_str('pce_yoy')}{self._get_prev_str('pce_yoy')}",
            "",
            "## Labor Market",
            f"- Unemployment Rate: {self._fmt(self.employment.unemployment_rate, '%')}{self._get_trend_str('unemployment_rate')}{self._get_prev_str('unemployment_rate')}",
            f"- Nonfarm Payrolls Change: {self._fmt(self.employment.nonfarm_payrolls_change, 'K', signed=True)}",
            f"- Labor Force Participation: {self._fmt(self.employment.labor_force_participation, '%')}{self._get_trend_str('labor_force_participation')}{self._get_prev_str('labor_force_participation')}",
            f"- Wage Growth (YoY): {self._fmt(self.employment.wage_growth_yoy, '%')}{self._get_trend_str('wage_growth_yoy')}{self._get_prev_str('wage_growth_yoy')}",
            f"- Job Openings: {self._fmt(self.employment.job_openings, 'K')}{self._get_trend_str('job_openings')}",
            "",
            "## Economic Activity",
            f"- GDP Growth (QoQ annualized): {self._fmt(self.activity.gdp_growth, '%', signed=True)}{self._get_trend_str('gdp_growth')}{self._get_prev_str('gdp_growth')}",
            f"- Retail Sales (MoM): {self._fmt(self.activity.retail_sales_mom, '%', signed=True)}{self._get_trend_str('retail_sales_mom')}",
            f"- Industrial Production (YoY): {self._fmt(self.activity.industrial_production_yoy, '%', signed=True)}{self._get_trend_str('industrial_production_yoy')}{self._get_prev_str('industrial_production_yoy')}",
            f"- Capacity Utilization: {self._fmt(self.activity.capacity_utilization, '%')}{self._get_trend_str('capacity_utilization')}",
            "",
            "## Financial Markets",
            f"- Current Fed Funds Target: {self.markets.current_rate_range or 'N/A'}",
            f"- 10-Year Treasury: {self._fmt(self.markets.treasury_10y, '%')}{self._get_trend_str('treasury_10y')}",
            f"- 2-Year Treasury: {self._fmt(self.markets.treasury_2y, '%')}{self._get_trend_str('treasury_2y')}",
            f"- 10Y-2Y Spread: {self._fmt(self.markets.yield_curve_spread, 'bps', mult=100, signed=True)}",
            f"- S&P 500 YTD: {self._fmt(self.markets.sp500_ytd, '%', signed=True)}",
            "",
            "## Expectations",
            f"- Consumer Sentiment: {self._fmt(self.expectations.michigan_sentiment)}{self._get_trend_str('michigan_sentiment')}{self._get_prev_str('michigan_sentiment')}",
            f"- 5-Year Breakeven Inflation: {self._fmt(self.expectations.breakeven_5y, '%')}{self._get_trend_str('breakeven_5y')}",
            f"- 10-Year Breakeven Inflation: {self._fmt(self.expectations.breakeven_10y, '%')}{self._get_trend_str('breakeven_10y')}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _fmt(
        value: float | None,
        suffix: str = "",
        mult: float = 1,
        signed: bool = False,
    ) -> str:
        """Format a value for display."""
        if value is None:
            return "N/A"
        val = value * mult
        if signed:
            return f"{val:+.1f}{suffix}"
        return f"{val:.1f}{suffix}"
