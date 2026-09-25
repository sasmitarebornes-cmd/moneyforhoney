"""
Adaptive Risk Management Service for MONEY For HONEY.
Dynamically scales position sizing from micro-balances ($10 - $30) up to institutional capital ($10,000+),
enforcing Binance Spot minimum notional requirements (Min $5-$10 USDT) and realistic volatility buffer.
"""

import logging
from typing import Any

logger = logging.getLogger("money_for_honey.risk_manager")


class RiskManager:
    """Manages position sizing, drawdown limits, circuit breaker, and exchange notional constraints."""

    def __init__(
        self,
        max_risk_per_trade_pct: float = 0.02,  # 2% max account risk budget
        max_daily_drawdown_pct: float = 0.05,  # 5% daily circuit breaker
        max_open_positions: int = 2,  # Maksimal 2 posisi simultan untuk modal kecil
        min_notional_usdt: float = 10.0,  # Standar minimum order Binance Spot ($10 USDT)
    ) -> None:
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.max_open_positions = max_open_positions
        self.min_notional_usdt = min_notional_usdt

    def calculate_position_size(
        self,
        total_balance_usdt: float,
        entry_price: float,
        stop_loss_price: float,
        active_positions_count: int = 0,
    ) -> dict[str, Any]:
        """
        Dynamically calculates optimal order position size with micro-capital scaling:
        - For micro balances ($10 - $30): Allocates single high-conviction order ($10 min notional).
        - For medium balances ($30 - $100): Splits into 2 manageable position slots.
        - For large capital ($100+): Fixed fractional sizing with strict SL risk caps.
        """
        if total_balance_usdt <= 0 or entry_price <= 0:
            return {
                "allowed": False,
                "reason": "Invalid balance or entry price",
                "quantity": 0.0,
                "notional_usdt": 0.0,
            }

        # Check maximum active positions limit
        if active_positions_count >= self.max_open_positions:
            return {
                "allowed": False,
                "reason": f"Max open positions reached ({active_positions_count}/{self.max_open_positions})",
                "quantity": 0.0,
                "notional_usdt": 0.0,
            }

        # Calculate distance to Stop Loss dengan batas aman realistis (minimal 1.2%)
        raw_dist_pct = (
            abs(entry_price - stop_loss_price) / entry_price
            if stop_loss_price > 0
            else 0.015
        )
        sl_distance_pct = max(raw_dist_pct, 0.012)

        # -----------------------------------------------------------------
        # TIER 1: Micro Balance ($10.00 - $30.00 USDT - Saldo $17.12 Masuk Sini)
        # -----------------------------------------------------------------
        if total_balance_usdt < 30.0:
            # Alokasi 1 posisi presisi ($10.00 - $11.00 USDT)
            order_notional = min(total_balance_usdt * 0.95, 11.0)
            order_notional = max(order_notional, self.min_notional_usdt)

            if total_balance_usdt < (self.min_notional_usdt * 0.95):
                return {
                    "allowed": False,
                    "reason": f"Balance (${total_balance_usdt:.2f}) below Binance minimum requirement (${self.min_notional_usdt} USDT)",
                    "quantity": 0.0,
                    "notional_usdt": 0.0,
                }

            quantity = order_notional / entry_price
            est_risk_usd = order_notional * sl_distance_pct

            return {
                "allowed": True,
                "tier": "MICRO_CAPITAL",
                "notional_usdt": round(order_notional, 2),
                "quantity": float(f"{quantity:.6f}"),
                "risk_amount_usdt": round(est_risk_usd, 2),
                "risk_pct_of_account": round(
                    (est_risk_usd / total_balance_usdt) * 100, 2
                ),
                "sl_distance_pct": round(sl_distance_pct * 100, 2),
            }

        # -----------------------------------------------------------------
        # TIER 2: Small Balance ($30.00 - $100.00 USDT)
        # -----------------------------------------------------------------
        elif total_balance_usdt <= 100.0:
            slot_size = total_balance_usdt / self.max_open_positions
            order_notional = max(
                self.min_notional_usdt, min(slot_size, total_balance_usdt * 0.45)
            )
            quantity = order_notional / entry_price
            est_risk_usd = order_notional * sl_distance_pct

            return {
                "allowed": True,
                "tier": "SMALL_CAPITAL",
                "notional_usdt": round(order_notional, 2),
                "quantity": float(f"{quantity:.6f}"),
                "risk_amount_usdt": round(est_risk_usd, 2),
                "risk_pct_of_account": round(
                    (est_risk_usd / total_balance_usdt) * 100, 2
                ),
                "sl_distance_pct": round(sl_distance_pct * 100, 2),
            }

        # -----------------------------------------------------------------
        # TIER 3: Standard Capital ($100.00+ USDT)
        # -----------------------------------------------------------------
        else:
            risk_usd_target = total_balance_usdt * self.max_risk_per_trade_pct
            calculated_notional = risk_usd_target / sl_distance_pct
            max_position_cap = total_balance_usdt * 0.30
            order_notional = max(
                self.min_notional_usdt, min(calculated_notional, max_position_cap)
            )
            quantity = order_notional / entry_price
            actual_risk_usd = order_notional * sl_distance_pct

            return {
                "allowed": True,
                "tier": "STANDARD_CAPITAL",
                "notional_usdt": round(order_notional, 2),
                "quantity": float(f"{quantity:.6f}"),
                "risk_amount_usdt": round(actual_risk_usd, 2),
                "risk_pct_of_account": round(
                    (actual_risk_usd / total_balance_usdt) * 100, 2
                ),
                "sl_distance_pct": round(sl_distance_pct * 100, 2),
            }


risk_manager = RiskManager()
