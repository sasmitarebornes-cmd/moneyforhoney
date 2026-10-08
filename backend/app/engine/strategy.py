"""
Multi-Strategy Quantitative Engine for MONEY For HONEY — Peaceful Trading Edition.
FOCUS: Quality over Quantity. High R:R, Wide Stops, Strict Filters.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

try:
    from app.engine.scanner import MarketRegime
except ImportError:

    class MarketRegime:
        pass


logger = logging.getLogger("money_for_honey.strategy")


@dataclass
class TradeSignal:
    strategy_name: str
    symbol: str
    action: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    confidence_score: float
    rationale: str
    timestamp: str
    atr_multiplier_used: float = 4.0
    max_risk_pct: float = 0.8


@dataclass
class PositionTracker:
    max_positions: int = 2
    recent_trades: deque = field(default_factory=lambda: deque(maxlen=20))
    daily_pnl: float = 0.0
    daily_loss_limit: float = -2.0

    def add_trade(self, symbol: str, pnl: float) -> None:
        self.recent_trades.append(
            {
                "symbol": symbol,
                "pnl": pnl,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "active": True,
            }
        )
        self.daily_pnl += pnl

    def is_correlated(self, symbol: str, threshold: int = 1) -> bool:
        groups = {
            "L1": ["SOL", "AVAX", "NEAR", "SUI", "APT", "SEI"],
            "L2": ["ETH", "ARB", "OP", "MATIC", "BASE"],
            "MEME": ["DOGE", "SHIB", "PEPE", "WIF", "HYPE"],
            "EXCHANGE": ["BNB", "OKB", "CRO"],
        }

        symbol_base = symbol.split("/")[0].upper()
        target_group = None

        # PERF102 FIX: Use .values() since we only need the values, not the keys
        for coins in groups.values():
            if symbol_base in coins:
                target_group = coins
                break

        if not target_group:
            return False

        count = sum(
            1
            for t in self.recent_trades
            if t.get("active") and t["symbol"].split("/")[0].upper() in target_group
        )
        return count >= threshold

    def should_trade(self) -> bool:
        if self.daily_pnl <= self.daily_loss_limit:
            logger.warning(
                "⚠️ Daily loss limit reached: %.2f%%. Halting trading.", self.daily_pnl
            )
            return False

        active_count = sum(1 for t in self.recent_trades if t.get("active", False))
        if active_count >= self.max_positions:
            logger.warning(
                "⚠️ Max concurrent positions reached: %d/%d",
                active_count,
                self.max_positions,
            )
            return False

        return True


class MultiStrategyEngine:
    def __init__(
        self,
        atr_multiplier_sl: float = 4.0,
        risk_reward_target: float = 3.0,
        min_sl_distance_pct: float = 0.065,
        max_position_risk_pct: float = 0.8,
        max_daily_loss_pct: float = 2.0,
        max_concurrent_positions: int = 2,
        min_confidence_score: float = 0.80,
        min_adx_for_breakout: float = 28.0,
        max_adx_for_mean_reversion: float = 22.0,
        rsi_capitulation_max: float = 28.0,
        rsi_mean_reversion_max: float = 40.0,
    ):
        self.atr_multiplier_sl = atr_multiplier_sl
        self.risk_reward_target = risk_reward_target
        self.min_sl_distance_pct = min_sl_distance_pct
        self.max_position_risk_pct = max_position_risk_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_concurrent_positions = max_concurrent_positions
        self.min_confidence_score = min_confidence_score

        self.min_adx_for_breakout = min_adx_for_breakout
        self.max_adx_for_mean_reversion = max_adx_for_mean_reversion
        self.rsi_capitulation_max = rsi_capitulation_max
        self.rsi_mean_reversion_max = rsi_mean_reversion_max

        self.position_tracker = PositionTracker()
        self.trading_hours = {"start": 8, "end": 23}

    def _calculate_protective_stops(
        self, entry: float, atr: float, atr_multiplier: float | None = None
    ) -> tuple[float, float, float]:
        mult = atr_multiplier or self.atr_multiplier_sl
        raw_sl_dist = max(atr * mult, entry * self.min_sl_distance_pct)
        sl = round(entry - raw_sl_dist, 4)
        tp = round(entry + (raw_sl_dist * self.risk_reward_target), 4)
        rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)
        return sl, tp, rr

    def _check_primary_trend(self, regime: MarketRegime) -> bool:
        # SIM103 FIX: Return the negated condition directly without unnecessary if/else blocks
        return not (
            (regime.adx > 35.0 and regime.trend_direction == "BEARISH")
            or regime.rsi_14 < 20.0
        )

    def evaluate_capitulation_dip(self, regime: MarketRegime) -> TradeSignal | None:
        if not self.position_tracker.should_trade():
            return None
        if not self._check_primary_trend(regime):
            return None
        if regime.rsi_14 > self.rsi_capitulation_max:
            return None

        band_width = max(1e-4, regime.upper_bollinger - regime.lower_bollinger)
        deep_discount_zone = regime.lower_bollinger + (band_width * 0.45)

        if regime.current_price <= deep_discount_zone:
            entry = regime.current_price
            sl, tp_candidate, rr = self._calculate_protective_stops(
                entry, regime.atr, atr_multiplier=5.0
            )

            mid_band = (regime.upper_bollinger + regime.lower_bollinger) / 2.0
            tp = round(max(tp_candidate, mid_band * 1.03), 4)
            rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)

            confidence = round(
                min(0.95, 0.80 + ((self.rsi_capitulation_max - regime.rsi_14) / 20.0)),
                2,
            )

            if confidence < self.min_confidence_score:
                return None

            return TradeSignal(
                strategy_name="PEACEFUL_CAPITULATION",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=confidence,
                rationale=f"Extreme Panic (RSI={regime.rsi_14:.1f}) | Wide SL (5x ATR)",
                timestamp=datetime.now(timezone.utc).isoformat(),
                atr_multiplier_used=5.0,
                max_risk_pct=self.max_position_risk_pct,
            )
        return None

    def evaluate_breakout(self, regime: MarketRegime) -> TradeSignal | None:
        if not self.position_tracker.should_trade():
            return None
        if regime.trend_direction != "BULLISH":
            return None
        if regime.adx < self.min_adx_for_breakout:
            return None
        if self.position_tracker.is_correlated(regime.symbol):
            return None

        if regime.current_price >= regime.donchian_high_20 and regime.rsi_14 < 70.0:
            entry = regime.current_price
            sl, tp, rr = self._calculate_protective_stops(entry, regime.atr)

            confidence = round(min(0.92, 0.80 + (regime.adx / 100.0)), 2)
            if confidence < self.min_confidence_score:
                return None

            return TradeSignal(
                strategy_name="PEACEFUL_BREAKOUT",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=confidence,
                rationale=f"Strong Breakout (ADX={regime.adx:.1f}) | R:R {rr}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                atr_multiplier_used=self.atr_multiplier_sl,
                max_risk_pct=self.max_position_risk_pct,
            )
        return None

    def evaluate_mean_reversion(self, regime: MarketRegime) -> TradeSignal | None:
        if not self.position_tracker.should_trade():
            return None
        if regime.adx > self.max_adx_for_mean_reversion:
            return None
        if self.position_tracker.is_correlated(regime.symbol):
            return None

        band_width = max(1e-4, regime.upper_bollinger - regime.lower_bollinger)
        lower_zone = regime.lower_bollinger + (band_width * 0.35)

        if (
            regime.current_price <= lower_zone
            and regime.rsi_14 <= self.rsi_mean_reversion_max
        ):
            entry = regime.current_price
            sl, tp_candidate, rr = self._calculate_protective_stops(entry, regime.atr)

            mid_band = (regime.upper_bollinger + regime.lower_bollinger) / 2.0
            tp = round(max(tp_candidate, mid_band * 1.02), 4)
            rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)

            confidence = round(
                min(
                    0.88, 0.75 + ((self.rsi_mean_reversion_max - regime.rsi_14) / 30.0)
                ),
                2,
            )
            if confidence < self.min_confidence_score:
                return None

            return TradeSignal(
                strategy_name="PEACEFUL_REVERSION",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=confidence,
                rationale=f"Sideways Dip (ADX={regime.adx:.1f}, RSI={regime.rsi_14:.1f})",
                timestamp=datetime.now(timezone.utc).isoformat(),
                atr_multiplier_used=self.atr_multiplier_sl,
                max_risk_pct=self.max_position_risk_pct,
            )
        return None

    def generate_signal(
        self, regime: MarketRegime, spread_pct: float = 0.0002
    ) -> TradeSignal | None:
        if not self.position_tracker.should_trade():
            return None

        cap_signal = self.evaluate_capitulation_dip(regime)
        if cap_signal:
            return cap_signal

        if regime.adx >= self.min_adx_for_breakout:
            breakout_signal = self.evaluate_breakout(regime)
            if breakout_signal:
                return breakout_signal

        return self.evaluate_mean_reversion(regime)

    def update_daily_pnl(self, pnl: float) -> None:
        self.position_tracker.daily_pnl += pnl


strategy_engine = MultiStrategyEngine()
