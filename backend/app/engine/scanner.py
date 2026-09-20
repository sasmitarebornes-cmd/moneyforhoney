"""
Dynamic Market Scanner & Regime Classifier.
Computes technical indicators (ATR, ADX, RSI, Donchian, Bollinger Bands)
and classifies the current market regime:
- ADX > 25: Trend / Breakout Regime (High directional momentum)
- ADX < 20: Mean-Reversion Regime (Consolidation & range-bound)
- 20 <= ADX <= 25: Transition / Neutral Regime
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("money_for_honey.scanner")


@dataclass
class MarketRegime:
    symbol: str
    current_price: float
    adx: float
    atr: float
    atr_pct: float
    regime: str  # "BREAKOUT" | "MEAN_REVERSION" | "TRANSITION"
    trend_direction: str  # "BULLISH" | "BEARISH" | "SIDEWAYS"
    rsi_14: float
    upper_bollinger: float
    lower_bollinger: float
    donchian_high_20: float
    donchian_low_20: float


class MarketScanner:
    """Async Market Scanner analyzing volatility and directional movement index."""

    def __init__(self, adx_period: int = 14, atr_period: int = 14):
        self.adx_period = adx_period
        self.atr_period = atr_period

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculates Average True Range using Wilder's exponential smoothing."""
        high = df["high"]
        low = df["low"]
        close_prev = df["close"].shift(1)

        tr1 = high - low
        tr2 = (high - close_prev).abs()
        tr3 = (low - close_prev).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1.0 / self.atr_period, adjust=False).mean()
        return atr

    def calculate_adx(self, df: pd.DataFrame) -> pd.Series:
        """Calculates Average Directional Index (ADX) over N periods."""
        high = df["high"]
        low = df["low"]
        close_prev = df["close"].shift(1)

        # True Range
        tr = pd.concat([
            high - low,
            (high - close_prev).abs(),
            (low - close_prev).abs()
        ], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1.0 / self.adx_period, adjust=False).mean()

        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        plus_di = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1.0 / self.adx_period, adjust=False).mean() / (atr + 1e-9))
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1.0 / self.adx_period, adjust=False).mean() / (atr + 1e-9))

        dx = 100 * ((plus_di - minus_di).abs() / ((plus_di + minus_di) + 1e-9))
        adx = dx.ewm(alpha=1.0 / self.adx_period, adjust=False).mean()
        return adx

    def calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Calculates standard Relative Strength Index."""
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        return 100 - (100 / (1 + rs))

    def classify_market(self, symbol: str, ohlcv_data: List[List[float]]) -> MarketRegime:
        """
        Parses OHLCV list [[timestamp, open, high, low, close, volume], ...],
        computes technical indicators, and classifies regime.
        """
        df = pd.DataFrame(ohlcv_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = df.astype(float)

        close = df["close"]
        current_price = float(close.iloc[-1])

        # Indicator Series
        atr_series = self.calculate_atr(df)
        adx_series = self.calculate_adx(df)
        rsi_series = self.calculate_rsi(close, period=14)

        current_atr = float(atr_series.iloc[-1])
        current_adx = float(adx_series.iloc[-1])
        current_rsi = float(rsi_series.iloc[-1])
        atr_pct = (current_atr / current_price) * 100.0

        # Bollinger Bands (20 periods, 2.0 std)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_bb = float((sma20 + 2.0 * std20).iloc[-1])
        lower_bb = float((sma20 - 2.0 * std20).iloc[-1])

        # Donchian Channels (20 periods)
        donchian_high = float(df["high"].rolling(window=20).max().iloc[-2])  # Previous 20 highs
        donchian_low = float(df["low"].rolling(window=20).min().iloc[-2])

        # Regime Decision Boundary
        if current_adx > 25.0:
            regime = "BREAKOUT"
            trend_direction = "BULLISH" if current_price > float(sma20.iloc[-1]) else "BEARISH"
        elif current_adx < 20.0:
            regime = "MEAN_REVERSION"
            trend_direction = "SIDEWAYS"
        else:
            regime = "TRANSITION"
            trend_direction = "SIDEWAYS"

        return MarketRegime(
            symbol=symbol,
            current_price=round(current_price, 4),
            adx=round(current_adx, 2),
            atr=round(current_atr, 4),
            atr_pct=round(atr_pct, 2),
            regime=regime,
            trend_direction=trend_direction,
            rsi_14=round(current_rsi, 2),
            upper_bollinger=round(upper_bb, 4),
            lower_bollinger=round(lower_bb, 4),
            donchian_high_20=round(donchian_high, 4),
            donchian_low_20=round(donchian_low, 4),
        )


market_scanner = MarketScanner()
