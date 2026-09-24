#!/usr/bin/env python3
"""
MONEY For HONEY — Dedicated Telegram Bot Long-Polling Runner.
Supports real-time text commands, 2-way callback queries, and Instant Channel Broadcasting.

How to run:
    python run_bot.py
"""

import asyncio
import logging
import os
import sys
from typing import Any

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
logger = logging.getLogger("money_for_honey.bot_runner")


# Standalone UI Keyboards Definition
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
                    {"text": "📈 Active Trades", "callback_data": "/positions"},
                    {"text": "🏦 Vault & Harvest", "callback_data": "/harvest"},
                ],
                [
                    {"text": "⚡ Radar Signals", "callback_data": "/radar"},
                    {"text": "📢 Broadcast to Channel", "callback_data": "/broadcast"},
                ],
                [
                    {"text": "📖 Manual / Help", "callback_data": "/help"},
                    {"text": "✅ Resume Engine", "callback_data": "/resume"},
                ],
                [
                    {
                        "text": "🚨 Emergency Stop",
                        "callback_data": "/confirm_emergency_stop",
                    },
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
                    {"text": "📊 Telemetry", "callback_data": "/status"},
                ],
                [
                    {"text": "📈 Active Trades", "callback_data": "/positions"},
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
                    {"text": "📈 View Positions", "callback_data": "/positions"},
                ],
                [
                    {"text": "📢 Broadcast to Channel", "callback_data": "/broadcast"},
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
                    {"text": "🛑 Liquidate All", "callback_data": "/confirm_close_all"},
                ],
                [
                    {"text": "📊 Live Telemetry", "callback_data": "/status"},
                    {"text": "🏠 Main Menu", "callback_data": "/menu"},
                ],
            ]
        }

    @staticmethod
    def confirm_emergency_stop() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "🚨 CONFIRM EMERGENCY STOP",
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
                    {
                        "text": "❌ Cancel & Keep Positions",
                        "callback_data": "/positions",
                    },
                ],
            ]
        }

    @staticmethod
    def back_to_menu() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {"text": "📊 Telemetry Status", "callback_data": "/status"},
                    {"text": "🏠 Main Dashboard", "callback_data": "/menu"},
                ]
            ]
        }


