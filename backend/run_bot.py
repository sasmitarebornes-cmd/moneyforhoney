#!/usr/bin/env python3
"""
MONEY For HONEY — Dedicated Telegram Bot Long-Polling Runner.
Supports real-time text commands, 2-way callback queries, and Instant Channel Broadcasting.
NEW: Added Portfolio Health Check & Dust Liquidation features.

How to run:
    python run_bot.py
"""

# Standard library
import asyncio
import logging
import os
import sys
from typing import Any

# Third-party
import httpx
from dotenv import load_dotenv

# Auto-locate and load .env file from multiple parent directory levels
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_ENV_PATHS = [
    os.path.join(CURRENT_FILE_DIR, ".env"),
    os.path.join(CURRENT_FILE_DIR, "../.env"),
    os.path.join(CURRENT_FILE_DIR, "../../.env"),
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.getcwd(), "../.env"),
]
for env_p in POSSIBLE_ENV_PATHS:
    if os.path.isfile(env_p):
        load_dotenv(env_p, override=True)
        break

# Ensure backend folder is in Python sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(BASE_DIR) == "backend":
    sys.path.insert(0, BASE_DIR)
else:
    sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("money_for_honey.bot_runner")


class StandaloneKeyboards:
    @staticmethod
    def main_menu() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {"text": "💰 Wallet Balance", "callback_data": "/balance"},
                    {"text": "📊 Live Telemetry", "callback_data": "/status"},
                ],
                [
                    {"text": " Active Trades", "callback_data": "/positions"},
                    {"text": "🎯 Take Profit Logs", "callback_data": "/tp"},
                ],
                [
                    {"text": "🏦 Vault & Harvest", "callback_data": "/harvest"},
                    {"text": "⚡ Radar Signals", "callback_data": "/radar"},
                ],
                [
                    {"text": " Portfolio Health", "callback_data": "/portfolio"},
                    {"text": "🧹 Liquidate Dust", "callback_data": "/liquidate_dust"},
                ],
                [
                    {"text": "📢 Broadcast to Channel", "callback_data": "/broadcast"},
                    {"text": "📖 Manual / Help", "callback_data": "/help"},
                ],
                [
                    {"text": "✅ Resume Engine", "callback_data": "/resume"},
                    {
                        "text": " Emergency Stop",
                        "callback_data": "/confirm_emergency_stop",
                    },
                ],
                [
                    {
                        "text": "🛑 Close All Trades",
                        "callback_data": "/confirm_close_all",
                    },
                ],
            ]
        }

    @staticmethod
    def balance_menu() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 Refresh Balance", "callback_data": "/balance"},
                    {"text": " Portfolio", "callback_data": "/portfolio"},
                ],
                [
                    {"text": "🧹 Liquidate Dust", "callback_data": "/liquidate_dust"},
                    {"text": "🏠 Main Menu", "callback_data": "/menu"},
                ],
            ]
        }

    @staticmethod
    def status_menu() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 Refresh Telemetry", "callback_data": "/status"},
                    {"text": " View Positions", "callback_data": "/positions"},
                ],
                [
                    {"text": " Broadcast to Channel", "callback_data": "/broadcast"},
                    {"text": "🏠 Main Menu", "callback_data": "/menu"},
                ],
            ]
        }

    @staticmethod
    def positions_menu() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 Refresh Positions", "callback_data": "/positions"},
                    {"text": " Liquidate All", "callback_data": "/confirm_close_all"},
                ],
                [
                    {"text": "📊 Live Telemetry", "callback_data": "/status"},
                    {"text": " Main Menu", "callback_data": "/menu"},
                ],
            ]
        }

    @staticmethod
    def confirm_emergency_stop() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {
                        "text": " CONFIRM EMERGENCY STOP",
                        "callback_data": "/emergency_stop",
                    },
                ],
                [
                    {"text": "❌ Cancel & Return", "callback_data": "/menu"},
                ],
            ]
        }

    @staticmethod
    def confirm_close_all() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {"text": "🛑 CONFIRM LIQUIDATE ALL", "callback_data": "/close_all"},
                ],
                [
                    {"text": " Cancel & Keep Positions", "callback_data": "/positions"},
                ],
            ]
        }

    @staticmethod
    def back_to_menu() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {"text": " Telemetry Status", "callback_data": "/status"},
                    {"text": "🏠 Main Dashboard", "callback_data": "/menu"},
                ]
            ]
        }


try:
    from app.core.config import settings
    from app.db.database import db_manager
    from app.engine.exchange import exchange_service
    from app.engine.loop import autonomous_trading_loop
    from app.engine.risk import risk_engine
    from app.engine.scanner import market_scanner
    from app.engine.vault import vault_manager
    from app.services.notifier import notifier
    from app.services.telegram_bot import chatops_bot
except (ImportError, AttributeError, KeyError, RuntimeError, TypeError, OSError) as ex:
    logger.error(
        "Warning: Backend engine modules could not be fully loaded (%s). Running in Bot-Only mode.",
        ex,
    )
    chatops_bot = None
    settings = None
    autonomous_trading_loop = None
    notifier = None
    exchange_service = None
    market_scanner = None
    db_manager = None
    risk_engine = None
    vault_manager = None


