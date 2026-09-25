async def notify_stop_loss(
    self,
    symbol: str,
    side: str,
    entry_price: float,
    exit_price: float,
    quantity: float,
    realized_pnl: float,
    reason: str = "Protective Stop Loss Hit",
) -> None:
    """Dispatches stop-loss execution alert to DM and Official Channel."""
    side_emoji = "🟢 LONG" if side.upper() == "BUY" else "🔴 SHORT"
    pnl_str = (
        f"-${abs(realized_pnl):,.2f}" if realized_pnl <= 0 else f"+${realized_pnl:,.2f}"
    )
    msg = (
        "🛡️ <b>STOP LOSS EXECUTED (CAPITAL PROTECTED)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Symbol:</b> #{symbol.replace('/', '')} | {side_emoji}\n"
        f"💵 <b>Entry Price:</b> <code>${entry_price:,.4f}</code>\n"
        f"🛑 <b>Exit Price:</b> <code>${exit_price:,.4f}</code>\n"
        f"📦 <b>Position Size:</b> <code>{quantity}</code>\n"
        f"📉 <b>Realized PnL:</b> <code>{pnl_str} USDT</code>\n"
        f"⚠️ <b>Trigger:</b> {reason}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ <i>Risk Management Active: Capital preserved for next setup.</i>\n"
        '📢 <a href="https://t.me/HoneyForHoneyOfficial">t.me/HoneyForHoneyOfficial</a>'
    )
    await self.send_telegram_message(msg, broadcast_to_channel=True)
