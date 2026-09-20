"""
Multi-Strategy Engine.
Implements:
1. Breakout Strategy (ADX > 25): Captures high-momentum directional expansion.
2. Mean-Reversion Strategy (ADX < 20): Capitalizes on statistical extremes (BB 2.0 std & RSI < 30 / > 70).
3. Micro-Scalping Strategy: Rapid intra-spread liquidity capture on tight orderbooks.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
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
    """Evaluates market regimes and fires precision quantitative trading signals."""

    def __init__(self, atr_multiplier_sl: float = 1.8, risk_reward_target: float = 2.5):
        self.atr_multiplier_sl = atr_multiplier_sl
        self.risk_reward_target = risk_reward_target

    def evaluate_breakout(self, regime: MarketRegime) -> Optional[TradeSignal]:
        """
        Executes Breakout strategy when ADX > 25.
        Long on break above 20-period Donchian High.
        Short on breakdown below 20-period Donchian Low.
        """
        if regime.adx <= 25.0:
            return None

        # Long Breakout
        if regime.current_price > regime.donchian_high_20 and regime.trend_direction == "BULLISH":
            entry = regime.current_price
            sl = entry - (regime.atr * self.atr_multiplier_sl)
            risk_dist = entry - sl
            tp = entry + (risk_dist * self.risk_reward_target)

            return TradeSignal(
                strategy_name="DYNAMIC_BREAKOUT_MOMENTUM",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=round(sl, 4),
                take_profit=round(tp, 4),
                risk_reward_ratio=self.risk_reward_target,
                confidence_score=round(min(0.95, 0.65 + (regime.adx / 100.0)), 2),
                rationale=f"Donchian 20 High break at ${regime.donchian_high_20:.2f} with ADX={regime.adx:.1f}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Short Breakout
        if regime.current_price < regime.donchian_low_20 and regime.trend_direction == "BEARISH":
            entry = regime.current_price
            sl = entry + (regime.atr * self.atr_multiplier_sl)
            risk_dist = sl - entry
            tp = entry - (risk_dist * self.risk_reward_target)

            return TradeSignal(
                strategy_name="DYNAMIC_BREAKOUT_MOMENTUM",
                symbol=regime.symbol,
                action="SELL",
                entry_price=round(entry, 4),
                stop_loss=round(sl, 4),
                take_profit=round(tp, 4),
                risk_reward_ratio=self.risk_reward_target,
                confidence_score=round(min(0.95, 0.65 + (regime.adx / 100.0)), 2),
                rationale=f"Donchian 20 Low break at ${regime.donchian_low_20:.2f} with ADX={regime.adx:.1f}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return None

    def evaluate_mean_reversion(self, regime: MarketRegime) -> Optional[TradeSignal]:
        """
        Executes Mean-Reversion strategy when ADX < 20.
        Long on Lower Bollinger Band touch + RSI oversold (< 32).
        Short on Upper Bollinger Band touch + RSI overbought (> 68).
        """
        if regime.adx >= 20.0:
            return None

        # Long Reversion (Oversold bounce to mean)
        if regime.current_price <= regime.lower_bollinger and regime.rsi_14 <= 32.0:
            entry = regime.current_price
            sl = entry - (regime.atr * 1.2)
            risk_dist = entry - sl
            # Target middle Bollinger band / mean
            mid_band = (regime.upper_bollinger + regime.lower_bollinger) / 2.0
            tp = max(entry + (risk_dist * 1.5), mid_band)
            rr = (tp - entry) / max(1e-6, risk_dist)

            return TradeSignal(
                strategy_name="STATISTICAL_MEAN_REVERSION",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=round(sl, 4),
                take_profit=round(tp, 4),
                risk_reward_ratio=round(rr, 2),
                confidence_score=round(0.70 + (32.0 - regime.rsi_14) / 100.0, 2),
                rationale=f"Lower BB touch at ${regime.lower_bollinger:.2f} with RSI={regime.rsi_14:.1f} (ADX={regime.adx:.1f})",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Short Reversion (Overbought rejection)
        if regime.current_price >= regime.upper_bollinger and regime.rsi_14 >= 68.0:
            entry = regime.current_price
            sl = entry + (regime.atr * 1.2)
            risk_dist = sl - entry
            mid_band = (regime.upper_bollinger + regime.lower_bollinger) / 2.0
            tp = min(entry - (risk_dist * 1.5), mid_band)
            rr = (entry - tp) / max(1e-6, risk_dist)

            return TradeSignal(
                strategy_name="STATISTICAL_MEAN_REVERSION",
                symbol=regime.symbol,
                action="SELL",
                entry_price=round(entry, 4),
                stop_loss=round(sl, 4),
                take_profit=round(tp, 4),
                risk_reward_ratio=round(rr, 2),
                confidence_score=round(0.70 + (regime.rsi_14 - 68.0) / 100.0, 2),
                rationale=f"Upper BB touch at ${regime.upper_bollinger:.2f} with RSI={regime.rsi_14:.1f} (ADX={regime.adx:.1f})",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        return None

    def evaluate_micro_scalping(self, regime: MarketRegime, bid_ask_spread_pct: float) -> Optional[TradeSignal]:
        """Micro-scalping during low volatility / ultra-tight spread conditions."""
        if bid_ask_spread_pct < 0.0003 and regime.atr_pct > 0.8:
            # High intraday oscillation with minimal maker/taker friction
            entry = regime.current_price
            sl = entry - (regime.atr * 0.6)
            tp = entry + (regime.atr * 1.0)
            return TradeSignal(
                strategy_name="MICRO_SCALP_LIQUIDITY_PUMP",
                symbol=regime.symbol,
                action="BUY",
                entry_price=round(entry, 4),
                stop_loss=round(sl, 4),
                take_profit=round(tp, 4),
                risk_reward_ratio=1.66,
                confidence_score=0.68,
                rationale="Ultra-tight spread orderbook imbalance scalp",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        return None

    def generate_signal(self, regime: MarketRegime, spread_pct: float = 0.0002) -> Optional[TradeSignal]:
        """Evaluates all strategy modules in sequence based on regime classifier."""
        if regime.regime == "BREAKOUT":
            return self.evaluate_breakout(regime)
        elif regime.regime == "MEAN_REVERSION":
            return self.evaluate_mean_reversion(regime)
        else:
            return self.evaluate_micro_scalping(regime, spread_pct)


strategy_engine = MultiStrategyEngine()
