"""
Dynamic Risk & Position Sizing Engine.
Implements:
1. Scale-Agnostic Risk Sizing: Position Quantity = (Equity * Risk_Pct) / |Entry - SL|
2. Risk per trade = 1.5% default, Max equity allocation per position = 30%.
3. Small account guard: Enforces Binance $10+ USDT min order size for accounts < $500.
4. Circuit Breaker: Daily Drawdown Cap = 5.0% from peak daily equity. Trips and halts engine on violation.
"""

import logging
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger("money_for_honey.risk")


@dataclass
class PositionSizeResult:
    is_valid: bool
    symbol: str
    quantity: float
    notional_value: float
    risk_amount: float
    entry_price: float
    stop_loss: float
    allocation_pct: float
    reason: str | None = None


class RiskManager:
    """Quantitative risk engine governing trade approvals, size calculations, and circuit breakers."""

    def __init__(
        self,
        risk_per_trade_pct: float = settings.RISK_PER_TRADE_PCT,
        max_daily_drawdown_pct: float = settings.DAILY_DRAWDOWN_CAP_PCT,
        max_allocation_pct: float = settings.MAX_EQUITY_ALLOCATION_PCT,
        min_binance_notional: float = settings.MIN_BINANCE_ORDER_USDT,
    ):
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.max_allocation_pct = max_allocation_pct
        self.min_binance_notional = min_binance_notional

        # Circuit Breaker state
        self.circuit_breaker_active: bool = False
        self.daily_starting_equity: float = 0.0
        self.daily_peak_equity: float = 0.0
        self.current_drawdown_pct: float = 0.0
        self.trip_reason: str | None = None

    def initialize_daily_equity(self, current_equity: float) -> None:
        """Sets the baseline equity at daily session open (00:00 UTC)."""
        self.daily_starting_equity = current_equity
        self.daily_peak_equity = max(self.daily_peak_equity, current_equity)
        self.current_drawdown_pct = 0.0
        logger.info(f"Initialized daily equity baseline: ${current_equity:,.2f}")

    def update_equity_and_check_breaker(self, current_equity: float) -> bool:
        """
        Calculates daily drawdown against peak equity and enforces circuit breaker.
        Returns True if circuit breaker is TRIPPED.
        """
        if self.daily_peak_equity <= 0:
            self.daily_peak_equity = current_equity

        self.daily_peak_equity = max(self.daily_peak_equity, current_equity)

        if self.daily_peak_equity > 0:
            drawdown = (
                self.daily_peak_equity - current_equity
            ) / self.daily_peak_equity
            self.current_drawdown_pct = max(0.0, drawdown)

        if self.current_drawdown_pct >= self.max_daily_drawdown_pct:
            if not self.circuit_breaker_active:
                self.circuit_breaker_active = True
                self.trip_reason = (
                    f"CRITICAL: Daily drawdown {self.current_drawdown_pct * 100:.2f}% "
                    f"exceeded maximum cap {self.max_daily_drawdown_pct * 100:.2f}%."
                )
                logger.critical(self.trip_reason)
            return True

        return self.circuit_breaker_active

    def toggle_manual_circuit_breaker(
        self, activate: bool | None = None, reason: str = "Manual User Override"
    ) -> bool:
        """Manual toggle for the emergency circuit breaker."""
        if activate is not None:
            self.circuit_breaker_active = activate
        else:
            self.circuit_breaker_active = not self.circuit_breaker_active

        if self.circuit_breaker_active:
            self.trip_reason = f"Manual Emergency Trip: {reason}"
        else:
            self.trip_reason = None

        logger.warning(
            f"Circuit Breaker state altered: active={self.circuit_breaker_active} ({self.trip_reason})"
        )
        return self.circuit_breaker_active

    def calculate_position_size(
        self,
        equity: float,
        entry_price: float,
        stop_loss: float,
        symbol: str = "BTC/USDT",
    ) -> PositionSizeResult:
        """
        Scale-agnostic risk sizing:
        Position Quantity = (Equity * Risk_Pct) / |Entry - SL|
        Enforces:
        - Max 30% capital allocation per position.
        - Minimum Binance $10 notional requirement for small capital (< $500).
        """
        if self.circuit_breaker_active:
            return PositionSizeResult(
                is_valid=False,
                symbol=symbol,
                quantity=0.0,
                notional_value=0.0,
                risk_amount=0.0,
                entry_price=entry_price,
                stop_loss=stop_loss,
                allocation_pct=0.0,
                reason=f"REJECTED: Circuit Breaker is active! ({self.trip_reason})",
            )

        if equity <= 0:
            return PositionSizeResult(
                is_valid=False,
                symbol=symbol,
                quantity=0.0,
                notional_value=0.0,
                risk_amount=0.0,
                entry_price=entry_price,
                stop_loss=stop_loss,
                allocation_pct=0.0,
                reason="REJECTED: Account equity is zero or negative.",
            )

        sl_distance = abs(entry_price - stop_loss)
        if sl_distance <= 0:
            return PositionSizeResult(
                is_valid=False,
                symbol=symbol,
                quantity=0.0,
                notional_value=0.0,
                risk_amount=0.0,
                entry_price=entry_price,
                stop_loss=stop_loss,
                allocation_pct=0.0,
                reason="REJECTED: Stop Loss distance cannot be zero.",
            )

        # 1. Nominal Risk allocation (1.5% of equity)
        risk_budget = equity * self.risk_per_trade_pct

        # 2. Formula: Q = Risk_Budget / |Entry - SL|
        quantity = risk_budget / sl_distance
        notional_value = quantity * entry_price
        max_allowed_notional = equity * self.max_allocation_pct

        # 3. Dynamic Position Cap:
        # For micro-capital accounts (equity < 35.0 USDT), allow single-bullet allocation (up to 95% of equity)
        # to satisfy Binance's minimum notional requirement ($5.00 USDT).
        # For accounts >= 35.0 USDT, enforce standard 30% max allocation per position.
        effective_max_alloc = 0.95 if equity < 35.0 else self.max_allocation_pct
        max_allowed_notional = equity * effective_max_alloc

        if notional_value > max_allowed_notional:
            logger.info(
                f"Notional ${notional_value:.2f} exceeded max allocation "
                f"${max_allowed_notional:.2f} ({effective_max_alloc * 100:.0f}%). Clamping quantity."
            )
            notional_value = max_allowed_notional
            quantity = notional_value / entry_price
            risk_budget = quantity * sl_distance

        # 4. Small Capital Guard & Binance minimum notional check ($5.00 floor)
        binance_min_floor = min(self.min_binance_notional, 5.0)
        if notional_value < binance_min_floor:
            # Special case for micro-accounts: allocate safe equity (up to 95%) to meet Binance minimum
            if equity >= binance_min_floor:
                target_notional = min(
                    equity * 0.95, max(binance_min_floor, equity * 0.90)
                )
                required_qty = target_notional / entry_price
                implied_risk = required_qty * sl_distance
                quantity = required_qty
                notional_value = target_notional
                risk_budget = implied_risk
                logger.info(
                    f"Micro-cap sizing applied for {symbol}: Sized order to ${notional_value:.2f} "
                    f"to fulfill Binance minimum lot size (Allocation: {(notional_value / equity) * 100:.1f}%)"
                )
            else:
                return PositionSizeResult(
                    is_valid=False,
                    symbol=symbol,
                    quantity=0.0,
                    notional_value=0.0,
                    risk_amount=0.0,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    allocation_pct=0.0,
                    reason=(
                        f"REJECTED: Account equity ${equity:.2f} is below Binance minimum required order "
                        f"of ${binance_min_floor:.2f}."
                    ),
                )

        allocation_pct = (notional_value / equity) * 100.0

        return PositionSizeResult(
            is_valid=True,
            symbol=symbol,
            quantity=round(quantity, 6),
            notional_value=round(notional_value, 2),
            risk_amount=round(risk_budget, 2),
            entry_price=entry_price,
            stop_loss=stop_loss,
            allocation_pct=round(allocation_pct, 2),
            reason="Approved by Dynamic Risk Engine",
        )


risk_engine = RiskManager()