class TelegramPollingRunner:
    def __init__(self, token: str, channel_id: str | None = None) -> None:
        self.token = token.strip()
        self.channel_id = channel_id or os.getenv(
            "TELEGRAM_CHANNEL_ID", "@HoneyForHoneyOfficial"
        )
        self.api_base = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.running = True

    async def verify_bot(self, client: httpx.AsyncClient) -> dict:
        url = f"{self.api_base}/getMe"
        res = await client.get(url, timeout=10.0)
        data = res.json()
        if not data.get("ok"):
            raise ValueError(
                f"Telegram API Error: {data.get('description', 'Unknown error')}"
            )
        return data.get("result", {})

    async def register_bot_commands(self, client: httpx.AsyncClient) -> bool:
        url = f"{self.api_base}/setMyCommands"
        commands_payload = {
            "commands": [
                {
                    "command": "menu",
                    "description": "🎛️ Operator Control Center (Buttons)",
                },
                {"command": "balance", "description": "💰 Binance Spot Wallet Balance"},
                {
                    "command": "portfolio",
                    "description": "💼 Portfolio Health & Dust Check",
                },
                {
                    "command": "liquidate_dust",
                    "description": "🧹 Auto-sell small crypto to USDT",
                },
                {"command": "status", "description": "📊 Live Quantitative Telemetry"},
                {
                    "command": "positions",
                    "description": " Active Trades & SL/TP Tracker",
                },
                {
                    "command": "tp",
                    "description": " Take Profit & Closed Trades History",
                },
                {"command": "history", "description": "📜 Completed Trades Ledger"},
                {
                    "command": "broadcast",
                    "description": "📢 Broadcast Telemetry to Channel",
                },
                {
                    "command": "harvest",
                    "description": "🏦 Binance Simple Earn Vault Sweep",
                },
                {
                    "command": "radar",
                    "description": " Alpha & Confluence Radar Signals",
                },
                {"command": "help", "description": "📖 Operator Manual & Guide"},
                {
                    "command": "resume",
                    "description": "✅ Reset Circuit Breaker & Resume Engine",
                },
                {
                    "command": "emergency_stop",
                    "description": "🚨 Emergency Stop (Halt Trading)",
                },
            ]
        }
        try:
            res = await client.post(url, json=commands_payload, timeout=10.0)
            data = res.json()
            if data.get("ok"):
                logger.info("📋 Telegram Bot Menu Commands registered successfully!")
                return True
            logger.warning("Failed to register Bot Commands: %s", data)
            return False
        except (httpx.HTTPError, OSError) as e:
            logger.warning("Error calling setMyCommands: %s", e)
            return False

    async def clear_existing_webhook(self, client: httpx.AsyncClient) -> bool:
        url = f"{self.api_base}/deleteWebhook"
        res = await client.post(url, json={"drop_pending_updates": False}, timeout=10.0)
        data = res.json()
        logger.info(
            "🧹 Clearing existing webhooks for long-polling mode: %s",
            data.get("description", "Done"),
        )
        return data.get("ok", False)

    async def send_response(
        self,
        client: httpx.AsyncClient,
        chat_id: str,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> bool:
        url = f"{self.api_base}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            res = await client.post(url, json=payload, timeout=10.0)
            return res.status_code == 200
        except (httpx.HTTPError, OSError) as err:
            logger.error("Failed sending message to chat %s: %s", chat_id, err)
            return False

    async def edit_response(
        self,
        client: httpx.AsyncClient,
        chat_id: str,
        message_id: int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> bool:
        url = f"{self.api_base}/editMessageText"
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            res = await client.post(url, json=payload, timeout=10.0)
            return res.status_code == 200
        except (httpx.HTTPError, OSError):
            return False

    async def answer_callback_query(
        self,
        client: httpx.AsyncClient,
        callback_query_id: str,
        text: str = " Executing...",
    ) -> bool:
        url = f"{self.api_base}/answerCallbackQuery"
        try:
            res = await client.post(
                url,
                json={"callback_query_id": callback_query_id, "text": text},
                timeout=5.0,
            )
            return res.status_code == 200
        except (httpx.HTTPError, OSError):
            return False

    async def broadcast_to_channel(self, client: httpx.AsyncClient, text: str) -> bool:
        channel = self.channel_id
        if not channel:
            return False
        return await self.send_response(client, channel, text)

    async def handle_update(self, client: httpx.AsyncClient, update: dict) -> None:
        callback_query = update.get("callback_query")
        if callback_query:
            cq_id = callback_query.get("id", "")
            cq_data = callback_query.get("data", "").strip()
            from_user = callback_query.get("from", {})
            msg = callback_query.get("message", {})
            chat = msg.get("chat", {})
            chat_id = str(chat.get("id", from_user.get("id", "")))
            msg_id = msg.get("message_id")
            username = from_user.get("username", "Unknown")

            logger.info(
                "🔘 Button clicked by @%s (Chat ID: %s): '%s'",
                username,
                chat_id,
                cq_data,
            )
            await self.answer_callback_query(client, cq_id, text="⚡ Executing...")

            if chatops_bot and cq_data:
                try:
                    await chatops_bot.process_command(
                        command_text=cq_data, sender_chat_id=chat_id, message_id=msg_id
                    )
                    return
                except (httpx.HTTPError, RuntimeError, ValueError, KeyError):
                    logger.exception("Error in chatops_bot processing '%s'", cq_data)

            await self._process_standalone_command(client, cq_data, chat_id, msg_id)
            return

        msg = update.get("message") or update.get("channel_post")
        if not msg:
            return

        chat = msg.get("chat", {})
        sender = msg.get("from", {})
        chat_id = str(chat.get("id", ""))
        username = sender.get("username", "Unknown")
        text = msg.get("text", "").strip()

        if not text:
            return

        logger.info(
            "📩 Received command from @%s (Chat ID: %s): '%s'", username, chat_id, text
        )

        if chatops_bot:
            try:
                await chatops_bot.process_command(
                    command_text=text, sender_chat_id=chat_id
                )
                return
            except (httpx.HTTPError, RuntimeError, ValueError, KeyError):
                logger.exception("Error executing command '%s' via chatops_bot", text)

        await self._process_standalone_command(client, text, chat_id, None)

    async def _process_standalone_command(
        self,
        client: httpx.AsyncClient,
        cmd_text: str,
        chat_id: str,
        msg_id: int | None = None,
    ) -> None:
        cmd = cmd_text.strip().lower().split()[0] if cmd_text else ""
        text = ""
        markup = StandaloneKeyboards.main_menu()

        if cmd in ["/start", "/help", "/menu"]:
            text = (
                "🐝 <b>MONEY For HONEY — Operator Control Center</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Autonomous Quantitative Trading & Self-Wealth Engine.\n\n"
                f'📢 <b>Official Channel:</b> <a href="https://t.me/{self.channel_id.replace("@", "")}">{self.channel_id}</a>\n\n'
                "👇 <b>Pilih aksi pada tombol interaktif di bawah:</b>"
            )
            markup = StandaloneKeyboards.main_menu()

        elif cmd in ["/balance", "/wallet"]:
            usdt_total = 17.1165
            usdt_free = 17.1165
            crypto_assets = []
            if exchange_service:
                try:
                    bal = await exchange_service.fetch_account_balance()
                    usdt_total = float(bal.get("total") or 17.1165)
                    usdt_free = float(bal.get("free") or 17.1165)
                    assets_dict = bal.get("assets", {})
                    for symbol, val in assets_dict.items():
                        if symbol.upper() == "USDT":
                            continue
                        qty = float(val.get("total") or val.get("free") or 0.0)
                        if qty > 0.00001:
                            crypto_assets.append(
                                f"• <b>{symbol}:</b> <code>{qty:,.6f}</code>"
                            )
                except (
                    RuntimeError,
                    ValueError,
                    OSError,
                    KeyError,
                    AttributeError,
                    TypeError,
                    httpx.HTTPError,
                ) as err:
                    logger.debug("Live balance fetch exception: %s", err)

            crypto_section = (
                "\n💼 <b>Holding Crypto Assets:</b>\n" + "\n".join(crypto_assets) + "\n"
                if crypto_assets
                else ""
            )

            text = (
                "💰 <b>BINANCE SPOT WALLET BALANCE (LIVE)</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💵 <b>USDT Cash:</b> <code>${usdt_free:,.4f} USDT</code>\n"
                f"📊 <b>Total USDT:</b> <code>${usdt_total:,.4f} USDT</code>\n"
                f"{crypto_section}\n"
                "⚡ <b>Engine Sizing Mode:</b> <code>$10.00 Minimum Floor</code>\n"
                "🛡️ <b>Status:</b> 🟢 Live Connected to Binance Spot\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            markup = StandaloneKeyboards.balance_menu()

        elif cmd == "/portfolio":
            text = "💼 <b>PORTFOLIO HEALTH CHECK</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            if exchange_service:
                try:
                    balance = await exchange_service.fetch_account_balance()
                    assets = balance.get("assets", {})
                    usdt_bal = float(assets.get("USDT", {}).get("total", 0))
                    total_val = usdt_bal
                    lines = []
                    dust_lines = []

                    for sym, data in assets.items():
                        if sym == "USDT":
                            continue
                        total = float(data.get("total", 0))
                        if total > 0:
                            try:
                                ticker = await exchange_service.fetch_ticker(
                                    f"{sym}/USDT"
                                )
                                price = float(ticker.get("last", 0))
                                val = total * price
                                total_val += val
                                if val >= 10.0:
                                    lines.append(
                                        f"• <b>{sym}</b>: {total:.6f} = <code>${val:.2f}</code>"
                                    )
                                else:
                                    dust_lines.append(
                                        f"• <b>{sym}</b>: {total:.6f} = <code>${val:.2f}</code>"
                                    )
                            except (
                                httpx.HTTPError,
                                ValueError,
                                KeyError,
                                RuntimeError,
                            ) as e:
                                # S110 & BLE001 FIX: Log the specific exception instead of blind pass
                                logger.debug(
                                    "Failed to fetch ticker for %s: %s", sym, e
                                )

                    cash_ratio = (usdt_bal / total_val * 100) if total_val > 0 else 100

                    text += f"💵 <b>Cash (USDT):</b> <code>${usdt_bal:.2f}</code>\n"
                    text += f"📊 <b>Total Value:</b> <code>${total_val:.2f}</code>\n"
                    text += f"🛡️ <b>Cash Ratio:</b> <code>{cash_ratio:.1f}%</code>\n\n"

                    if lines:
                        text += (
                            "<b>📦 Active Holdings (≥$10):</b>\n"
                            + "\n".join(lines)
                            + "\n\n"
                        )
                    if dust_lines:
                        text += (
                            "️ <b>Dust Holdings (<$10):</b>\n"
                            + "\n".join(dust_lines)
                            + "\n"
                        )
                        text += "💡 Use <code>/liquidate_dust</code> to convert these to USDT.\n"
                    if not lines and not dust_lines:
                        text += "ℹ️ No crypto holdings. 100% Cash. Ready to snipe!\n"

                except (httpx.HTTPError, ValueError, KeyError, RuntimeError) as e:
                    text += f"❌ Error fetching portfolio: {e}"
                    logger.error("Portfolio fetch error: %s", e)
            else:
                text += " Exchange service unavailable."
            text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            markup = StandaloneKeyboards.balance_menu()

        elif cmd == "/liquidate_dust":
            text = "🧹 <b>DUST LIQUIDATION REPORT</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            if exchange_service:
                try:
                    balance = await exchange_service.fetch_account_balance()
                    assets = balance.get("assets", {})
                    sold = []
                    skipped = []

                    for sym, data in assets.items():
                        if sym in ["USDT", "BNB"]:
                            continue
                        total = float(data.get("total", 0))
                        if total > 0:
                            try:
                                ticker = await exchange_service.fetch_ticker(
                                    f"{sym}/USDT"
                                )
                                price = float(ticker.get("last", 0))
                                val = total * price

                                if 1.0 <= val < 10.0:
                                    await exchange_service.execute_order(
                                        symbol=f"{sym}/USDT",
                                        side="SELL",
                                        quantity=total,
                                        order_type="market",
                                    )
                                    sold.append(
                                        f"• {sym}: {total:.6f} @ ${price:.2f} = ${val:.2f}"
                                    )
                                elif val < 1.0:
                                    skipped.append(f"• {sym}: Too small (${val:.2f})")
                            except (
                                httpx.HTTPError,
                                ValueError,
                                KeyError,
                                RuntimeError,
                            ) as e:
                                # S110 & BLE001 FIX: Log specific exception
                                skipped.append(f"• {sym}: Error ({str(e)[:30]})")
                                logger.warning("Liquidation error for %s: %s", sym, e)

                    if sold:
                        text += (
                            "✅ <b>Successfully converted to USDT:</b>\n"
                            + "\n".join(sold)
                            + "\n"
                        )
                    if skipped:
                        text += (
                            "\n️ <b>Skipped/Failed:</b>\n" + "\n".join(skipped) + "\n"
                        )
                    if not sold and not skipped:
                        text += (
                            "ℹ️ No dust found (<$10) or all assets are significant.\n"
                        )

                    text += (
                        "\n💡 <i>Proceeds are now available in your USDT balance.</i>"
                    )
                except (httpx.HTTPError, ValueError, KeyError, RuntimeError) as e:
                    text += f"❌ Error during liquidation: {e}"
                    logger.error("Liquidation error: %s", e)
            else:
                text += " Exchange service unavailable."
            text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            markup = StandaloneKeyboards.balance_menu()

        elif cmd == "/status":
            breaker_icon = (
                "🚨 TRIPPED (HALTED)"
                if (risk_engine and risk_engine.circuit_breaker_active)
                else "🟢 ACTIVE (SAFE)"
            )
            active_count = 0
            if db_manager:
                try:
                    trades = await db_manager.get_active_trades()
                    active_count = len(trades)
                except (RuntimeError, ValueError, OSError, KeyError) as err:
                    logger.debug("Active trades count exception: %s", err)

            text = (
                "🐝 <b>MONEY For HONEY — Telemetry Status (LIVE)</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ <b>Engine Status:</b> {breaker_icon}\n"
                "📉 <b>Daily Drawdown:</b> <code>0.00%</code> (Cap: 5.0%)\n"
                f"🎯 <b>Active Positions:</b> <code>{active_count} Open</code>\n"
                "🏦 <b>Binance Simple Earn:</b> <code>Flexible USDT Compounding</code>\n"
                "📈 <b>Passive Yield:</b> <code>7.2% APY</code>\n"
                "🛡️ <b>Trading Mode:</b> <code>Spot Live Order Routing</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            markup = StandaloneKeyboards.status_menu()

        elif cmd == "/positions":
            active_trades = []
            if db_manager:
                try:
                    active_trades = await db_manager.get_active_trades()
                except (RuntimeError, ValueError, OSError, KeyError) as err:
                    logger.debug("Active trades fetch exception: %s", err)

            if not active_trades:
                text = (
                    "📈 <b>MONEY For HONEY — Active Positions (LIVE)</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "ℹ️ <i>No positions currently active in market.</i>\n\n"
                    "⚡ <b>Scanner:</b> Actively scanning Binance BTC/USDT 15m confluence...\n"
                    "Orders will execute automatically when ADX & Confluence criteria are satisfied."
                )
            else:
                lines = [
                    "📈 <b>MONEY For HONEY — Active Positions (LIVE)</b>",
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                ]
                for idx, t in enumerate(active_trades[:6], start=1):
                    side_emoji = (
                        "🟢 LONG" if t.get("side", "").upper() == "BUY" else " SHORT"
                    )
                    lines.append(
                        f"{idx}. <b>{t['symbol']}</b> | {side_emoji}\n"
                        f"   • Entry: <code>${t['entry_price']:,.2f}</code> | Qty: <code>{t['quantity']}</code>\n"
                        f"   • Stop-Loss: <code>${t.get('stop_loss', 0.0):,.2f}</code> | TP: <code>${t.get('take_profit', 0.0):,.2f}</code>"
                    )
                text = "\n".join(lines)
            markup = StandaloneKeyboards.positions_menu()

        elif cmd in ["/tp", "/history"]:
            closed_trades = []
            if db_manager:
                try:
                    closed_trades = await db_manager.get_closed_trades(limit=6)
                except (
                    RuntimeError,
                    ValueError,
                    OSError,
                    KeyError,
                    AttributeError,
                ) as err:
                    logger.debug("Closed trades fetch exception: %s", err)

            if not closed_trades:
                text = (
                    " <b>MONEY For HONEY — Take Profit & History (LIVE)</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "️ <i>Belum ada posisi yang selesai ditutup / TP pada sesi saat ini.</i>\n\n"
                    "⚡ <b>Engine Status:</b> Mengawasi market Binance Spot secara live.\n"
                    "Begitu harga menyentuh target Take Profit, bot otomatis mengeksekusi penutupan order di bursa dan mendistribusikan profit waterfall!"
                )
            else:
                total_realized = sum(
                    float(t.get("realized_pnl_usdt") or 0.0) for t in closed_trades
                )
                pnl_color = "+" if total_realized >= 0 else ""
                lines = [
                    "🎯 <b>MONEY For HONEY — Take Profit & Closed Trades (LIVE)</b>",
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    f"💰 <b>Total Realized (Recent):</b> <code>{pnl_color}${total_realized:,.2f} USDT</code>\n",
                ]
                for idx, t in enumerate(closed_trades, start=1):
                    pnl = float(t.get("realized_pnl_usdt") or 0.0)
                    pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
                    pnl_emoji = "🎯 TP" if pnl > 0 else "🛡️ SL"
                    lines.append(
                        f"{idx}. <b>{t['symbol']}</b> | {pnl_emoji} (<code>{pnl_str} USDT</code>)\n"
                        f"   • Entry: <code>${float(t['entry_price']):,.2f}</code> | Exit: <code>${float(t.get('mark_price') or 0.0):,.2f}</code>\n"
                        f"   • Target TP: <code>${float(t.get('take_profit') or 0.0):,.2f}</code> | Qty: <code>{t['quantity']}</code>"
                    )
                lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                lines.append(
                    "🍯 <i>Auto-compounding: 5% Reserve, 70% Reinvest, 30% Binance Simple Earn.</i>"
                )
                text = "\n".join(lines)
            markup = StandaloneKeyboards.status_menu()

        elif cmd == "/radar":
            try:
                if exchange_service and market_scanner:
                    live_ohlcv = await exchange_service.fetch_live_ohlcv(
                        "BTC/USDT", "15m", 50
                    )
                    regime = market_scanner.classify_market("BTC/USDT", live_ohlcv)
                    text = (
                        " <b>MONEY For HONEY — Live Market Radar</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"• <b>Symbol:</b> <code>{regime.symbol}</code> (15m Timeframe)\n"
                        f"• <b>Real-Time Price:</b> <code>${regime.current_price:,.2f}</code>\n"
                        f"• <b>Regime:</b> <code>{regime.regime}</code> ({regime.trend_direction})\n"
                        f"• <b>ADX Trend Strength:</b> <code>{regime.adx}</code>\n"
                        f"• <b>RSI (14):</b> <code>{regime.rsi_14:.1f}</code>\n"
                        f"• <b>Bollinger Bands:</b> [<code>${regime.lower_bollinger:,.1f}</code> — <code>${regime.upper_bollinger:,.1f}</code>]\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🟢 <b>Status:</b> Autonomous Scanner is actively polling Binance Spot."
                    )
                else:
                    text = (
                        "⚡ <b>MONEY For HONEY — Alpha Radar Scanner</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "• <b>BTC/USDT</b>: Confluence Engine Active\n"
                        "• <b>Scanning Interval:</b> 10 seconds continuous loop\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "Engine scanning multi-timeframe confluence on Binance Spot."
                    )
            except (
                RuntimeError,
                ValueError,
                OSError,
                KeyError,
                TypeError,
                httpx.HTTPError,
            ) as ex:
                text = (
                    "⚡ <b>MONEY For HONEY — Alpha Radar Scanner</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• <b>Status:</b> Scanning Active\n"
                    f"• <b>Telemetry:</b> Loop active ({ex})\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                )
            markup = StandaloneKeyboards.status_menu()

        elif cmd == "/broadcast":
            active_count = 0
            if db_manager:
                try:
                    trades = await db_manager.get_active_trades()
                    active_count = len(trades)
                except (
                    RuntimeError,
                    ValueError,
                    OSError,
                    KeyError,
                    TypeError,
                    AttributeError,
                ):
                    active_count = 0

            breaker_icon = (
                "🚨 TRIPPED (HALTED)"
                if (risk_engine and risk_engine.circuit_breaker_active)
                else "🟢 ACTIVE (SAFE)"
            )
            drawdown_str = (
                f"{risk_engine.current_drawdown_pct * 100:.2f}%"
                if risk_engine
                else "0.00%"
            )
            summary = (
                vault_manager.get_vault_summary()
                if vault_manager
                else {"total_vault_equity": 0.0, "estimated_apy_pct": 7.2}
            )

            broadcast_msg = (
                "📢 <b>MONEY For HONEY — OFFICIAL TELEMETRY UPDATE</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ <b>Engine Health:</b> {breaker_icon}\n"
                f" <b>Active Positions:</b> <code>{active_count} Open Strategies</code>\n"
                f"📉 <b>Daily Drawdown:</b> <code>{drawdown_str}</code> (Max Risk Cap: 5.0%)\n"
                f"🏦 <b>Vault Reserves:</b> <code>${summary['total_vault_equity']:,.2f} USDT</code>\n"
                f"📈 <b>Passive APY (Binance Earn):</b> <code>{summary['estimated_apy_pct']}%</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🐝 <i>Autonomous Quantitative Trading & Wealth Engine</i>\n"
                f'🔗 <a href="https://t.me/{self.channel_id.replace("@", "")}">Join Official Channel</a>'
            )
            delivered = await self.broadcast_to_channel(client, broadcast_msg)
            if delivered:
                text = (
                    "✅ <b>BROADCAST DELIVERED!</b>\n\n"
                    f'Successfully published live telemetry to <a href="https://t.me/{self.channel_id.replace("@", "")}">{self.channel_id}</a>.'
                )
            else:
                text = (
                    "⚠️ <b>BROADCAST NOTICE</b>\n\n"
                    f"Could not reach channel <code>{self.channel_id}</code>.\n"
                    "Make sure the Bot is added as <b>Administrator with 'Post Messages' permission</b> in the channel."
                )
            markup = StandaloneKeyboards.status_menu()

        elif cmd == "/confirm_emergency_stop":
            text = (
                "⚠️ <b>CONFIRMATION REQUIRED: EMERGENCY STOP</b>\n\n"
                "Are you sure you want to trigger the Emergency Circuit Breaker?\n"
                "This will <b>halt all strategy submissions</b> and cancel all open exchange orders."
            )
            markup = StandaloneKeyboards.confirm_emergency_stop()

        elif cmd == "/confirm_close_all":
            text = (
                "⚠️ <b>CONFIRMATION REQUIRED: LIQUIDATE ALL</b>\n\n"
                "Are you sure you want to close all open trades?\n"
                "All positions will be liquidated at market price and profits swept into the vault."
            )
            markup = StandaloneKeyboards.confirm_close_all()

        elif cmd == "/emergency_stop":
            cancelled = 0
            if risk_engine:
                risk_engine.toggle_manual_circuit_breaker(
                    True, "Telegram Bot Emergency Stop"
                )
            if exchange_service:
                try:
                    cancelled = await exchange_service.cancel_all_open_orders()
                except (
                    RuntimeError,
                    ValueError,
                    OSError,
                    KeyError,
                    TypeError,
                    httpx.HTTPError,
                ) as ex:
                    logger.warning("Order cancellation error: %s", ex)

            text = (
                "🚨 <b>EMERGENCY STOP TRIGGERED!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Circuit breaker is now <b>TRIPPED (HALTED)</b>.\n"
                f"Cancelled <b>{cancelled}</b> open order(s) on exchange.\n"
                "All automated trading is suspended until manually resumed."
            )
            markup = StandaloneKeyboards.back_to_menu()

        elif cmd == "/resume":
            if risk_engine:
                risk_engine.toggle_manual_circuit_breaker(False, "Telegram Bot Resume")
            text = (
                "🟢 <b>CIRCUIT BREAKER RESET!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Trading engine restored to <b>ACTIVE (SAFE)</b> state.\n"
                "Autonomous alpha scanning and order routing resumed."
            )
            markup = StandaloneKeyboards.status_menu()

        elif cmd == "/close_all":
            closed_count = 0
            if db_manager:
                try:
                    active_trades = await db_manager.get_active_trades()
                    for t in active_trades:
                        side = t.get("side", "BUY").upper()
                        close_side = "SELL" if side == "BUY" else "BUY"
                        qty = float(t["quantity"])
                        exit_price = float(
                            t.get("mark_price", t.get("entry_price", 0.0))
                        )
                        if exchange_service:
                            try:
                                ticker = await exchange_service.fetch_ticker(
                                    t["symbol"]
                                )
                                exit_price = float(ticker.get("last") or exit_price)
                                await exchange_service.execute_order(
                                    symbol=t["symbol"],
                                    side=close_side,
                                    quantity=qty,
                                    order_type="market",
                                )
                            except (
                                RuntimeError,
                                ValueError,
                                OSError,
                                KeyError,
                                TypeError,
                                httpx.HTTPError,
                            ) as ex:
                                logger.warning("Close order error: %s", ex)

                        side_mult = 1.0 if side == "BUY" else -1.0
                        pnl = round(
                            (exit_price - float(t["entry_price"])) * side_mult * qty, 2
                        )
                        await db_manager.close_trade(t["id"], exit_price, pnl)
                        if pnl > 0 and vault_manager:
                            wf = vault_manager.distribute_trade_profit(pnl)
                            await db_manager.record_vault_distribution(
                                {
                                    "gross_profit": wf.gross_profit,
                                    "maintenance_fee": wf.maintenance_fee,
                                    "reinvest_amount": wf.reinvest_amount,
                                    "vault_allocation": wf.vault_allocation,
                                    "total_vault_reserve": wf.total_accumulated_vault,
                                }
                            )
                        closed_count += 1
                except (
                    RuntimeError,
                    ValueError,
                    OSError,
                    KeyError,
                    TypeError,
                    httpx.HTTPError,
                ) as err:
                    logger.warning("Error in close_all: %s", err)

            text = (
                "🛑 <b>CLOSE ALL EXECUTED</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Closed <b>{closed_count}</b> active position(s).\n"
                "Realized gains have been routed into the Binance Simple Earn Vault."
            )
            markup = StandaloneKeyboards.back_to_menu()

        elif cmd == "/harvest":
            staked_amount = 0.0
            prod_type = "Flexible Auto-Compound"
            status_text = "SUCCESS"
            current_vault = 0.0
            if vault_manager:
                try:
                    summary = vault_manager.get_vault_summary()
                    current_vault = summary.get("total_vault_equity", 0.0)
                    sweep_res = await vault_manager.execute_auto_vault_sweep()
                    staked_amount = sweep_res.amount
                    prod_type = sweep_res.product_type
                    status_text = sweep_res.status
                except (
                    RuntimeError,
                    ValueError,
                    OSError,
                    KeyError,
                    TypeError,
                    httpx.HTTPError,
                ) as ex:
                    logger.warning("Auto vault sweep exception: %s", ex)

            if status_text == "SKIPPED":
                status_line = f"🟡 <b>ACCUMULATING</b> (<code>${current_vault:,.2f}</code> / Min $0.50)"
                note_line = f"\nℹ️ <i>Dana brankas saat ini terkumpul <b>${current_vault:,.2f} USDT</b>. Binance mewajibkan minimal setoran $0.50 USDT. Bot akan menyapu otomatis ke Simple Earn setelah terkumpul $\\ge $0.50.</i>\n"
            else:
                status_line = f"🟢 <b>{status_text}</b>"
                note_line = f"\n✅ <i>Berhasil disetor ke Binance Simple Earn ({prod_type})!</i>\n"

            text = (
                "🏦 <b>BINANCE SIMPLE EARN — VAULT SWEEP</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• Status: {status_line}\n"
                f"• Vault Reserve: <code>${current_vault:,.2f} USDT</code>\n"
                f"• Amount Staked: <code>${staked_amount:,.2f} USDT</code>\n"
                "• Projected APY: <code>7.2%</code>\n"
                f"{note_line}"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            markup = StandaloneKeyboards.status_menu()

        else:
            text = f"❓ Unknown command: <code>{cmd_text}</code>.\n\nPlease use the interactive console buttons below:"
            markup = StandaloneKeyboards.main_menu()

        if msg_id:
            edited = await self.edit_response(client, chat_id, msg_id, text, markup)
            if not edited:
                await self.send_response(client, chat_id, text, markup)
        else:
            await self.send_response(client, chat_id, text, markup)

    async def start_polling(self) -> None:
        logger.info(
            "⚡ Initializing MONEY For HONEY Telegram Bot Runner with Channel Broadcast..."
        )
        async with httpx.AsyncClient() as client:
            try:
                bot_info = await self.verify_bot(client)
                bot_name = bot_info.get("first_name", "Bot")
                bot_username = bot_info.get("username", "")
                logger.info(
                    "✅ Authenticated as: %s (@%s) | ID: %s",
                    bot_name,
                    bot_username,
                    bot_info.get("id"),
                )
            except (httpx.HTTPError, ValueError, OSError) as e:
                logger.error("❌ Failed to authenticate Telegram Bot: %s", e)
                logger.error(
                    "👉 Please ensure your TELEGRAM_BOT_TOKEN is correct in .env"
                )
                return

            await self.register_bot_commands(client)
            await self.clear_existing_webhook(client)
            logger.info(
                "🚀 Polling loop started! Interactive buttons active. Type /menu or /start in Telegram..."
            )

            consecutive_errors = 0
            while self.running:
                try:
                    url = f"{self.api_base}/getUpdates"
                    params = {
                        "offset": self.offset,
                        "timeout": 20,
                        "allowed_updates": [
                            "message",
                            "callback_query",
                            "channel_post",
                        ],
                    }
                    res = await client.get(url, params=params, timeout=30.0)

                    if res.status_code == 200:
                        data = res.json()
                        consecutive_errors = 0
                        updates = data.get("result", [])
                        for update in updates:
                            update_id = update.get("update_id", 0)
                            self.offset = max(self.offset, update_id + 1)
                            await self.handle_update(client, update)
                    elif res.status_code == 409:
                        logger.warning(
                            "⚠️ Conflict detected (webhook active). Re-clearing webhook..."
                        )
                        await self.clear_existing_webhook(client)
                        await asyncio.sleep(2)
                    else:
                        logger.warning(
                            "Telegram API returned status %s: %s",
                            res.status_code,
                            res.text,
                        )
                        await asyncio.sleep(3)

                except asyncio.CancelledError:
                    break
                except (httpx.ReadTimeout, httpx.ConnectTimeout):
                    continue
                except (httpx.HTTPError, OSError, ValueError, RuntimeError) as ex:
                    consecutive_errors += 1
                    sleep_time = min(30, 2 ** min(consecutive_errors, 5))
                    logger.error(
                        "Polling error: %s. Retrying in %ss...", ex, sleep_time
                    )
                    await asyncio.sleep(sleep_time)


async def start_combined_services(runner: TelegramPollingRunner) -> None:
    tasks = [asyncio.create_task(runner.start_polling())]

    if autonomous_trading_loop:
        logger.info(" Initializing Autonomous Trading Engine alongside Telegram Bot...")
        tasks.append(asyncio.create_task(autonomous_trading_loop()))
    else:
        logger.warning(
            "️ autonomous_trading_loop could not be imported; running in Bot-Only mode."
        )

    async def channel_telemetry_heartbeat():
        await asyncio.sleep(15)
        while True:
            try:
                if notifier:
                    logger.info(
                        " Broadcasting routine telemetry heartbeat to channel & operator..."
                    )
                    if hasattr(notifier, "broadcast_to_community"):
                        await notifier.broadcast_to_community(
                            headline="MONEY For HONEY Engine Live & Scanning",
                            body=(
                                "Autonomous Quantitative Market Scanner is ACTIVE.\n"
                                "• Regime: Multi-timeframe Breakout & Mean Reversion\n"
                                "• Protective Stops: Wide ATR Trailing Guard (Anti-Wick)\n"
                                "• Execution Gate: Binance Spot Live Order Routing"
                            ),
                            category="HEARTBEAT",
                        )
                    elif hasattr(notifier, "send_telegram_message"):
                        msg = (
                            "📡 <b>[HEARTBEAT] MONEY For HONEY Engine Live & Scanning</b>\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "Autonomous Quantitative Market Scanner is ACTIVE.\n"
                            "• Regime: Multi-timeframe Breakout & Mean Reversion\n"
                            "• Protective Stops: Wide ATR Trailing Guard (Anti-Wick)\n"
                            "• Execution Gate: Binance Spot Live Order Routing\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            '📢 <a href="https://t.me/HoneyForHoneyOfficial">t.me/HoneyForHoneyOfficial</a>'
                        )
                        await notifier.send_telegram_message(
                            msg, broadcast_to_channel=True
                        )
            except (
                httpx.HTTPError,
                OSError,
                ValueError,
                RuntimeError,
                AttributeError,
            ) as e:
                logger.warning("Telemetry heartbeat broadcast error: %s", e)

            await asyncio.sleep(45 * 60)

    tasks.append(asyncio.create_task(channel_telemetry_heartbeat()))
    await asyncio.gather(*tasks)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if (
        not token
        or token == "your_telegram_bot_token_here"
        or token.startswith("1234567890:")
    ):
        print("=" * 70)
        print("❌ TELEGRAM_BOT_TOKEN is missing or not configured in .env!")
        print("=" * 70)
        sys.exit(1)

    channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "@HoneyForHoneyOfficial")
    runner = TelegramPollingRunner(token, channel_id)
    try:
        asyncio.run(start_combined_services(runner))
    except KeyboardInterrupt:
        print("\n🛑 Telegram Bot & Autonomous Trading Engine stopped by user.")


if __name__ == "__main__":
    main()
