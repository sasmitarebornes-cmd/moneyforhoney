"""
Multi-Strategy Quantitative Engine for MONEY For HONEY — Predator Money Hunter Edition.
ENHANCED: Added trend filters, wider stops, correlation checks, and safety mechanisms.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
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
    atr_multiplier_used: float = 3.5
    max_risk_pct: float = 1.0


@dataclass
class PositionTracker:
    """Tracks recent positions for correlation and risk management."""

    max_positions: int = 5
    recent_trades: deque = field(default_factory=lambda: deque(maxlen=20))
    daily_pnl: float = 0.0
    daily_loss_limit: float = -3.0  # -3% daily loss limit
    max_concurrent_positions: int = 3

    def add_trade(self, symbol: str, pnl: float):
        self.recent_trades.append(
            {
                "symbol": symbol,
                "pnl": pnl,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.daily_pnl += pnl

    def is_correlated(self, symbol: str, threshold: int = 2) -> bool:
        """Check if we already have too many positions in correlated assets."""
        # Define correlation groups
        correlation_groups = {
            "BTC": ["BTC", "ETH"],
            "ETH": ["ETH", "BTC"],
            "SOL": ["SOL"],
            "BNB": ["BNB"],
        }

        symbol_base = symbol.split("/")[0]
        correlated_symbols = correlation_groups.get(symbol_base, [symbol_base])

        # Count recent trades in correlated symbols
        count = sum(
            1
            for t in self.recent_trades
            if any(c in t["symbol"] for c in correlated_symbols)
        )
        return count >= threshold

    def should_trade(self) -> bool:
        """Check if we should allow new trades based on risk limits."""
        # Check daily loss limit
        if self.daily_pnl <= self.daily_loss_limit:
            logger.warning(
                f"⚠️ Daily loss limit reached: {self.daily_pnl:.2f}%. Halting trading."
            )
            return False

        # Check concurrent positions
        active_count = sum(1 for t in self.recent_trades if t.get("active", False))
        if active_count >= self.max_concurrent_positions:
            logger.warning(
                f"⚠️ Max concurrent positions reached: {active_count}/{self.max_concurrent_positions}"
            )
            return False

        return True


class MultiStrategyEngine:
    """Enhanced quantitative engine with safety filters and adaptive risk management."""

    def __init__(
        self,
        atr_multiplier_sl: float = 3.5,  # INCREASED: 2.5 -> 3.5 (avoid wick hunts)
        risk_reward_target: float = 2.5,  # INCREASED: 2.0 -> 2.5 (better R:R)
        min_sl_distance_pct: float = 0.055,  # INCREASED: 3.8% -> 5.5% (wider breathing)
        max_position_risk_pct: float = 1.0,  # Max 1% risk per trade
        max_daily_loss_pct: float = 3.0,  # Daily loss circuit breaker
        max_concurrent_positions: int = 3,  # Max simultaneous positions
    ):
        self.atr_multiplier_sl = atr_multiplier_sl
        self.risk_reward_target = risk_reward_target
        self.min_sl_distance_pct = min_sl_distance_pct
        self.max_position_risk_pct = max_position_risk_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_concurrent_positions = max_concurrent_positions

        # Position tracker for risk management
        self.position_tracker = PositionTracker()

        # Time-based filters
        self.trading_hours = {"start": 8, "end": 22}  # UTC hours

        # Confidence thresholds
        self.min_confidence_score = 0.75

    def _calculate_protective_stops(
        self, entry: float, atr: float, atr_multiplier: float | None = None
    ) -> tuple[float, float, float]:
        """Enhanced SL/TP calculation dengan adaptive multiplier."""
        mult = atr_multiplier or self.atr_multiplier_sl
        raw_sl_dist = max(atr * mult, entry * self.min_sl_distance_pct)
        sl = round(entry - raw_sl_dist, 4)
        tp = round(entry + (raw_sl_dist * self.risk_reward_target), 4)
        rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)
        return sl, tp, rr

    def _check_primary_trend(self, regime: MarketRegime) -> bool:
        """
        PRIMARY TREND FILTER: Prevents LONG entries in strong downtrends.
        """
        # Strong downtrend filter
        if regime.adx > 35.0 and regime.trend_direction == "BEARISH":
            logger.warning(
                "️ Primary trend filter: Strong downtrend (ADX=%.1f, BEARISH). Skipping LONG.",
                regime.adx,
            )
            return False

        # Extreme oversold without confirmation = falling knife
        if regime.rsi_14 < 25.0:
            logger.warning(
                "️ Extreme oversold (RSI=%.1f) without reversal confirmation. Waiting...",
                regime.rsi_14,
            )
            return False

        return True

    def _check_time_filter(self) -> bool:
        """Time-based filter to avoid high volatility periods."""
        current_hour = datetime.now(timezone.utc).hour
        if not (
            self.trading_hours["start"] <= current_hour <= self.trading_hours["end"]
        ):
            logger.info(
                f"⏰ Outside trading hours ({current_hour} UTC). Skipping signal."
            )
            return False
        return True

    def _check_correlation(self, symbol: str) -> bool:
        """Prevents overexposure to correlated assets."""
        if self.position_tracker.is_correlated(symbol):
            logger.warning(
                f"⚠️ Correlation filter: Too many positions in {symbol} group."
            )
            return False
        return True

    def evaluate_capitulation_dip(self, regime: MarketRegime) -> TradeSignal | None:
        """
        ENHANCED: Capitulation Dip Hunter dengan konfirmasi dan wider stops.
        """
        # Safety checks
        if not self.position_tracker.should_trade():
            return None

        if not self._check_time_filter():
            return None

        if not self._check_primary_trend(regime):
            return None

        # RSI range: 25-32 (not too extreme)
        if not (25.0 <= regime.rsi_14 <= 32.0):
            return None

        # Price zone: Lower Bollinger Band
        band_width = max(1e-4, regime.upper_bollinger - regime.lower_bollinger)
        deep_discount_zone = regime.lower_bollinger + (band_width * 0.45)

        if regime.current_price <= deep_discount_zone:
            entry = regime.current_price

            # Wider stops for capitulation (4x ATR)
            sl, tp_candidate, rr = self._calculate_protective_stops(
                entry, regime.atr, atr_multiplier=4.0
            )

            # TP target: Mid BB or 1:2.5 R:R
            mid_band = (regime.upper_bollinger + regime.lower_bollinger) / 2.0
            tp = round(max(tp_candidate, mid_band * 1.02), 4)
            rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)

            # Confidence scoring
            confidence = round(min(0.92, 0.75 + ((32.0 - regime.rsi_14) / 50.0)), 2)

            if confidence < self.min_confidence_score:
                logger.debug(
                    f"️ Confidence too low: {confidence} < {self.min_confidence_score}"
                )
                return None

            return TradeSignal(
                strategy_name="SPOT_CAPITULATION_DIP_V2",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=confidence,
                rationale=(
                    f" Capitulation Dip at ${entry:.2f} | "
                    f"RSI={regime.rsi_14:.1f} | ADX={regime.adx:.1f} | "
                    f"Wider SL (4x ATR) | Confidence: {confidence}"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
                atr_multiplier_used=4.0,
                max_risk_pct=self.max_position_risk_pct,
            )

        return None

    def evaluate_breakout(self, regime: MarketRegime) -> TradeSignal | None:
        """
        ENHANCED: Breakout dengan trend confirmation dan ADX filter.
        """
        # Safety checks
        if not self.position_tracker.should_trade():
            return None

        if not self._check_time_filter():
            return None

        if not self._check_correlation(regime.symbol):
            return None

        # TREND FILTER: Must be bullish
        if regime.trend_direction != "BULLISH":
            return None

        # ADX range: 24-45 (strong but not extreme)
        if not (24.0 <= regime.adx <= 45.0):
            return None

        # Breakout confirmation
        if (
            regime.current_price >= regime.donchian_high_20
            and regime.rsi_14 < 72.0  # Conservative: avoid buying at mania
        ):
            entry = regime.current_price
            sl, tp, rr = self._calculate_protective_stops(entry, regime.atr)

            # Confidence scoring
            confidence = round(min(0.94, 0.78 + (regime.adx / 120.0)), 2)

            if confidence < self.min_confidence_score:
                return None

            return TradeSignal(
                strategy_name="SPOT_BREAKOUT_MOMENTUM_V2",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=confidence,
                rationale=(
                    f" Bullish Breakout at ${regime.donchian_high_20:.2f} | "
                    f"ADX={regime.adx:.1f} | RSI={regime.rsi_14:.1f} | "
                    f"Trend: BULLISH | Confidence: {confidence}"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
                atr_multiplier_used=self.atr_multiplier_sl,
                max_risk_pct=self.max_position_risk_pct,
            )

        return None

    def evaluate_mean_reversion(self, regime: MarketRegime) -> TradeSignal | None:
        """
        ENHANCED: Mean reversion hanya di sideways market dengan ADX rendah.
        """
        # Safety checks
        if not self.position_tracker.should_trade():
            return None

        if not self._check_time_filter():
            return None

        if not self._check_correlation(regime.symbol):
            return None

        # Must be sideways/transition
        if regime.adx >= 25.0:
            return None

        # No mean revert in strong bearish trend
        if regime.trend_direction == "BEARISH" and regime.adx > 20.0:
            return None

        # Lower zone definition
        band_width = max(1e-4, regime.upper_bollinger - regime.lower_bollinger)
        lower_zone = regime.lower_bollinger + (band_width * 0.35)

        # Entry condition: RSI 35-44
        if regime.current_price <= lower_zone and 35.0 <= regime.rsi_14 <= 44.0:
            entry = regime.current_price
            sl, tp_candidate, rr = self._calculate_protective_stops(entry, regime.atr)

            mid_band = (regime.upper_bollinger + regime.lower_bollinger) / 2.0
            tp = round(max(tp_candidate, mid_band * 1.015), 4)
            rr = round(abs(tp - entry) / max(1e-6, abs(entry - sl)), 2)

            # Confidence scoring
            confidence = round(min(0.88, 0.75 + ((44.0 - regime.rsi_14) / 60.0)), 2)

            if confidence < self.min_confidence_score:
                return None

            return TradeSignal(
                strategy_name="SPOT_MEAN_REVERSION_DIP_V2",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=sl,
                take_profit=tp,
                risk_reward_ratio=rr,
                confidence_score=confidence,
                rationale=(
                    f" Mean Reversion Dip at ${entry:.2f} | "
                    f"RSI={regime.rsi_14:.1f} | ADX={regime.adx:.1f} | "
                    f"Sideways Market | Confidence: {confidence}"
                ),
                timestamp=datetime.now(timezone.utc).isoformat(),
                atr_multiplier_used=self.atr_multiplier_sl,
                max_risk_pct=self.max_position_risk_pct,
            )

        return None

    def generate_signal(
        self, regime: MarketRegime, spread_pct: float = 0.0002
    ) -> TradeSignal | None:
        """
        Enhanced Priority System dengan semua safety filters.
        """
        # Global safety check
        if not self.position_tracker.should_trade():
            logger.info("️ Trading paused due to risk limits.")
            return None

        # Priority 1: Capitulation Dip (dengan konfirmasi)
        cap_signal = self.evaluate_capitulation_dip(regime)
        if cap_signal:
            logger.info("✅ CAPITULATION SIGNAL: %s", cap_signal.rationale)
            self.position_tracker.add_trade(regime.symbol, 0.0)
            return cap_signal

        # Priority 2: Breakout (hanya jika bullish trend)
        if regime.adx >= 24.0:
            breakout_signal = self.evaluate_breakout(regime)
            if breakout_signal:
                logger.info("✅ BREAKOUT SIGNAL: %s", breakout_signal.rationale)
                self.position_tracker.add_trade(regime.symbol, 0.0)
                return breakout_signal

        # Priority 3: Mean Reversion (hanya sideways)
        mr_signal = self.evaluate_mean_reversion(regime)
        if mr_signal:
            logger.info("✅ MEAN REVERSION SIGNAL: %s", mr_signal.rationale)
            self.position_tracker.add_trade(regime.symbol, 0.0)
            return mr_signal

        # No signal
        logger.debug(
            "⏸️ No signal for %s | ADX=%.1f | RSI=%.1f | Trend=%s",
            regime.symbol,
            regime.adx,
            regime.rsi_14,
            regime.trend_direction,
        )
        return None

    def update_daily_pnl(self, pnl: float):
        """Update daily PnL tracker."""
        self.position_tracker.daily_pnl += pnl
        logger.info(f"📊 Daily PnL updated: {self.position_tracker.daily_pnl:.2f}%")


strategy_engine = MultiStrategyEngine()
