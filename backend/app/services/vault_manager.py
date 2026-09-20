"""
Vault & Yield Compounding Manager for MONEY For HONEY.
Handles automated profit waterfall, Binance Simple Earn sweeps, and zero-idle capital allocation.
Scales smoothly from micro-gains ($0.10 - $1.00) up to large portfolio sweeps.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger("money_for_honey.vault_manager")


class VaultManager:
    """Manages Profit Waterfall distribution and Binance Simple Earn Flexible Sweeps."""

    def __init__(
        self,
        reinvest_ratio: float = 0.70,  # 70% Reinvest in Trading Engine
        vault_ratio: float = 0.30,  # 30% Sweep to Binance Simple Earn Vault
        min_sweep_usdt: float = 0.10,  # Minimum Binance Simple Earn USDT deposit threshold
    ) -> None:
        self.reinvest_ratio = reinvest_ratio
        self.vault_ratio = vault_ratio
        self.min_sweep_usdt = min_sweep_usdt
        self.total_vault_staked_usdt = 0.0
        self.total_yield_earned_usdt = 0.0

    def process_realized_profit(self, realized_pnl_usdt: float) -> dict[str, Any]:
        """
        Splits realized trade profit into Trading Capital Reinvestment and Simple Earn Vault Sweep.
        Works seamlessly for micro-profits ($0.20 - $2.00) up to large profits.
        """
        if realized_pnl_usdt <= 0:
            return {
                "status": "NO_PROFIT",
                "realized_pnl": realized_pnl_usdt,
                "reinvest_amount": 0.0,
                "vault_sweep_amount": 0.0,
            }

        reinvest_amount = realized_pnl_usdt * self.reinvest_ratio
        vault_sweep = realized_pnl_usdt * self.vault_ratio

        return {
            "status": "WATERFALL_CALCULATED",
            "realized_pnl": round(realized_pnl_usdt, 4),
            "reinvest_amount": round(reinvest_amount, 4),
            "vault_sweep_amount": round(vault_sweep, 4),
            "reinvest_ratio": self.reinvest_ratio,
            "vault_ratio": self.vault_ratio,
        }

    async def sweep_idle_cash_to_earn(
        self,
        idle_usdt_balance: float,
        api_client: Any | None = None,
        testnet: bool = True,
    ) -> dict[str, Any]:
        """
        Sweeps idle/unallocated USDT into Binance Simple Earn Flexible Product.
        Binance Simple Earn Flexible allows subscriptions as low as 0.1 USDT.
        """
        if idle_usdt_balance < self.min_sweep_usdt:
            return {
                "success": False,
                "reason": f"Idle balance (${idle_usdt_balance:.2f}) below min sweep threshold (${self.min_sweep_usdt} USDT)",
                "amount": 0.0,
            }

        logger.info(
            "🏦 Sweeping $%.2f USDT into Binance Simple Earn Flexible...",
            idle_usdt_balance,
        )

        if testnet or api_client is None:
            self.total_vault_staked_usdt += idle_usdt_balance
            return {
                "success": True,
                "mode": "TESTNET_SIMULATED",
                "product": "USDT Simple Earn Flexible",
                "amount_staked": round(idle_usdt_balance, 2),
                "estimated_apy": 7.2,
                "total_vault_staked": round(self.total_vault_staked_usdt, 2),
            }

        try:
            res = await api_client.post(
                "/sapi/v1/simple-earn/flexible/subscribe",
                params={"productId": "USDT001", "amount": idle_usdt_balance},
            )
            data = res.json()
            if data.get("success", False):
                self.total_vault_staked_usdt += idle_usdt_balance
                return {
                    "success": True,
                    "mode": "LIVE_BINANCE",
                    "product": "USDT Simple Earn Flexible",
                    "amount_staked": round(idle_usdt_balance, 2),
                    "purchase_id": data.get("purchaseId"),
                }
            return {"success": False, "error": data.get("msg", "Unknown error")}
        except (httpx.HTTPError, OSError) as e:
            logger.error("Error executing Binance Simple Earn sweep: %s", e)
            return {"success": False, "error": str(e)}


vault_manager = VaultManager()
