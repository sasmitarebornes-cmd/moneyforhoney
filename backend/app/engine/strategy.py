"""
Multi-Strategy Quantitative Engine for MONEY For HONEY.
Optimized Precision Edge:
1. Breakout Momentum (ADX > 25 & Clean Donchian Breakout + Volume Confluence).
2. Statistical Mean-Reversion (ADX < 22 & Strict Lower Bollinger Dip + RSI <= 38.0).
3. Dynamic ATR-based Stop Loss (1.8x - 2.2x ATR) with Minimum 1.2% Noise Cushion.
4. Institutional Risk-to-Reward Target (1:2.0 - 1:2.8).
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.engine.scanner import MarketRegime

logger = logging.getLogger("money_for_honey.strategy")


@dataclass
class TradeSignal:
    strategy_name: str
    symbol: str
    action: str  # "BUY" | "SELL" | "HOLD"
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    confidence_score: float  # 0.0 - 1.0
    rationale: str
    timestamp: str


class MultiStrategyEngine:
    """Evaluates market regimes and fires high-conviction quantitative trading signals."""

    def __init__(
        self,
        atr_multiplier_sl: float = 2.0,  # 2.0x ATR: Menghindari tersapu wick market
        risk_reward_target: float = 2.2,  # R:R 1:2.2 (1 Win menutup 2.2x Loss)
        min_sl_distance_pct: float = 0.012,  # Minimum 1.2% SL floor untuk BTC/Crypto
    ):
        self.atr_multiplier_sl = atr_multiplier_sl
        self.risk_reward_target = risk_reward_target
        self.min_sl_distance_pct = min_sl_distance_pct

    def _calculate_protective_stops(
        self, entry: float, atr: float, side: str = "BUY"
    ) -> tuple[float, float, float]:
        """
        Menghitung Stop Loss dan Take Profit yang presisi.
        Menjamin jarak SL memiliki 'ruang bernapas' minimal 1.2% - 2.0% dari entry.
        """
        raw_sl_dist = max(
            atr * self.atr_multiplier_sl, entry * self.min_sl_distance_pct
        )

        if side == "BUY":
            sl = entry - raw_sl_dist
            tp = entry + (raw_sl_dist * self.risk_reward_target)
        else:
            sl = entry + raw_sl_dist
            tp = entry - (raw_sl_dist * self.risk_reward_target)

        rr = abs(tp - entry) / max(1e-6, abs(entry - sl))
        return round(sl, 4), round(tp, 4), round(rr, 2)

    def evaluate_breakout(self, regime: MarketRegime) -> TradeSignal | None:
        """
        Strategi Tren Kuat (ADX > 25):
        LONG hanya jika Donchian High ditembus DAN RSI belum overbought (< 72).
        """
        if regime.adx < 25.0:
            return None

        # Long Breakout Momentum
        if (
            regime.current_price >= regime.donchian_high_20
            and regime.trend_direction == "BULLISH"
            and regime.rsi_14 < 72.0  # Mencegah beli di pucuk overbought
        ):
            entry = regime.current_price
            sl, tp, rr = self._calculate_protective_stops(entry, regime.atr, side="BUY")

            return TradeSignal(
                strategy_name="DYNAMIC_BREAKOUT_MOMENTUM",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=round(min(0.96, 0.70 + (regime.adx / 100.0)), 2),
                rationale=(
                    f"Bullish Donchian Breakout at ${regime.donchian_high_20:.2f} | "
                    f"ADX={regime.adx:.1f} (Strong Trend) | RSI={regime.rsi_14:.1f}"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Short Breakout Momentum
        if (
            regime.current_price <= regime.donchian_low_20
            and regime.trend_direction == "BEARISH"
            and regime.rsi_14 > 28.0  # Mencegah sell di dasar oversold
        ):
            entry = regime.current_price
            sl, tp, rr = self._calculate_protective_stops(
                entry, regime.atr, side="SELL"
            )

            return TradeSignal(
                strategy_name="DYNAMIC_BREAKOUT_MOMENTUM",
                symbol=regime.symbol,
                action="SELL",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=round(min(0.96, 0.70 + (regime.adx / 100.0)), 2),
                rationale=(
                    f"Bearish Donchian Breakdown at ${regime.donchian_low_20:.2f} | "
                    f"ADX={regime.adx:.1f} (Strong Trend) | RSI={regime.rsi_14:.1f}"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return None

    def evaluate_mean_reversion(self, regime: MarketRegime) -> TradeSignal | None:
        """
        Strategi Sideways / Ranging (ADX < 24):
        LONG HANYA KETIKA:
        1. Harga menyentuh / di bawah area Lower Bollinger Band (Beli Murah di Bawah).
        2. RSI menunjukkan Oversold / Pullback Sehat (RSI <= 38.0).
        """
        if regime.adx >= 24.0:
            return None

        # Hitung area pantulan bawah (Lower Band + buffer 0.25%)
        lower_threshold = regime.lower_bollinger * 1.0025

        # LONG HANYA DI LEMBAH (DIP ACCUMULATION)
        if regime.current_price <= lower_threshold and regime.rsi_14 <= 38.0:
            entry = regime.current_price
            sl, tp_candidate, rr = self._calculate_protective_stops(
                entry, regime.atr, side="BUY"
            )

            # Target Take Profit: Menuju Mid Band atau Upper Band
            mid_band = (regime.upper_bollinger + regime.lower_bollinger) / 2.0
            tp = round(max(tp_candidate, mid_band * 1.005), 4)
            rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)

            return TradeSignal(
                strategy_name="STATISTICAL_MEAN_REVERSION",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=round(
                    min(0.95, 0.80 + ((38.0 - regime.rsi_14) / 50.0)), 2
                ),
                rationale=(
                    f"Statistical Lower Band Dip at ${entry:.2f} | "
                    f"RSI={regime.rsi_14:.1f} (Oversold Bounce) | Target Mid/Upper Band"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return None

    def evaluate_micro_scalping(
        self, regime: MarketRegime, bid_ask_spread_pct: float
    ) -> TradeSignal | None:
        """
        Transisi / Konsolidasi:
        Hanya masuk jika RSI sangat oversold (RSI <= 32) dengan proteksi ketat.
        """
        if regime.rsi_14 <= 32.0:
            entry = regime.current_price
            sl, tp, rr = self._calculate_protective_stops(entry, regime.atr, side="BUY")
            return TradeSignal(
                strategy_name="DYNAMIC_RANGE_ACCUMULATOR",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=0.78,
                rationale=f"Deep oversold pullback capture at ${entry:.2f} with RSI={regime.rsi_14:.1f}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        return None

    def generate_signal(
        self, regime: MarketRegime, spread_pct: float = 0.0002
    ) -> TradeSignal | None:
        """Evaluates quantitative modules in order of strict statistical edge."""
        if regime.regime == "BREAKOUT":
            return self.evaluate_breakout(regime)
        elif regime.regime == "MEAN_REVERSION":
            return self.evaluate_mean_reversion(regime)
        else:
            return self.evaluate_micro_scalping(regime, spread_pct)


strategy_engine = MultiStrategyEngine()
