"""
MultiChannel Notifier Service.
Integrates:
1. Telegram Bot & Channel (via httpx AsyncClient) for trade fills, profit waterfalls, and vault auto-sweeps.
2. Dual-channel broadcast (Private Operator DM + Public/Community Telegram Channel).
3. WhatsApp Business Cloud API for emergency priority alerts when Circuit Breaker is tripped or API connectivity fails.
"""

import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv

# Auto-locate and load .env file from multiple parent directory levels
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_ENV_PATHS = [
    os.path.join(CURRENT_FILE_DIR, "../../../.env"),  # repo root
    os.path.join(CURRENT_FILE_DIR, "../../.env"),  # backend root
    os.path.join(CURRENT_FILE_DIR, "../.env"),
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.getcwd(), "../.env"),
]
for env_p in POSSIBLE_ENV_PATHS:
    if os.path.isfile(env_p):
        load_dotenv(env_p, override=True)
        break

try:
    from app.core.config import settings
except ImportError:

    class StandaloneSettings:
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
        TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@HoneyForHoneyOfficial")
        WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "")
        WHATSAPP_PHONE_NUMBER = os.getenv("WHATSAPP_PHONE_NUMBER", "")
        WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
        APP_NAME = "MONEY For HONEY"

    settings = StandaloneSettings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("money_for_honey.notifier")


