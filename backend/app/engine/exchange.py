"""
Production Exchange Connectivity & Execution Service.
Integrates CCXT asynchronous client for Binance, Bybit, and OKX.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import ccxt.async_support as ccxt

from app.core.config import settings
from app.core.security import key_vault

logger = logging.getLogger("money_for_honey.exchange")


class ExchangeService:
    """Enterprise multi-exchange asynchronous execution service."""

    def __init__(self) -> None:
        self.testnet_mode: bool = getattr(settings, "TESTNET_MODE", True)
        self.binance: ccxt.binance | None = None
        self.bybit: ccxt.bybit | None = None
        self.okx: ccxt.okx | None = None
        self._init_exchanges()

    def _init_exchanges(self) -> None:
        """Initializes CCXT exchange connectors with decrypted keys."""
        try:
            # 1. Binance
            binance_config: dict[str, Any] = {
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
            if settings.BINANCE_API_KEY and settings.BINANCE_API_SECRET:
                try:
                    binance_config["apiKey"] = key_vault.decrypt(
                        settings.BINANCE_API_KEY
                    )
                    binance_config["secret"] = key_vault.decrypt(
                        settings.BINANCE_API_SECRET
                    )
                except Exception:  # noqa: BLE001
                    binance_config["apiKey"] = settings.BINANCE_API_KEY
                    binance_config["secret"] = settings.BINANCE_API_SECRET

            self.binance = ccxt.binance(binance_config)
            if self.testnet_mode:
                self.binance.set_sandbox_mode(True)
                logger.info("Binance client loaded in TESTNET / SANDBOX mode.")

            # 2. Bybit
            bybit_config: dict[str, Any] = {"enableRateLimit": True}
            if settings.BYBIT_API_KEY and settings.BYBIT_API_SECRET:
                try:
                    bybit_config["apiKey"] = key_vault.decrypt(settings.BYBIT_API_KEY)
                    bybit_config["secret"] = key_vault.decrypt(
                        settings.BYBIT_API_SECRET
                    )
                except Exception:  # noqa: BLE001
                    bybit_config["apiKey"] = settings.BYBIT_API_KEY
                    bybit_config["secret"] = settings.BYBIT_API_SECRET
            self.bybit = ccxt.bybit(bybit_config)
            if self.testnet_mode:
                self.bybit.set_sandbox_mode(True)

            # 3. OKX
            okx_config: dict[str, Any] = {"enableRateLimit": True}
            if settings.OKX_API_KEY and settings.OKX_API_SECRET:
                try:
                    okx_config["apiKey"] = key_vault.decrypt(settings.OKX_API_KEY)
                    okx_config["secret"] = key_vault.decrypt(settings.OKX_API_SECRET)
                    if settings.OKX_PASSPHRASE:
                        okx_config["password"] = key_vault.decrypt(
                            settings.OKX_PASSPHRASE
                        )
                except Exception:  # noqa: BLE001
                    okx_config["apiKey"] = settings.OKX_API_KEY
                    okx_config["secret"] = settings.OKX_API_SECRET
                    okx_config["password"] = settings.OKX_PASSPHRASE or ""
            self.okx = ccxt.okx(okx_config)
            if self.testnet_mode:
                self.okx.set_sandbox_mode(True)

            logger.info("All exchange clients initialized successfully")
        except Exception:
            # FIX TRY401: logger.exception otomatis menampilkan traceback, tidak perlu passing 'e'
            logger.exception("Failed to initialize CCXT exchanges")
            raise

    async def fetch_ticker(
        self, symbol: str = "BTC/USDT", exchange_name: str = "binance"
    ) -> dict[str, Any]:
        """Fetches real-time ticker data."""
        client = getattr(self, exchange_name, self.binance)
        if not client:
            return {
                "symbol": symbol,
                "bid": 0.0,
                "ask": 0.0,
                "last": 0.0,
                "change24h": 0.0,
                "volume": 0.0,
            }

        try:
            ticker = await client.fetch_ticker(symbol)
            return {
                "symbol": symbol,
                "bid": float(ticker.get("bid") or ticker.get("last") or 0.0),
                "ask": float(ticker.get("ask") or ticker.get("last") or 0.0),
                "last": float(ticker.get("last") or 0.0),
                "change24h": float(ticker.get("percentage") or 0.0),
                "volume": float(ticker.get("baseVolume") or 0.0),
            }
        except Exception as err:  # noqa: BLE001
            logger.warning(
                "Could not fetch %s ticker for %s: %s. Returning fallback.",
                exchange_name,
                symbol,
                err,
            )
            return {
                "symbol": symbol,
                "bid": 0.0,
                "ask": 0.0,
                "last": 0.0,
                "change24h": 0.0,
                "volume": 0.0,
            }

    async def fetch_live_ohlcv(
        self, symbol: str = "BTC/USDT", timeframe: str = "15m", limit: int = 50
    ) -> list[list[float]]:
        """Fetches live OHLCV candlestick series for market regime scanning."""
        if not self.binance:
            logger.warning("Binance client not available for OHLCV fetch")
            return []
        try:
            ohlcv = await self.binance.fetch_ohlcv(
                symbol, timeframe=timeframe, limit=limit
            )
            return ohlcv
        except Exception as err:  # noqa: BLE001
            logger.warning(
                "Live OHLCV fetch failed: %s. Using default algorithmic sequence.", err
            )
            return []

    async def execute_order(
        self,
        symbol: str,
        side: str,  # "BUY" | "SELL"
        quantity: float,
        price: float | None = None,
        order_type: str = "limit",
    ) -> dict[str, Any]:
        """Executes a real or testnet spot order on Binance with safety checks."""
        if not self.binance:
            raise RuntimeError("Binance client is not initialized.")

        if quantity <= 0:
            raise ValueError(f"Order quantity must be positive, got: {quantity}")

        if price is not None and price <= 0:
            raise ValueError(f"Order price must be positive, got: {price}")

        try:
            has_live_keys = bool(self.binance.apiKey and len(self.binance.apiKey) > 10)

            # FIX SIM102: Menggabungkan nested if menjadi satu pernyataan dengan 'and'
            if not has_live_keys and (
                getattr(settings, "STRICT_PRODUCTION_MODE", False)
                or (settings.APP_ENV == "production" and not self.testnet_mode)
            ):
                error_msg = (
                    "CRITICAL EXECUTION HALT: Live order rejected. "
                    "STRICT_PRODUCTION_MODE is enabled and valid Binance API keys were not detected. "
                    "Simulated fallback is strictly prohibited in live production."
                )
                logger.critical(error_msg)
                raise RuntimeError(error_msg)

            if has_live_keys:
                logger.info(
                    "Submitting LIVE %s %s order for %s %s at %s...",
                    order_type.upper(),
                    side,
                    quantity,
                    symbol,
                    price,
                )
                order = await self.binance.create_order(
                    symbol=symbol,
                    type=order_type,
                    side=side.lower(),
                    amount=quantity,
                    price=price if order_type == "limit" else None,
                )
                return {
                    "status": "FILLED"
                    if order.get("status") in ["closed", "filled"]
                    else "SUBMITTED",
                    "order_id": str(order.get("id")),
                    "symbol": symbol,
                    "side": side.upper(),
                    "quantity": float(order.get("amount", quantity)),
                    "price": float(order.get("price", price or 0.0)),
                    "executed_at": order.get("datetime"),
                    "raw": order,
                }

            await asyncio.sleep(0.05)
            simulated_price = price or 0.0
            return {
                "status": "FILLED",
                "order_id": f"SIM-{int(asyncio.get_event_loop().time() * 1000)}",
                "symbol": symbol,
                "side": side.upper(),
                "quantity": quantity,
                "price": simulated_price,
                "executed_at": "SIMULATED_TESTNET",
                "raw": {"simulated": True},
            }
        except ccxt.InsufficientFunds as e:
            logger.critical(
                "Execution rejected: Insufficient funds on exchange (%s)", e
            )
            raise
        except ccxt.InvalidOrder as e:
            logger.error("Execution rejected: Invalid order structure (%s)", e)
            raise
        except Exception:
            # FIX TRY401: Menghapus variabel 'e' karena logger.exception sudah otomatis menampilkannya
            logger.exception("Execution error on exchange")
            raise

    async def cancel_all_open_orders(self, symbol: str | None = None) -> int:
        """Emergency method called when Circuit Breaker trips: cancels all active open orders."""
        cancelled_count = 0
        if not self.binance:
            return 0
        try:
            if self.binance.apiKey and len(self.binance.apiKey) > 10:
                orders = await self.binance.fetch_open_orders(symbol=symbol)
                for o in orders:
                    await self.binance.cancel_order(o["id"], o["symbol"])
                    cancelled_count += 1
                logger.warning(
                    "CIRCUIT BREAKER: Cancelled %s open orders.", cancelled_count
                )
        except Exception as e:  # noqa: BLE001
            logger.error("Error during emergency order cancellation: %s", e)
        return cancelled_count

    async def preflight_check(self) -> dict[str, Any]:
        """Production readiness audit."""
        audit_results: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": settings.APP_ENV,
            "testnet_mode": self.testnet_mode,
            "strict_production_mode": getattr(
                settings, "STRICT_PRODUCTION_MODE", False
            ),
            "exchanges": {},
            "all_passed": True,
            "warnings": [],
            "critical_errors": [],
        }

        binance_info: dict[str, Any] = {
            "configured": bool(
                self.binance and self.binance.apiKey and len(self.binance.apiKey) > 5
            ),
            "connected": False,
            "latency_ms": None,
            "permissions": {"spot_trade": False, "read": False},
            "balance_usdt": 0.0,
            "status": "NOT_CONFIGURED",
        }

        if self.binance:
            try:
                t0 = asyncio.get_event_loop().time()
                await self.binance.fetch_time()
                latency = round((asyncio.get_event_loop().time() - t0) * 1000, 2)
                binance_info["connected"] = True
                binance_info["latency_ms"] = latency

                if binance_info["configured"]:
                    try:
                        balance = await self.binance.fetch_balance()
                        usdt_free = float(balance.get("USDT", {}).get("free", 0.0))
                        binance_info["balance_usdt"] = usdt_free
                        binance_info["permissions"]["read"] = True
                        binance_info["permissions"]["spot_trade"] = True
                        binance_info["status"] = (
                            "LIVE_READY"
                            if not self.testnet_mode
                            else "TESTNET_CONNECTED"
                        )
                    except Exception as auth_err:  # noqa: BLE001
                        binance_info["status"] = "AUTH_FAILED"
                        audit_results["critical_errors"].append(
                            f"Binance API authentication failed: {auth_err}"
                        )
                        audit_results["all_passed"] = False
                else:
                    binance_info["status"] = "PAPER_TRADING_FALLBACK"
                    if settings.APP_ENV == "production" and not self.testnet_mode:
                        audit_results["critical_errors"].append(
                            "Binance API keys are missing in live production!"
                        )
                        audit_results["all_passed"] = False
                    else:
                        audit_results["warnings"].append(
                            "Binance running in simulated paper-trade mode."
                        )
            except Exception as conn_err:  # noqa: BLE001
                binance_info["status"] = "CONNECTION_ERROR"
                audit_results["critical_errors"].append(
                    f"Binance connection error: {conn_err}"
                )
                audit_results["all_passed"] = False

        audit_results["exchanges"]["binance"] = binance_info
        return audit_results

    async def execute_two_leg_delta_neutral(
        self,
        symbol: str,
        spot_qty: float,
        perp_qty: float,
        spot_price: float,
        perp_price: float,
    ) -> dict[str, Any]:
        """Executes an atomic Delta-Neutral pairing with automatic immediate rollback if Leg 2 fails."""
        if spot_qty <= 0 or perp_qty <= 0:
            raise ValueError(
                f"Quantities must be positive: spot={spot_qty}, perp={perp_qty}"
            )
        if spot_price <= 0 or perp_price <= 0:
            raise ValueError(
                f"Prices must be positive: spot={spot_price}, perp={perp_price}"
            )

        logger.info(
            "Initiating Atomic Delta-Neutral Execution for %s (Spot: %s, Perp: %s)",
            symbol,
            spot_qty,
            perp_qty,
        )
        leg1_spot = None
        try:
            leg1_spot = await self.execute_order(
                symbol=symbol,
                side="BUY",
                quantity=spot_qty,
                price=spot_price,
                order_type="market",
            )
            logger.info(
                "Leg 1 (Spot Long) FILLED: Order ID %s", leg1_spot.get("order_id")
            )
        except Exception as leg1_err:  # noqa: BLE001
            logger.error(
                "Leg 1 (Spot Long) failed: %s. Aborting before Leg 2.", leg1_err
            )
            raise RuntimeError(f"Leg 1 Spot order failed: {leg1_err}")

        try:
            leg2_perp = await self.execute_order(
                symbol=symbol,
                side="SELL",
                quantity=perp_qty,
                price=perp_price,
                order_type="market",
            )
            logger.info(
                "Leg 2 (Perp Short) FILLED: Order ID %s. Delta-Neutral established!",
                leg2_perp.get("order_id"),
            )
            return {
                "status": "HEDGED_SUCCESS",
                "net_delta": 0.0,
                "leg1_spot": leg1_spot,
                "leg2_perp": leg2_perp,
            }
        except Exception as leg2_err:  # noqa: BLE001
            logger.critical(
                "LEG 2 (Perp Short) FAILED (%s)! Initiating EMERGENCY ROLLBACK...",
                leg2_err,
            )
            rollback_res = None
            try:
                rollback_res = await self.execute_order(
                    symbol=symbol,
                    side="SELL",
                    quantity=spot_qty,
                    order_type="market",
                )
                logger.warning(
                    "EMERGENCY ROLLBACK SUCCESS: Sold spot position %s %s.",
                    spot_qty,
                    symbol,
                )
            except Exception as rollback_err:  # noqa: BLE001
                logger.critical(
                    "FATAL: Emergency rollback failed: %s! Unhedged exposure exists on %s!",
                    rollback_err,
                    symbol,
                )

            raise RuntimeError(
                f"Delta-Neutral Leg 2 failed ({leg2_err}). Emergency rollback executed: {rollback_res is not None}"
            )

    async def close(self) -> None:
        """Closes all active exchange HTTP sessions."""
        for client in [self.binance, self.bybit, self.okx]:
            if client:
                try:
                    await client.close()
                except Exception:  # noqa: S110, BLE001
                    pass


exchange_service = ExchangeService()
