"""
Dynamic Trailing Stop & Break-Even Auto-Adjustment Engine.
Implements:
1. Break-Even Trigger: When profit >= +1.5R, auto-shifts Stop Loss to Entry + fee buffer (0.08%).
2. Chandelier / ATR Trailing Stop: Continuously adjusts SL as price makes new highs/lows.
3. Ratchet Protection: Stop Loss NEVER retreats backwards.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("money_for_honey.trailing")


@dataclass
class TrailingUpdateResult:
    trade_id: str
    symbol: str
    side: str
    old_sl: float
    new_sl: float
    is_breakeven_activated: bool
    is_trailing_stepped: bool
    current_profit_r: float
    message: str


class TrailingStopManager:
    """Manages dynamic trailing stops, profit locks, and break-even transitions."""

    def __init__(self, breakeven_r_threshold: float = 1.5, chandelier_atr_mult: float = 2.0, fee_buffer_pct: float = 0.0008):
        self.breakeven_r_threshold = breakeven_r_threshold
        self.chandelier_atr_mult = chandelier_atr_mult
        self.fee_buffer_pct = fee_buffer_pct

    def evaluate_position_trailing(
        self,
        trade_id: str,
        symbol: str,
        side: str,  # "BUY" | "SELL"
        entry_price: float,
        initial_sl: float,
        current_sl: float,
        current_price: float,
        highest_price: float,
        lowest_price: float,
        atr: float = 0.0,
    ) -> TrailingUpdateResult:
        """
        Evaluates position state and returns updated stop loss.
        """
        risk_distance = abs(entry_price - initial_sl)
        if risk_distance <= 0:
            return TrailingUpdateResult(
                trade_id=trade_id,
                symbol=symbol,
                side=side,
                old_sl=current_sl,
                new_sl=current_sl,
                is_breakeven_activated=False,
                is_trailing_stepped=False,
                current_profit_r=0.0,
                message="Invalid initial risk distance.",
            )

        new_sl = current_sl
        is_be_activated = False
        is_trailing_stepped = False

        if side.upper() == "BUY":
            gain = current_price - entry_price
            profit_r = gain / risk_distance
            breakeven_level = entry_price * (1.0 + self.fee_buffer_pct)

            # 1. Check Break-Even trigger (+1.5R)
            if profit_r >= self.breakeven_r_threshold and current_sl < breakeven_level:
                new_sl = round(breakeven_level, 4)
                is_be_activated = True

            # 2. Chandelier ATR Trailing Stop above +2.0R
            if profit_r >= 2.0 and atr > 0:
                chandelier_sl = round(highest_price - (atr * self.chandelier_atr_mult), 4)
                if chandelier_sl > new_sl:
                    new_sl = chandelier_sl
                    is_trailing_stepped = True

            # Ratchet rule: SL can only increase for long
            new_sl = max(current_sl, new_sl)

        else:  # SELL (Short)
            gain = entry_price - current_price
            profit_r = gain / risk_distance
            breakeven_level = entry_price * (1.0 - self.fee_buffer_pct)

            # 1. Check Break-Even trigger (+1.5R)
            if profit_r >= self.breakeven_r_threshold and current_sl > breakeven_level:
                new_sl = round(breakeven_level, 4)
                is_be_activated = True

            # 2. Chandelier ATR Trailing Stop above +2.0R
            if profit_r >= 2.0 and atr > 0:
                chandelier_sl = round(lowest_price + (atr * self.chandelier_atr_mult), 4)
                if chandelier_sl < new_sl:
                    new_sl = chandelier_sl
                    is_trailing_stepped = True

            # Ratchet rule: SL can only decrease for short
            new_sl = min(current_sl, new_sl)

        msg = "Trailing maintained"
        if is_be_activated:
            msg = f"Break-Even locked at ${new_sl:,.2f} (+{profit_r:.2f}R reached)"
        elif is_trailing_stepped:
            msg = f"Chandelier ATR Trailing adjusted to ${new_sl:,.2f}"

        return TrailingUpdateResult(
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            old_sl=current_sl,
            new_sl=new_sl,
            is_breakeven_activated=is_be_activated,
            is_trailing_stepped=is_trailing_stepped,
            current_profit_r=round(profit_r, 2),
            message=msg,
        )


trailing_manager = TrailingStopManager()