class MultiChannelNotifier:
    """Dispatches real-time quantitative alerts, community channel broadcasts, and emergency notifications."""

    def __init__(self) -> None:
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN") or getattr(
            settings, "TELEGRAM_BOT_TOKEN", ""
        )
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID") or getattr(
            settings, "TELEGRAM_CHAT_ID", ""
        )
        self.telegram_channel_id = (
            os.getenv("TELEGRAM_CHANNEL_ID")
            or getattr(settings, "TELEGRAM_CHANNEL_ID", "@HoneyForHoneyOfficial")
            or "@HoneyForHoneyOfficial"
        )
        self.whatsapp_url = os.getenv("WHATSAPP_API_URL") or getattr(
            settings, "WHATSAPP_API_URL", ""
        )
        self.whatsapp_phone = os.getenv("WHATSAPP_PHONE_NUMBER") or getattr(
            settings, "WHATSAPP_PHONE_NUMBER", ""
        )
        self.whatsapp_token = os.getenv("WHATSAPP_API_TOKEN") or getattr(
            settings, "WHATSAPP_API_TOKEN", ""
        )

    async def _send_single_telegram(
        self, client: httpx.AsyncClient, chat_id: str, text: str
    ) -> bool:
        """Helper to send a message to a single Telegram target (Chat ID or @channel_username)."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            data = resp.json()
            if resp.status_code == 200 and data.get("ok"):
                print(f"✅ Telegram message successfully delivered to: {chat_id}")
                logger.info("Telegram dispatch to %s succeeded.", chat_id)
                return True
            print(
                f"❌ Telegram API Error for {chat_id}: HTTP {resp.status_code} - {data.get('description', resp.text)}"
            )
            logger.warning(
                "Telegram dispatch to %s failed: %s %s",
                chat_id,
                resp.status_code,
                resp.text,
            )
            return False
        except (httpx.HTTPError, httpx.RequestError, OSError) as err:
            print(f"❌ Telegram network error for {chat_id}: {err}")
            logger.error("Telegram network error to %s: %s", chat_id, err)
            return False
        except Exception as err:
            print(f"❌ Unexpected Telegram error for {chat_id}: {err}")
            logger.exception("Unexpected error sending Telegram message to %s", chat_id)
            return False

    async def send_telegram_message(
        self,
        text: str,
        target_chat_id: str | None = None,
        broadcast_to_channel: bool = True,
    ) -> bool:
        """
        Sends formatted HTML notification to Telegram.
        Automatically broadcasts to BOTH Private Operator DM AND the Official Channel!
        """
        if (
            not self.telegram_token
            or self.telegram_token == "your_telegram_bot_token_here"
        ):
            print(f"⚠️ [SIMULATION - NO TOKEN FOUND] -> {text[:80]}...")
            logger.info("[SIMULATED TELEGRAM DISPATCH] -> %s...", text[:100])
            return True

        targets = []
        if target_chat_id:
            targets.append(str(target_chat_id))
        else:
            if (
                self.telegram_chat_id
                and str(self.telegram_chat_id) != "your_telegram_chat_id_here"
            ):
                targets.append(str(self.telegram_chat_id))
            if broadcast_to_channel and self.telegram_channel_id:
                channel = str(self.telegram_channel_id)
                if channel not in targets:
                    targets.append(channel)

        if not targets:
            print(
                "⚠️ Telegram dispatch skipped: Missing target chat_id/channel_id in configuration."
            )
            logger.warning(
                "Telegram dispatch skipped: Missing target chat_id/channel_id."
            )
            return False

        success = False
        async with httpx.AsyncClient(timeout=10.0) as client:
            for target in targets:
                delivered = await self._send_single_telegram(client, target, text)
                if delivered:
                    success = True

        return success

    async def send_whatsapp_emergency(self, alert_title: str, alert_body: str) -> bool:
        """
        Sends high-priority WhatsApp message when Circuit Breaker trips or critical API disconnects.
        """
        message_body = (
            f"🚨 *[MONEY For HONEY EMERGENCY ALERT]* 🚨\n\n"
            f"*Trigger:* {alert_title}\n"
            f"*Details:* {alert_body}\n"
            f"*Action Taken:* Circuit breaker engaged. All active orders cancelled. Engine halted."
        )

        if not (self.whatsapp_url and self.whatsapp_token and self.whatsapp_phone):
            logger.critical("[SIMULATED WHATSAPP EMERGENCY ALERT] -> %s", message_body)
            return True

        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": self.whatsapp_phone,
            "type": "text",
            "text": {"body": message_body},
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.whatsapp_url, headers=headers, json=payload
                )
                if resp.status_code in (200, 201):
                    logger.critical("WhatsApp emergency alert dispatched successfully.")
                    return True
                logger.error("WhatsApp API error: %s %s", resp.status_code, resp.text)
                return False
        except (httpx.HTTPError, httpx.RequestError, OSError) as err:
            logger.error("WhatsApp emergency network error: %s", err)
            return False
        except Exception:
            logger.exception("Unexpected error sending WhatsApp emergency alert")
            return False

    async def notify_trade_opened(
        self,
        symbol: str,
        strategy: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: float,
        notional_usdt: float,
        risk_usdt: float,
    ) -> None:
        """Dispatches rich trade entry report to both DM and Official Channel."""
        side_emoji = "🟢 LONG / BUY" if side.upper() == "BUY" else "🔴 SHORT / SELL"
        msg = (
            f"🚀 <b>TRADE SIGNAL EXECUTED | {getattr(settings, 'APP_NAME', 'MONEY For HONEY')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Symbol:</b> #{symbol.replace('/', '')}\n"
            f"⚡ <b>Action:</b> {side_emoji}\n"
            f"🧠 <b>Strategy:</b> <code>{strategy}</code>\n"
            f"💵 <b>Entry Price:</b> <code>${entry_price:,.4f}</code>\n"
            f"🛡️ <b>Stop Loss:</b> <code>${stop_loss:,.4f}</code>\n"
            f"🎯 <b>Take Profit:</b> <code>${take_profit:,.4f}</code>\n"
            f"📦 <b>Position Size:</b> <code>{quantity}</code> (${notional_usdt:,.2f} USDT)\n"
            f"⚖️ <b>Risk Allocated:</b> <code>${risk_usdt:,.2f}</code> (1.5% Strict Cap)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🐝 <i>Autonomous Wealth Compounding Engine Active</i>\n"
            '📢 <a href="https://t.me/HoneyForHoneyOfficial">t.me/HoneyForHoneyOfficial</a>'
        )
        await self.send_telegram_message(msg, broadcast_to_channel=True)

    async def notify_profit_harvest(
        self,
        gross_profit: float,
        maintenance_fee: float,
        reinvest_equity: float,
        vault_deposit: float,
        total_vault_balance: float,
    ) -> None:
        """Dispatches automated profit compounding waterfall to DM and Official Channel."""
        msg = (
            "🍯 <b>PROFIT WATERFALL & REINVESTMENT HARVEST</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Gross Profit Realized:</b> <code>+${gross_profit:,.2f} USDT</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"▫️ <b>5% Platform Reserve:</b> -${maintenance_fee:,.2f}\n"
            f"▫️ <b>70% Trading Reinvestment:</b> <code>+${reinvest_equity:,.2f} USDT</code>\n"
            f"▫️ <b>30% Vault Savings:</b> <code>+${vault_deposit:,.2f} USDT</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 <b>Total Vault Reserve:</b> <code>${total_vault_balance:,.2f} USDT</code>\n"
            "<i>Auto-Compounding Wealth Cycle Executed</i>\n"
            '📢 <a href="https://t.me/HoneyForHoneyOfficial">t.me/HoneyForHoneyOfficial</a>'
        )
        await self.send_telegram_message(msg, broadcast_to_channel=True)

    async def notify_vault_staked(
        self, product_type: str, amount: float, tenure: int | None
    ) -> None:
        """Dispatches Binance Simple Earn subscription summary to DM and Official Channel."""
        tenure_str = (
            f"{tenure}-Day Locked Staking" if tenure else "Flexible Auto-Compound"
        )
        msg = (
            "🔒 <b>BINANCE SIMPLE EARN AUTO-SWEEP</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Product:</b> {product_type} ({tenure_str})\n"
            f"• <b>Subscribed Amount:</b> <code>${amount:,.2f} USDT</code>\n"
            "• <b>Yield Strategy:</b> Passive High-Yield Self-Wealth Staking\n"
            "• <b>Cash Drag:</b> <code>0.00% (Zero Idle Capital)</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            '📢 <a href="https://t.me/HoneyForHoneyOfficial">t.me/HoneyForHoneyOfficial</a>'
        )
        await self.send_telegram_message(msg, broadcast_to_channel=True)

    async def notify_circuit_breaker(self, reason: str, drawdown_pct: float) -> None:
        """Fires synchronized dual-channel emergency alerts."""
        telegram_msg = (
            "⛔ <b>CIRCUIT BREAKER TRIGGERED</b> ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Current Drawdown:</b> <code>{drawdown_pct * 100:.2f}%</code>\n"
            "<b>System Status:</b> ALL TRADING HALTED. Orders Cancelled.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        await self.send_telegram_message(telegram_msg, broadcast_to_channel=True)
        await self.send_whatsapp_emergency(
            "CIRCUIT BREAKER ENGAGED",
            f"{reason} | Drawdown: {drawdown_pct * 100:.2f}%",
        )


notifier = MultiChannelNotifier()

# Standalone Diagnostic Test Runner
if __name__ == "__main__":

    async def _test():
        print("=" * 60)
        print("⚡ MONEY For HONEY — Notifier Diagnostic & Test Broadcast")
        print("=" * 60)
        n = MultiChannelNotifier()
        token_preview = (
            f"{n.telegram_token[:6]}...{n.telegram_token[-4:]}"
            if len(n.telegram_token) > 10
            else "MISSING"
        )
        print(f"• Bot Token: {token_preview}")
        print(f"• Private Chat ID: {n.telegram_chat_id}")
        print(f"• Official Channel ID: {n.telegram_channel_id}")
        print("=" * 60)
        print("📡 Dispatching live test signal...")
        await n.notify_trade_opened(
            symbol="BTC/USDT",
            strategy="Triple-Barrier Confluence",
            side="BUY",
            entry_price=67420.50,
            stop_loss=65800.00,
            take_profit=71500.00,
            quantity=0.15,
            notional_usdt=10113.07,
            risk_usdt=243.08,
        )
        print("=" * 60)

    asyncio.run(_test())
