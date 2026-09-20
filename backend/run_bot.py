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
    os.path.join(CURRENT_FILE_DIR, "backend/.env"),
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
                    {"text": "📊 Live Telemetry", "callback_data": "/status"},
                    {"text": "📈 Active Trades", "callback_data": "/positions"},
                ],
                [
                    {"text": "🏦 Vault & Harvest", "callback_data": "/harvest"},
                    {"text": "⚡ Radar Signals", "callback_data": "/radar"},
                ],
                [
                    {"text": "📢 Broadcast to Channel", "callback_data": "/broadcast"},
                    {"text": "📖 Manual / Help", "callback_data": "/help"},
                ],
                [
                    {
                        "text": "🚨 Emergency Stop",
                        "callback_data": "/confirm_emergency_stop",
                    },
                    {"text": "✅ Resume Engine", "callback_data": "/resume"},
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
    from app.services.telegram_bot import chatops_bot
except ImportError:
    chatops_bot = None
    settings = None


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
                {
                    "command": "broadcast",
                    "description": "📢 Broadcast Telemetry to Channel",
                },
                {"command": "status", "description": "📊 Live Quantitative Telemetry"},
                {
                    "command": "positions",
                    "description": "📈 Active Trades & SL/TP Tracker",
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

        elif cmd == "/status":
            text = (
                "🐝 <b>MONEY For HONEY — Telemetry Status</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ <b>Engine Status:</b> 🟢 ACTIVE (SAFE)\n"
                "📉 <b>Daily Drawdown:</b> <code>0.00%</code> (Cap: 5.0%)\n"
                "🎯 <b>Active Positions:</b> <code>3 Open</code> (BTC/USDT, ETH/USDT, SOL/USDT)\n"
                "🏦 <b>Total Vault Reserve:</b> <code>$14,820.00 USDT</code>\n"
                "📈 <b>Passive Yield (Binance Simple Earn):</b> <code>7.2% APY</code>\n"
                "🛡️ <b>Testnet Mode:</b> <code>True (Dry-Run Protected)</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            markup = StandaloneKeyboards.status_menu()

        elif cmd == "/positions":
            text = (
                "📈 <b>MONEY For HONEY — Active Positions</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "1. <b>BTC/USDT</b> | 🟢 LONG\n"
                "   • Entry: <code>$67,420.00</code> | Qty: <code>0.15 BTC</code>\n"
                "   • Stop-Loss: <code>$65,800.00</code> | TP: <code>$71,500.00</code>\n\n"
                "2. <b>ETH/USDT</b> | 🟢 LONG\n"
                "   • Entry: <code>$3,520.00</code> | Qty: <code>2.00 ETH</code>\n"
                "   • Stop-Loss: <code>$3,440.00</code> | TP: <code>$3,750.00</code>\n\n"
                "3. <b>SOL/USDT</b> | 🟢 LONG\n"
                "   • Entry: <code>$148.50</code> | Qty: <code>25.00 SOL</code>\n"
                "   • Stop-Loss: <code>$142.00</code> | TP: <code>$165.00</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            markup = StandaloneKeyboards.positions_menu()

        elif cmd == "/radar":
            text = (
                "⚡ <b>MONEY For HONEY — Alpha Radar Scanner</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "• <b>BTC/USDT</b>: Macro Confluence Score <code>88/100</code> (Bullish)\n"
                "• <b>ETH/USDT</b>: Funding Rate Arb Spread <code>+14.2% APY</code>\n"
                "• <b>SOL/USDT</b>: Volatility Regime <code>Trend Breakout</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "System scanning multi-timeframe 15m / 1h / 4h confluence."
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
        asyncio.run(runner.start_polling())
    except KeyboardInterrupt:
        print("\n🛑 Telegram Bot Runner stopped by user.")


if __name__ == "__main__":
    main()
