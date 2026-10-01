"""Unit tests for Event War Room schemas, calculation logic, and API contracts."""
from datetime import UTC, datetime
from app.schemas.war_room import (
    EventWarRoom,
    ExpectedMetricItem,
    ExpectedOutcomeProbabilities,
    SignalMatrixFactor,
    SignalStatus,
    UpcomingWarRoomItem,
    UpcomingWarRoomsResponse,
    WarRoomScenario,
    WarRoomVerdict,
)
from app.services.war_room import (
    calculate_atr,
    calculate_ema,
    calculate_rsi,
    slugify_event,
)


def test_slugify_event():
    dt = datetime(2026, 9, 18, 12, 30, tzinfo=UTC)
    slug = slugify_event("US Consumer Price Index (CPI) MoM", dt)
    assert slug == "us-consumer-price-index-cpi-mom-202609181230"


def test_technical_helpers():
    closes = [2600.0 + i for i in range(30)]
    rsi = calculate_rsi(closes, 14)
    assert rsi is not None
    assert 90.0 <= rsi <= 100.0  # Monotonically increasing closes have high RSI

    ema = calculate_ema(closes, 12)
    assert ema is not None
    assert ema > 2600.0

    highs = [c + 2.0 for c in closes]
    lows = [c - 2.0 for c in closes]
    atr = calculate_atr(highs, lows, closes, 14)
    assert atr is not None
    assert abs(atr - 4.0) < 0.1


def test_expected_outcome_probabilities_contract():
    probs = ExpectedOutcomeProbabilities(
        cool_pct=35.0,
        inline_pct=40.0,
        hot_pct=25.0,
        rationale="Calibrated from historical distribution.",
    )
    assert abs(probs.cool_pct + probs.inline_pct + probs.hot_pct - 100.0) < 0.01


def test_event_war_room_full_model_validation():
    now = datetime.now(UTC)
    war_room = EventWarRoom(
        event_id="us-cpi-20260918",
        event_name="US Consumer Price Index",
        timestamp=now,
        importance="high",
        country="US",
        currency="USD",
        current_xau_price=2650.50,
        market_context="Trading near ATH before release.",
        probabilities=ExpectedOutcomeProbabilities(
            cool_pct=30.0,
            inline_pct=45.0,
            hot_pct=25.0,
            rationale="Balanced consensus prior.",
        ),
        expected_metrics=[
            ExpectedMetricItem(name="Headline MoM", forecast=0.2, previous=0.2, actual=None, unit="%"),
            ExpectedMetricItem(name="Headline YoY", forecast=2.9, previous=3.0, actual=None, unit="%"),
        ],
        signal_matrix=[
            SignalMatrixFactor(factor="Trend vs SMA 200", status=SignalStatus.BULLISH, reason="Above 200 SMA", indicator_value="+35 pts"),
            SignalMatrixFactor(factor="RSI Momentum", status=SignalStatus.NEUTRAL, reason="RSI at 55.4", indicator_value="55.4"),
        ],
        scenarios=[
            WarRoomScenario(
                name="COOL / SOFT",
                probability=30.0,
                expected_direction=SignalStatus.BULLISH,
                target_range="$2670 – $2690",
                assumptions="Weaker inflation pulls USD lower",
                invalidation="Rejection below $2640",
                risk_note="Spread widening",
            ),
            WarRoomScenario(
                name="IN-LINE",
                probability=45.0,
                expected_direction=SignalStatus.NEUTRAL,
                target_range="$2645 – $2660",
                assumptions="Consensus met",
                invalidation="Breakout beyond 1.5 ATR",
                risk_note="Two-way whipsaw",
            ),
            WarRoomScenario(
                name="HOT",
                probability=25.0,
                expected_direction=SignalStatus.BEARISH,
                target_range="$2620 – $2635",
                assumptions="Hot print lifts USD",
                invalidation="Bounce above $2660",
                risk_note="Dip-buying support",
            ),
        ],
        verdict=WarRoomVerdict(
            dominant_scenario="IN-LINE",
            bias=SignalStatus.BULLISH,
            main_drivers=["Price above SMA 200", "AI model bullish"],
            main_risk="Initial slippage",
            invalidation_condition="Close below SMA 200",
        ),
        generated_at=now,
        cached=False,
    )

    assert war_room.event_id == "us-cpi-20260918"
    assert len(war_room.scenarios) == 3
    assert war_room.verdict.dominant_scenario == "IN-LINE"
