"""
Multi-Strategy Quantitative Engine for MONEY For HONEY.
STRICT SPOT LONG-ONLY ACCUMULATION ENGINE:
1. Dynamic Breakout Momentum (BUY Only when ADX > 25 & Bullish Breakout).
2. Statistical Mean-Reversion (BUY Only at Lower Band Dip & RSI <= 44.0).
3. ZERO Naked Shorting (Eliminates counter-trend short losses on Binance Spot).
4. Dynamic 2.0x ATR Stop Loss & 1:2.2 Take Profit.
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
        min_sl_distance_pct: float = 0.015,  # Minimum 1.5% SL floor
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

    def evaluate_breakout(self, regime: MarketRegime) -> TradeSignal | None:
        """
        Strategi Momentum Tren (ADX > 25):
        HANYA EKSEKUSI BUY ketika harga menembus Donchian High dalam tren Bullish.
        (Menolak semua sinyal breakdown Short agar tidak melawan tren).
        """
        if regime.adx < 25.0:
            return None

        # PURE LONG BREAKOUT
        if (
            regime.current_price >= regime.donchian_high_20
            and regime.trend_direction == "BULLISH"
            and regime.rsi_14 < 70.0  # Tidak beli jika sudah overbought parah
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
                    f"Bullish Breakout at ${regime.donchian_high_20:.2f} | "
                    f"ADX={regime.adx:.1f} (Strong Trend) | RSI={regime.rsi_14:.1f}"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return None

    def evaluate_mean_reversion(self, regime: MarketRegime) -> TradeSignal | None:
        """
        Strategi Sideways / Ranging (ADX < 24):
        HANYA EKSEKUSI BUY di area lembah diskon (Lower 35% BB Band & RSI <= 44.0).
        """
        if regime.adx >= 24.0:
            return None

        # Definisi area lembah: sepertiga bawah rentang Bollinger Bands
        band_width = regime.upper_bollinger - regime.lower_bollinger
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
                    f"Oversold Dip at ${entry:.2f} | "
                    f"RSI={regime.rsi_14:.1f} (<= 44.0) | Lower BB Pullback Setup"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return None

    def generate_signal(
        self, regime: MarketRegime, spread_pct: float = 0.0002
    ) -> TradeSignal | None:
        """Hanya memproduksi sinyal BUY berprobabilitas tinggi."""
        if regime.regime == "BREAKOUT":
            return self.evaluate_breakout(regime)
        elif regime.regime == "MEAN_REVERSION":
            return self.evaluate_mean_reversion(regime)
        return None


strategy_engine = MultiStrategyEngine()
