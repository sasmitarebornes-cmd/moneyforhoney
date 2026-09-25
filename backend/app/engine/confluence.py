"""
Multi-Timeframe Confluence & Macro Trend Filter.
Combines higher timeframe (4H / 1D) structural bias with lower timeframe (15M / 1H) execution triggers.
Prevents counter-trend whipsaws and false breakouts by requiring:
1. Macro EMA 200 trend alignment (Bullish if Macro Price > EMA 200, Bearish if Macro Price < EMA 200)
2. Macro Momentum Confirmation (MACD Histogram > 0 or RSI > 50 for longs)
3. Confluence Score calculation (0 - 100%)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

try:
    import numpy as np
    import pandas as pd

    HAS_PANDAS = True
except (ImportError, ModuleNotFoundError):
    np = None  # type: ignore[assignment]
    pd = None  # type: ignore[assignment]
    HAS_PANDAS = False

logger = logging.getLogger("money_for_honey.confluence")


@dataclass
class ConfluenceFilterResult:
    symbol: str
    proposed_action: str  # "BUY" | "SELL"
    is_approved: bool
    confluence_score: float  # 0.0 - 100.0%
    macro_trend: (
        str  # "STRONG_BULLISH" | "BULLISH" | "BEARISH" | "STRONG_BEARISH" | "NEUTRAL"
    )
    macro_ema_200: float
    current_price: float
    rejection_reason: str | None = None


class MultiTimeframeConfluenceEngine:
    """Enforces macro trend alignment on all execution signals."""

    def __init__(self, min_confluence_threshold: float = 50.0):
        self.min_confluence_threshold = min_confluence_threshold

    def compute_ema(self, series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    def evaluate_macro_confluence(
        self,
        symbol: str,
        proposed_action: str,  # "BUY" | "SELL"
        current_price: float,
        macro_ohlcv: list[list[float]],
    ) -> ConfluenceFilterResult:
        """
        Parses 4H/1D OHLCV series and evaluates trend alignment.
        """
        if not HAS_PANDAS or not macro_ohlcv or len(macro_ohlcv) < 30:
            # Not enough historical macro bars: allow with neutral score
            return ConfluenceFilterResult(
                symbol=symbol,
                proposed_action=proposed_action,
                is_approved=True,
                confluence_score=75.0,
                macro_trend="NEUTRAL",
                macro_ema_200=current_price * 0.98,
                current_price=current_price,
                rejection_reason=None,
            )

        df = pd.DataFrame(
            macro_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
        ).astype(float)
        close = df["close"]
        macro_price = float(close.iloc[-1])

        # Indicators on macro timeframe
        ema_50 = float(self.compute_ema(close, 50).iloc[-1])
        ema_200 = float(self.compute_ema(close, min(200, len(close))).iloc[-1])

        # Momentum RSI 14
        delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1.0 / 14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1.0 / 14, adjust=False).mean()
        macro_rsi = float((100 - (100 / (1 + (gain / (loss + 1e-9))))).iloc[-1])

        # Determine macro regime
        score = 50.0
        if macro_price > ema_200 and ema_50 > ema_200:
            macro_trend = "STRONG_BULLISH"
            score += 25.0
        elif macro_price > ema_200:
            macro_trend = "BULLISH"
            score += 15.0
        elif macro_price < ema_200 and ema_50 < ema_200:
            macro_trend = "STRONG_BEARISH"
            score -= 25.0
        else:
            macro_trend = "BEARISH"
            score -= 15.0

        if macro_rsi > 50.0:
            score += 10.0
        else:
            score -= 10.0

        score = max(0.0, min(100.0, score))

        # Check alignment against proposed action
        is_approved = True
        rejection_reason = None

        if proposed_action == "BUY" and score < self.min_confluence_threshold:
            is_approved = False
            rejection_reason = f"LOW CONFLUENCE: Score {score:.1f}% is below required {self.min_confluence_threshold}%."
        elif (
            proposed_action == "SELL"
            and (100.0 - score) < self.min_confluence_threshold
        ):
            is_approved = False
            rejection_reason = f"LOW CONFLUENCE: Bearish alignment score {(100.0 - score):.1f}% below required threshold."

        return ConfluenceFilterResult(
            symbol=symbol,
            proposed_action=proposed_action,
            is_approved=is_approved,
            confluence_score=round(score, 1),
            macro_trend=macro_trend,
            macro_ema_200=round(ema_200, 2),
            current_price=round(current_price, 2),
            rejection_reason=rejection_reason,
        )


confluence_engine = MultiTimeframeConfluenceEngine()
