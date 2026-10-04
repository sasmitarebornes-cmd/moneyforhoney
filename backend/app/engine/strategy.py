"""
Multi-Strategy Quantitative Engine for MONEY For HONEY — Predator Money Hunter Edition.
STRICT SPOT LONG-ONLY ACCUMULATION ENGINE:
1. Extreme Capitulation Dip Accumulation (BUY on Oversold Panic RSI <= 32.0 regardless of ADX).
2. Dynamic Breakout Momentum (BUY Only when ADX >= 24.0 & Bullish Breakout).
3. Statistical Mean-Reversion Dip (BUY on Lower Band Pullback & RSI <= 44.0).
4. ZERO Naked Shorting (100% Spot Capital Preservation).
5. Dynamic 2.0x ATR Stop Loss & 1:2.2 Take Profit (Golden Rules Compliance).
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
    action: str  # "BUY" | "HOLD" (No naked SELL on Spot)
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    confidence_score: float  # 0.0 - 1.0
    rationale: str
    timestamp: str


class MultiStrategyEngine:
    """Evaluates market regimes and fires high-conviction quantitative SPOT LONG trading signals."""

    def __init__(
        self,
        atr_multiplier_sl: float = 2.0,  # 2.0x ATR buffer
        risk_reward_target: float = 2.2,  # R:R 1:2.2 Target
        min_sl_distance_pct: float = 0.018,  # Minimum 1.8% SL floor for volatility wicks
    ):
        self.atr_multiplier_sl = atr_multiplier_sl
        self.risk_reward_target = risk_reward_target
        self.min_sl_distance_pct = min_sl_distance_pct

    def _calculate_protective_stops(
        self, entry: float, atr: float
    ) -> tuple[float, float, float]:
        """Menghitung level SL dan TP presisi khusus posisi BUY (Spot Long)."""
        raw_sl_dist = max(
            atr * self.atr_multiplier_sl, entry * self.min_sl_distance_pct
        )
        sl = round(entry - raw_sl_dist, 4)
        tp = round(entry + (raw_sl_dist * self.risk_reward_target), 4)
        rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)
        return sl, tp, rr

    def evaluate_capitulation_dip(self, regime: MarketRegime) -> TradeSignal | None:
        """
        Strategi Predator: Capitulation Dip Hunter (RSI <= 32.0).
        BYPASS BATASAN ADX:
        Ketika pasar mengalami dump tajam, harga diskon ekstrim (misal DOGE RSI 10, XRP 11, BTC 19).
        Membeli di lembah Lower Bollinger Band dengan potensi rebound V-Shape reversal.
        """
        # Syarat Utama: Diskon Ekstrim Oversold
        if regime.rsi_14 > 32.0:
            return None

        # Zona harga: berada di 45% rentang bawah Bollinger Bands atau menembus Lower BB
        band_width = max(1e-4, regime.upper_bollinger - regime.lower_bollinger)
        deep_discount_zone = regime.lower_bollinger + (band_width * 0.45)

        if regime.current_price <= deep_discount_zone:
            entry = regime.current_price
            sl, tp_candidate, rr = self._calculate_protective_stops(entry, regime.atr)

            # Target TP minimal menuju Mid Bollinger Band (SMA20) atau 1:2.2 R:R
            mid_band = (regime.upper_bollinger + regime.lower_bollinger) / 2.0
            tp = round(max(tp_candidate, mid_band * 1.01), 4)
            rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)

            confidence = round(min(0.98, 0.85 + ((32.0 - regime.rsi_14) / 40.0)), 2)

            return TradeSignal(
                strategy_name="SPOT_CAPITULATION_DIP",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=confidence,
                rationale=(
                    f"🔥 Extreme Capitulation Dip at ${entry:.2f} | "
                    f"RSI={regime.rsi_14:.1f} (<= 32.0 Super Oversold) | ADX={regime.adx:.1f} | "
                    f"Lower BB Discount Floor Setup"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return None

    def evaluate_breakout(self, regime: MarketRegime) -> TradeSignal | None:
        """
        Strategi Momentum Tren (ADX >= 24.0 & Bullish):
        HANYA EKSEKUSI BUY ketika harga menembus Donchian High dalam tren Bullish.
        """
        if regime.adx < 24.0:
            return None

        # PURE LONG BREAKOUT
        if (
            regime.current_price >= regime.donchian_high_20
            and regime.trend_direction == "BULLISH"
            and regime.rsi_14 < 72.0  # Mencegah beli di puncak mania
        ):
            entry = regime.current_price
            sl, tp, rr = self._calculate_protective_stops(entry, regime.atr)

            return TradeSignal(
                strategy_name="SPOT_BREAKOUT_MOMENTUM",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=round(min(0.96, 0.75 + (regime.adx / 100.0)), 2),
                rationale=(
                    f"🚀 Bullish Breakout at ${regime.donchian_high_20:.2f} | "
                    f"ADX={regime.adx:.1f} (Strong Trend) | RSI={regime.rsi_14:.1f}"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return None

    def evaluate_mean_reversion(self, regime: MarketRegime) -> TradeSignal | None:
        """
        Strategi Sideways / Transition (ADX < 28):
        HANYA EKSEKUSI BUY di area lembah diskon (Lower 35% BB Band & RSI <= 44.0).
        """
        if regime.adx >= 28.0:
            return None

        # Definisi area lembah: sepertiga bawah rentang Bollinger Bands
        band_width = max(1e-4, regime.upper_bollinger - regime.lower_bollinger)
        lower_zone = regime.lower_bollinger + (band_width * 0.35)

        # PURE DIP ACCUMULATION (BUY LOW ON PULLBACK)
        if regime.current_price <= lower_zone and regime.rsi_14 <= 44.0:
            entry = regime.current_price
            sl, tp_candidate, rr = self._calculate_protective_stops(entry, regime.atr)

            mid_band = (regime.upper_bollinger + regime.lower_bollinger) / 2.0
            tp = round(max(tp_candidate, mid_band * 1.008), 4)
            rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)

            return TradeSignal(
                strategy_name="SPOT_MEAN_REVERSION_DIP",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=round(
                    min(0.95, 0.80 + ((44.0 - regime.rsi_14) / 50.0)), 2
                ),
                rationale=(
                    f"⚡ Oversold Dip at ${entry:.2f} | "
                    f"RSI={regime.rsi_14:.1f} (<= 44.0) | Lower BB Pullback Setup"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return None

    def generate_signal(
        self, regime: MarketRegime, spread_pct: float = 0.0002
    ) -> TradeSignal | None:
        """
        Multi-Condition Predator Signal Dispatcher:
        1. Priority 1: Capitulation Dip Hunter (Snatch extreme oversold discounts RSI <= 32).
        2. Priority 2: Bullish Breakout Momentum (Ride upward trend surges).
        3. Priority 3: Statistical Mean Reversion (Accumulate calm pullbacks RSI <= 44).
        """
        # 1. Cek Diskon Ekstrim Capitulation Dip (Paling menguntungkan saat crash/dump)
        cap_signal = self.evaluate_capitulation_dip(regime)
        if cap_signal:
            return cap_signal

        # 2. Cek Momentum Breakout Bullish (Saat pasar bergerak naik kencang)
        if regime.adx >= 24.0 and regime.trend_direction == "BULLISH":
            breakout_signal = self.evaluate_breakout(regime)
            if breakout_signal:
                return breakout_signal

        # 3. Cek Mean Reversion Dip Normal (Saat pasar sideways / transition)
        return self.evaluate_mean_reversion(regime)


strategy_engine = MultiStrategyEngine()
