"""FRED API client for fetching economic data."""

import asyncio
from datetime import date, timedelta
from typing import Any

import httpx

from fed_board.config import Settings, get_settings
from fed_board.data.cache import FREDCache
from fed_board.data.indicators import (
    FRED_FREQUENCIES,
    FRED_SERIES,
    ActivityIndicators,
    EconomicIndicators,
    EmploymentIndicators,
    ExpectationsIndicators,
    IndicatorValue,
    InflationIndicators,
    MarketIndicators,
)


class FREDAPIError(Exception):
    """Exception raised for FRED API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FREDClient:
    """Async client for the FRED API."""

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize the FRED client.

        Args:
            settings: Application settings (uses defaults if not provided)
        """
        self.settings = settings or get_settings()
        self.api_key = self.settings.fred_api_key
        self.cache = FREDCache(
            cache_dir=self.settings.fred_cache_dir,
            ttl_monthly=self.settings.fred_cache_ttl_monthly,
            ttl_daily=self.settings.fred_cache_ttl_daily,
        )

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make a request to the FRED API.

        Args:
            endpoint: API endpoint (e.g., 'series/observations')
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            FREDAPIError: If the API returns an error
        """
        url = f"{self.BASE_URL}/{endpoint}"
        request_params = {
            "api_key": self.api_key,
            "file_type": "json",
            **(params or {}),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=request_params)

            if response.status_code != 200:
                raise FREDAPIError(
                    f"FRED API error: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()

            # Check for FRED error messages
            if "error_message" in data:
                raise FREDAPIError(data["error_message"])

            return data

    async def get_series(
        self,
        series_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
        sort_order: str = "desc",
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get observations for a FRED series.

        Args:
            series_id: FRED series ID
            start_date: Start date for observations
            end_date: End date for observations
            limit: Maximum number of observations
            sort_order: 'asc' or 'desc'
            use_cache: Whether to use cached data

        Returns:
            List of observations
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(series_id)
            if cached is not None:
                return cached

        # Set default dates if not provided
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        params = {
            "series_id": series_id,
            "observation_start": start_date.isoformat(),
            "observation_end": end_date.isoformat(),
            "limit": limit,
            "sort_order": sort_order,
        }

        data = await self._request("series/observations", params)
        observations = data.get("observations", [])

        # Cache the result
        frequency = FRED_FREQUENCIES.get(
            self._get_indicator_key(series_id),
            "monthly",
        )
        self.cache.set(series_id, observations, frequency)

        return observations

    async def get_latest_value(
        self,
        series_id: str,
        use_cache: bool = True,
    ) -> float | None:
        """
        Get the latest value for a FRED series.

        Args:
            series_id: FRED series ID
            use_cache: Whether to use cached data

        Returns:
            Latest value or None if not available
        """
        observations = await self.get_series(series_id, limit=1, use_cache=use_cache)

        if not observations:
            return None

        value = observations[0].get("value")
        if value is None or value == ".":
            return None

        try:
            return float(value)
        except ValueError:
            return None

    async def get_yoy_change(
        self,
        series_id: str,
        use_cache: bool = True,
    ) -> float | None:
        """
        Calculate year-over-year percentage change for a series.

        Args:
            series_id: FRED series ID
            use_cache: Whether to use cached data

        Returns:
            YoY percentage change or None
        """
        observations = await self.get_series(
            series_id,
            start_date=date.today() - timedelta(days=400),
            limit=15,
            sort_order="desc",
            use_cache=use_cache,
        )

        if len(observations) < 12:
            return None

        try:
            current_value = float(observations[0]["value"])
            # Find observation from ~12 months ago
            year_ago_value = float(observations[12]["value"])

            if year_ago_value == 0:
                return None

            return ((current_value - year_ago_value) / year_ago_value) * 100
        except (ValueError, IndexError, KeyError):
            return None

    async def get_mom_change(
        self,
        series_id: str,
        use_cache: bool = True,
    ) -> float | None:
        """
        Calculate month-over-month percentage change for a series.

        Args:
            series_id: FRED series ID
            use_cache: Whether to use cached data

        Returns:
            MoM percentage change or None
        """
        observations = await self.get_series(
            series_id,
            start_date=date.today() - timedelta(days=90),
            limit=3,
            sort_order="desc",
            use_cache=use_cache,
        )

        if len(observations) < 2:
            return None

        try:
            current_value = float(observations[0]["value"])
            previous_value = float(observations[1]["value"])

            if previous_value == 0:
                return None

            return ((current_value - previous_value) / previous_value) * 100
        except (ValueError, IndexError, KeyError):
            return None

    async def get_indicator_with_trend(
        self,
        series_id: str,
        num_periods: int = 3,
        use_cache: bool = True,
    ) -> IndicatorValue:
        """
        Get an indicator value with historical values and trend.

        Args:
            series_id: FRED series ID
            num_periods: Number of periods to fetch for trend
            use_cache: Whether to use cached data

        Returns:
            IndicatorValue with current, previous values and trend
        """
        observations = await self.get_series(
            series_id,
            start_date=date.today() - timedelta(days=365),
            limit=num_periods + 2,  # Get a few extra in case of missing data
            sort_order="desc",
            use_cache=use_cache,
        )

        values = []
        dates = []
        for obs in observations[:num_periods]:
            val = obs.get("value")
            if val is not None and val != ".":
                try:
                    values.append(float(val))
                    if obs.get("date"):
                        dates.append(date.fromisoformat(obs["date"]))
                except ValueError:
                    continue

        return IndicatorValue.from_values(values, dates if dates else None)

    async def get_yoy_with_trend(
        self,
        series_id: str,
        use_cache: bool = True,
    ) -> IndicatorValue:
        """
        Calculate YoY change with trend (3 periods of YoY values).

        Args:
            series_id: FRED series ID
            use_cache: Whether to use cached data

        Returns:
            IndicatorValue with YoY values and trend
        """
        observations = await self.get_series(
            series_id,
            start_date=date.today() - timedelta(days=500),
            limit=18,  # Need 15+ for 3 YoY calculations
            sort_order="desc",
            use_cache=use_cache,
        )

        if len(observations) < 13:
            return IndicatorValue()

        yoy_values = []
        dates = []

        # Calculate YoY for the last 3 periods
        for i in range(min(3, len(observations) - 12)):
            try:
                current = float(observations[i]["value"])
                year_ago = float(observations[i + 12]["value"])
                if year_ago != 0:
                    yoy = ((current - year_ago) / year_ago) * 100
                    yoy_values.append(yoy)
                    if observations[i].get("date"):
                        dates.append(date.fromisoformat(observations[i]["date"]))
            except (ValueError, IndexError, KeyError):
                continue

        return IndicatorValue.from_values(yoy_values, dates if dates else None)

    async def get_economic_indicators(
        self,
        as_of_date: date | None = None,
        use_cache: bool = True,
    ) -> EconomicIndicators:
        """
        Fetch all economic indicators for FOMC decision-making.

        Args:
            as_of_date: Date for the snapshot (defaults to today)
            use_cache: Whether to use cached data

        Returns:
            Complete EconomicIndicators snapshot
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Fetch all data concurrently
        tasks = {
            # Inflation (YoY)
            "cpi_yoy": self.get_yoy_change(FRED_SERIES["cpi_yoy"], use_cache),
            "core_cpi_yoy": self.get_yoy_change(FRED_SERIES["core_cpi_yoy"], use_cache),
            "pce_yoy": self.get_yoy_change(FRED_SERIES["pce_yoy"], use_cache),
            "core_pce_yoy": self.get_yoy_change(FRED_SERIES["core_pce_yoy"], use_cache),
            # Employment
            "unemployment_rate": self.get_latest_value(FRED_SERIES["unemployment_rate"], use_cache),
            "nonfarm_payrolls": self.get_latest_value(FRED_SERIES["nonfarm_payrolls"], use_cache),
            "nonfarm_payrolls_mom": self.get_mom_change(FRED_SERIES["nonfarm_payrolls"], use_cache),
            "labor_force_participation": self.get_latest_value(
                FRED_SERIES["labor_force_participation"], use_cache
            ),
            "wage_growth_yoy": self.get_yoy_change(FRED_SERIES["wage_growth_yoy"], use_cache),
            "job_openings": self.get_latest_value(FRED_SERIES["job_openings"], use_cache),
            "initial_claims": self.get_latest_value(FRED_SERIES["initial_claims"], use_cache),
            # Activity
            "gdp_growth": self.get_latest_value(FRED_SERIES["gdp_growth"], use_cache),
            "retail_sales_mom": self.get_mom_change(FRED_SERIES["retail_sales_mom"], use_cache),
            "industrial_production": self.get_latest_value(
                FRED_SERIES["industrial_production"], use_cache
            ),
            "industrial_production_yoy": self.get_yoy_change(
                FRED_SERIES["industrial_production"], use_cache
            ),
            "capacity_utilization": self.get_latest_value(
                FRED_SERIES["capacity_utilization"], use_cache
            ),
            "housing_starts": self.get_latest_value(FRED_SERIES["housing_starts"], use_cache),
            # Markets
            "fed_funds_rate": self.get_latest_value(FRED_SERIES["fed_funds_rate"], use_cache),
            "fed_funds_target_upper": self.get_latest_value(
                FRED_SERIES["fed_funds_target_upper"], use_cache
            ),
            "fed_funds_target_lower": self.get_latest_value(
                FRED_SERIES["fed_funds_target_lower"], use_cache
            ),
            "treasury_10y": self.get_latest_value(FRED_SERIES["treasury_10y"], use_cache),
            "treasury_2y": self.get_latest_value(FRED_SERIES["treasury_2y"], use_cache),
            "treasury_3m": self.get_latest_value(FRED_SERIES["treasury_3m"], use_cache),
            "sp500": self.get_latest_value(FRED_SERIES["sp500"], use_cache),
            # Expectations
            "michigan_sentiment": self.get_latest_value(
                FRED_SERIES["michigan_sentiment"], use_cache
            ),
            "breakeven_5y": self.get_latest_value(FRED_SERIES["breakeven_5y"], use_cache),
            "breakeven_10y": self.get_latest_value(FRED_SERIES["breakeven_10y"], use_cache),
        }

        # Trend tasks for key indicators
        trend_tasks = {
            # Inflation trends (YoY values)
            "trend_cpi_yoy": self.get_yoy_with_trend(FRED_SERIES["cpi_yoy"], use_cache),
            "trend_core_cpi_yoy": self.get_yoy_with_trend(FRED_SERIES["core_cpi_yoy"], use_cache),
            "trend_pce_yoy": self.get_yoy_with_trend(FRED_SERIES["pce_yoy"], use_cache),
            "trend_core_pce_yoy": self.get_yoy_with_trend(FRED_SERIES["core_pce_yoy"], use_cache),
            # Employment trends
            "trend_unemployment_rate": self.get_indicator_with_trend(FRED_SERIES["unemployment_rate"], 3, use_cache),
            "trend_labor_force_participation": self.get_indicator_with_trend(FRED_SERIES["labor_force_participation"], 3, use_cache),
            "trend_wage_growth_yoy": self.get_yoy_with_trend(FRED_SERIES["wage_growth_yoy"], use_cache),
            "trend_job_openings": self.get_indicator_with_trend(FRED_SERIES["job_openings"], 3, use_cache),
            # Activity trends
            "trend_gdp_growth": self.get_indicator_with_trend(FRED_SERIES["gdp_growth"], 3, use_cache),
            "trend_retail_sales_mom": self.get_indicator_with_trend(FRED_SERIES["retail_sales_mom"], 3, use_cache),
            "trend_industrial_production_yoy": self.get_yoy_with_trend(FRED_SERIES["industrial_production"], use_cache),
            "trend_capacity_utilization": self.get_indicator_with_trend(FRED_SERIES["capacity_utilization"], 3, use_cache),
            # Market trends
            "trend_treasury_10y": self.get_indicator_with_trend(FRED_SERIES["treasury_10y"], 5, use_cache),
            "trend_treasury_2y": self.get_indicator_with_trend(FRED_SERIES["treasury_2y"], 5, use_cache),
            # Expectations trends
            "trend_michigan_sentiment": self.get_indicator_with_trend(FRED_SERIES["michigan_sentiment"], 3, use_cache),
            "trend_breakeven_5y": self.get_indicator_with_trend(FRED_SERIES["breakeven_5y"], 5, use_cache),
            "trend_breakeven_10y": self.get_indicator_with_trend(FRED_SERIES["breakeven_10y"], 5, use_cache),
        }

        # Execute all tasks concurrently (both main and trend tasks)
        all_tasks = list(tasks.values()) + list(trend_tasks.values())
        all_keys = list(tasks.keys()) + list(trend_tasks.keys())

        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Map results back to keys
        data = {}
        trends = {}
        for key, result in zip(all_keys, results):
            if isinstance(result, Exception):
                if key.startswith("trend_"):
                    trends[key.replace("trend_", "")] = IndicatorValue()
                else:
                    data[key] = None
            else:
                if key.startswith("trend_"):
                    trends[key.replace("trend_", "")] = result
                else:
                    data[key] = result

        # Calculate nonfarm payrolls change (in thousands)
        nonfarm_change = None
        if data.get("nonfarm_payrolls_mom") is not None and data.get("nonfarm_payrolls") is not None:
            # Convert percentage change to absolute change in thousands
            nonfarm_change = (data["nonfarm_payrolls_mom"] / 100) * data["nonfarm_payrolls"]

        # Build the indicators object
        return EconomicIndicators(
            as_of_date=as_of_date,
            inflation=InflationIndicators(
                cpi_yoy=data.get("cpi_yoy"),
                core_cpi_yoy=data.get("core_cpi_yoy"),
                pce_yoy=data.get("pce_yoy"),
                core_pce_yoy=data.get("core_pce_yoy"),
            ),
            employment=EmploymentIndicators(
                unemployment_rate=data.get("unemployment_rate"),
                nonfarm_payrolls=data.get("nonfarm_payrolls"),
                nonfarm_payrolls_change=nonfarm_change,
                labor_force_participation=data.get("labor_force_participation"),
                wage_growth_yoy=data.get("wage_growth_yoy"),
                job_openings=data.get("job_openings"),
                initial_claims=data.get("initial_claims"),
            ),
            activity=ActivityIndicators(
                gdp_growth=data.get("gdp_growth"),
                retail_sales_mom=data.get("retail_sales_mom"),
                industrial_production=data.get("industrial_production"),
                industrial_production_yoy=data.get("industrial_production_yoy"),
                capacity_utilization=data.get("capacity_utilization"),
                housing_starts=data.get("housing_starts"),
            ),
            markets=MarketIndicators(
                fed_funds_rate=data.get("fed_funds_rate"),
                fed_funds_target_upper=data.get("fed_funds_target_upper"),
                fed_funds_target_lower=data.get("fed_funds_target_lower"),
                treasury_10y=data.get("treasury_10y"),
                treasury_2y=data.get("treasury_2y"),
                treasury_3m=data.get("treasury_3m"),
                sp500=data.get("sp500"),
            ),
            expectations=ExpectationsIndicators(
                michigan_sentiment=data.get("michigan_sentiment"),
                breakeven_5y=data.get("breakeven_5y"),
                breakeven_10y=data.get("breakeven_10y"),
            ),
            trends=trends,
        )

    def _get_indicator_key(self, series_id: str) -> str:
        """Get the indicator key from a FRED series ID."""
        for key, sid in FRED_SERIES.items():
            if sid == series_id:
                return key
        return ""

    def clear_cache(self) -> int:
        """Clear all cached data."""
        return self.cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()