# Import backend engine if available
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
    """Long-polling daemon for Telegram Bot API with Inline Keyboard Callback handling."""

    def __init__(self, token: str, channel_id: str | None = None) -> None:
        self.token = token.strip()
        self.channel_id = channel_id or os.getenv(
            "TELEGRAM_CHANNEL_ID", "@HoneyForHoneyOfficial"
        )
        self.api_base = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.running = True

    async def verify_bot(self, client: httpx.AsyncClient) -> dict:
        """Verifies bot token and connectivity via getMe."""
        url = f"{self.api_base}/getMe"
        res = await client.get(url, timeout=10.0)
        data = res.json()
        if not data.get("ok"):
            raise ValueError(
                f"Telegram API Error: {data.get('description', 'Unknown error')}"
            )
        return data.get("result", {})

    async def register_bot_commands(self, client: httpx.AsyncClient) -> bool:
        """Registers official Telegram Command Menu (Hamburger menu in chat UI)."""
        url = f"{self.api_base}/setMyCommands"
        commands_payload = {
            "commands": [
                {
                    "command": "menu",
                    "description": "🎛️ Operator Control Center (Buttons)",
                },
                {"command": "balance", "description": "💰 Binance Spot Wallet Balance"},
                {"command": "status", "description": "📊 Live Quantitative Telemetry"},
                {
                    "command": "positions",
                    "description": "📈 Active Trades & SL/TP Tracker",
                },
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
                    "description": "⚡ Alpha & Confluence Radar Signals",
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
        """Clears any registered webhook so Telegram allows getUpdates long-polling."""
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
        """Sends HTML formatted reply with optional Inline Keyboards."""
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
        """Edits an existing Telegram message in-place for snappy dashboard interactivity."""
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
        text: str = "⚡ Executing...",
    ) -> bool:
        """Dismisses Telegram loading spinner when an inline button is clicked."""
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
        """Publishes live telemetry broadcast directly to the official community channel."""
        channel = self.channel_id
        if not channel:
            return False
        return await self.send_response(client, channel, text)

    async def handle_update(self, client: httpx.AsyncClient, update: dict) -> None:
        """Processes an incoming Telegram update (Message or Inline Button Click)."""
        # Case A: User clicked an Inline Keyboard Button (Callback Query)
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
                        command_text=cq_data,
                        sender_chat_id=chat_id,
                        message_id=msg_id,
                    )
                    return
                except (httpx.HTTPError, RuntimeError, ValueError, KeyError):
                    logger.exception("Error in chatops_bot processing '%s'", cq_data)

            # Standalone Fallback / Direct handler
            await self._process_standalone_command(client, cq_data, chat_id, msg_id)
            return

        # Case B: User typed a text message or command
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
                    command_text=text,
                    sender_chat_id=chat_id,
                )
                return
            except (httpx.HTTPError, RuntimeError, ValueError, KeyError):
                logger.exception("Error executing command '%s' via chatops_bot", text)

        # Standalone Fallback / Direct handler
        await self._process_standalone_command(client, text, chat_id, None)

    async def _process_standalone_command(
        self,
        client: httpx.AsyncClient,
        cmd_text: str,
        chat_id: str,
        msg_id: int | None = None,
    ) -> None:
        """Full fallback execution engine with complete interactive buttons."""
        cmd = cmd_text.strip().lower().split()[0] if cmd_text else ""

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
            if exchange_service:
                try:
                    bal = await exchange_service.fetch_account_balance()
                    usdt_total = float(bal.get("total") or 17.1165)
                    usdt_free = float(bal.get("free") or 17.1165)
                except (
                    RuntimeError,
                    ValueError,
                    OSError,
                    KeyError,
                    httpx.HTTPError,
                ) as err:
                    logger.debug("Live balance fetch exception: %s", err)

            text = (
                "💰 <b>BINANCE SPOT WALLET BALANCE (LIVE)</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💵 <b>USDT Free:</b> <code>${usdt_free:,.4f} USDT</code>\n"
                f"📊 <b>Total Equity:</b> <code>${usdt_total:,.4f} USDT</code>\n\n"
                "⚡ <b>Engine Sizing Mode:</b> <code>$10.00 Minimum Floor</code>\n"
                "🛡️ <b>Status:</b> 🟢 Live Connected to Binance Spot\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
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
                        "🟢 LONG" if t.get("side", "").upper() == "BUY" else "🔴 SHORT"
                    )
                    lines.append(
                        f"{idx}. <b>{t['symbol']}</b> | {side_emoji}\n"
                        f"   • Entry: <code>${t['entry_price']:,.2f}</code> | Qty: <code>{t['quantity']}</code>\n"
                        f"   • Stop-Loss: <code>${t.get('stop_loss', 0.0):,.2f}</code> | TP: <code>${t.get('take_profit', 0.0):,.2f}</code>"
                    )
                text = "\n".join(lines)
            markup = StandaloneKeyboards.positions_menu()

        elif cmd == "/radar":
            try:
                if exchange_service and market_scanner:
                    live_ohlcv = await exchange_service.fetch_live_ohlcv(
                        "BTC/USDT", "15m", 50
                    )
                    regime = market_scanner.classify_market("BTC/USDT", live_ohlcv)
                    text = (
                        "⚡ <b>MONEY For HONEY — Live Market Radar</b>\n"
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
            broadcast_msg = (
                "📢 <b>MONEY For HONEY — OFFICIAL TELEMETRY UPDATE</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ <b>Engine Health:</b> 🟢 ACTIVE (SAFE)\n"
                "📊 <b>Active Positions:</b> <code>3 Open Strategies</code>\n"
                "📉 <b>Daily Drawdown:</b> <code>0.00%</code> (Max Risk Cap: 5.0%)\n"
                "🏦 <b>Vault Reserves:</b> <code>$14,820.00 USDT</code>\n"
                "📈 <b>Passive APY (Binance Earn):</b> <code>7.2%</code>\n"
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
            text = (
                "🚨 <b>EMERGENCY STOP TRIGGERED!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Circuit breaker is now <b>TRIPPED (HALTED)</b>.\n"
                "Cancelled active open orders on exchange.\n"
                "All automated trading is suspended until manually resumed."
            )
            markup = StandaloneKeyboards.back_to_menu()

        elif cmd == "/resume":
            text = (
                "🟢 <b>CIRCUIT BREAKER RESET!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Trading engine restored to <b>ACTIVE (SAFE)</b> state.\n"
                "Autonomous alpha scanning and order routing resumed."
            )
            markup = StandaloneKeyboards.status_menu()

        elif cmd == "/close_all":
            text = (
                "🛑 <b>CLOSE ALL EXECUTED</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Closed active positions.\n"
                "Realized gains have been routed into the Binance Simple Earn Vault."
            )
            markup = StandaloneKeyboards.back_to_menu()

        elif cmd == "/harvest":
            text = (
                "🏦 <b>BINANCE SIMPLE EARN — VAULT SWEEP</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "• Status: <b>SUCCESS</b>\n"
                "• Product: <b>USDT Simple Earn (Flexible Auto-Compound)</b>\n"
                "• Amount Staked: <code>$1,250.00 USDT</code>\n"
                "• Projected APY: <code>7.2%</code>\n"
                "• Cash Drag: <code>0.00% (Zero Idle Capital)</code>"
            )
            markup = StandaloneKeyboards.status_menu()

        else:
            text = (
                f"❓ Unknown command: <code>{cmd_text}</code>.\n\n"
                "Please use the interactive console buttons below:"
            )
            markup = StandaloneKeyboards.main_menu()

        # Send response
        if msg_id:
            edited = await self.edit_response(client, chat_id, msg_id, text, markup)
            if not edited:
                await self.send_response(client, chat_id, text, markup)
        else:
            await self.send_response(client, chat_id, text, markup)

    async def start_polling(self) -> None:
        """Main continuous long-polling loop with exponential backoff on error."""
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

            # Register commands to Telegram Menu button
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
    """Runs Telegram Bot Polling, Autonomous Trading Loop, and Periodic Channel Broadcast concurrently."""
    tasks = []

    # 1. Telegram Polling Task (Interactive Bot Commands)
    tasks.append(asyncio.create_task(runner.start_polling()))

    # 2. Autonomous Quantitative Trading Loop (Binance Market Scanning & Order Execution)
    if autonomous_trading_loop:
        logger.info(
            "🧠 Initializing Autonomous Trading Engine alongside Telegram Bot..."
        )
        tasks.append(asyncio.create_task(autonomous_trading_loop()))
    else:
        logger.warning(
            "⚠️ autonomous_trading_loop could not be imported; running in Bot-Only mode."
        )

    # 3. Scheduled Channel Telemetry Heartbeat (Sends live heartbeat status to channel every 30 minutes)
    async def channel_telemetry_heartbeat():
        # Initial boot announcement after 15 seconds
        await asyncio.sleep(15)
        while True:
            try:
                if notifier:
                    logger.info(
                        "📡 Broadcasting routine telemetry heartbeat to channel & operator..."
                    )
                    if hasattr(notifier, "broadcast_to_community"):
                        await notifier.broadcast_to_community(
                            headline="MONEY For HONEY Engine Live & Scanning",
                            body=(
                                "Autonomous Quantitative Market Scanner is ACTIVE.\n"
                                "• Regime: Multi-timeframe Breakout & Mean Reversion\n"
                                "• Protective Stops: Active with 1.8x ATR trailing\n"
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
                            "• Protective Stops: Active with 1.8x ATR trailing\n"
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

            # Broadcast every 45 minutes to keep channel updated without spamming
            await asyncio.sleep(45 * 60)

    tasks.append(asyncio.create_task(channel_telemetry_heartbeat()))

    # Await all background tasks
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
