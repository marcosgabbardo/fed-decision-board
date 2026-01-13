"""Tests for economic indicators."""

from datetime import date

import pytest

from fed_board.data.indicators import (
    FRED_FREQUENCIES,
    FRED_SERIES,
    EconomicIndicators,
    InflationIndicators,
    MarketIndicators,
)


class TestFREDSeries:
    """Tests for FRED series mappings."""

    def test_all_series_have_frequencies(self) -> None:
        """Test that all series have frequency defined."""
        for key in FRED_SERIES:
            assert key in FRED_FREQUENCIES, f"Missing frequency for {key}"

    def test_key_series_exist(self) -> None:
        """Test that key economic series are defined."""
        required_series = [
            "cpi_yoy",
            "core_pce_yoy",
            "unemployment_rate",
            "fed_funds_rate",
            "treasury_10y",
        ]
        for series in required_series:
            assert series in FRED_SERIES, f"Missing series: {series}"


class TestInflationIndicators:
    """Tests for inflation indicators."""

    def test_inflation_summary(self) -> None:
        """Test inflation summary generation."""
        indicators = InflationIndicators(
            cpi_yoy=3.2,
            core_cpi_yoy=3.0,
            pce_yoy=2.8,
            core_pce_yoy=2.6,
        )
        summary = indicators.inflation_summary
        assert "Core PCE: 2.6%" in summary
        assert "CPI: 3.2%" in summary

    def test_partial_data(self) -> None:
        """Test with partial data."""
        indicators = InflationIndicators(core_pce_yoy=2.5)
        summary = indicators.inflation_summary
        assert "Core PCE: 2.5%" in summary

    def test_no_data(self) -> None:
        """Test with no data."""
        indicators = InflationIndicators()
        assert indicators.inflation_summary == "Data unavailable"


class TestMarketIndicators:
    """Tests for market indicators."""

    def test_yield_curve_spread(self) -> None:
        """Test yield curve spread calculation."""
        indicators = MarketIndicators(
            treasury_10y=4.5,
            treasury_2y=5.0,
        )
        assert indicators.yield_curve_spread == -0.5
        assert indicators.is_yield_curve_inverted is True

    def test_normal_yield_curve(self) -> None:
        """Test normal (non-inverted) yield curve."""
        indicators = MarketIndicators(
            treasury_10y=5.0,
            treasury_2y=4.5,
        )
        assert indicators.yield_curve_spread == 0.5
        assert indicators.is_yield_curve_inverted is False

    def test_current_rate_range(self) -> None:
        """Test current rate range formatting."""
        indicators = MarketIndicators(
            fed_funds_target_lower=5.25,
            fed_funds_target_upper=5.50,
        )
        assert indicators.current_rate_range == "5.25-5.50%"


class TestEconomicIndicators:
    """Tests for complete economic indicators."""

    def test_create_indicators(self) -> None:
        """Test creating economic indicators."""
        indicators = EconomicIndicators(
            as_of_date=date(2024, 1, 15),
            inflation=InflationIndicators(core_pce_yoy=2.6),
            markets=MarketIndicators(fed_funds_rate=5.33),
        )
        assert indicators.as_of_date == date(2024, 1, 15)
        assert indicators.inflation.core_pce_yoy == 2.6
        assert indicators.markets.fed_funds_rate == 5.33

    def test_to_briefing(self) -> None:
        """Test briefing generation."""
        indicators = EconomicIndicators(
            as_of_date=date(2024, 1, 15),
            inflation=InflationIndicators(
                cpi_yoy=3.0,
                core_pce_yoy=2.6,
            ),
            markets=MarketIndicators(
                fed_funds_target_lower=5.25,
                fed_funds_target_upper=5.50,
            ),
        )
        briefing = indicators.to_briefing()
        assert "Economic Briefing" in briefing
        assert "Inflation" in briefing
        assert "January 15, 2024" in briefing
