"""
Autonomous Multi-Pair Quantitative Scanner & Trading Loop for MONEY For HONEY.
Continuously scans high-liquidity Spot universe:
BTC/USDT, ETH/USDT, SOL/USDT, HYPE/USDT, SUI/USDT, NEAR/USDT, DOGE/USDT, XRP/USDT, BNB/USDT, AVAX/USDT.
"""

import asyncio
import logging

from app.db.database import db_manager
from app.engine.exchange import exchange_service
from app.engine.risk import risk_engine
from app.engine.scanner import market_scanner
from app.engine.strategy import strategy_engine
from app.engine.vault import vault_manager
from app.services.notifier import notifier

logger = logging.getLogger("money_for_honey.engine_loop")

# Multi-Pair Spot High-Liquidity Basket
SCAN_PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "HYPE/USDT",
    "SUI/USDT",
    "NEAR/USDT",
    "DOGE/USDT",
    "XRP/USDT",
    "BNB/USDT",
    "AVAX/USDT",
]


async def evaluate_pair_opportunity(symbol: str, tick_count: int) -> None:
    """Memindai dan mengevaluasi satu pair untuk mencari sinyal entry berprobabilitas tinggi."""
    try:
        # Ambil data candlestick 15m live
        ohlcv = await exchange_service.fetch_live_ohlcv(
            symbol, timeframe="15m", limit=50
        )
        if not ohlcv or len(ohlcv) < 20:
            return

        regime = market_scanner.classify_market(symbol, ohlcv)
        signal = strategy_engine.generate_signal(regime)

        logger.info(
            f"🔍 [Scanner #{tick_count}] {symbol} | Price=${regime.current_price:,.2f} | "
            f"ADX={regime.adx:.2f} ({regime.regime}) | RSI={regime.rsi_14:.1f} | "
            f"BB=[${regime.lower_bollinger:,.1f} - ${regime.upper_bollinger:,.1f}]"
        )

        if signal and signal.action == "BUY":
            # Cek saldo dan slot alokasi risiko
            bal = await exchange_service.fetch_account_balance()
            total_bal = float(bal.get("total") or 17.1165)
            active_trades = await db_manager.get_active_trades()

            # Verifikasi apakah sudah ada posisi aktif pada pair yang sama
            if any(t.get("symbol") == symbol for t in active_trades):
                return

            sizing = risk_engine.calculate_position_size(
                total_balance_usdt=total_bal,
                entry_price=signal.entry_price,
                stop_loss_price=signal.stop_loss,
                active_positions_count=len(active_trades),
            )

            if sizing.get("allowed"):
                qty = sizing["quantity"]
                logger.info(
                    f"🚀 [SIGNAL TRIGGERED] BUY {qty} {symbol} @ ${signal.entry_price} | "
                    f"SL: ${signal.stop_loss} | TP: ${signal.take_profit} | Strategy: {signal.strategy_name}"
                )

                # Eksekusi Order Riil di Binance Spot (fix unused variable F841)
                await exchange_service.execute_order(
                    symbol=symbol,
                    side="BUY",
                    quantity=qty,
                    order_type="market",
                )

                # Rekam ke Database Posisi Aktif
                trade_record = {
                    "symbol": symbol,
                    "strategy": signal.strategy_name,
                    "side": "BUY",
                    "entry_price": signal.entry_price,
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                    "quantity": qty,
                    "notional_usdt": sizing["notional_usdt"],
                    "allocated_risk_usdt": sizing["risk_amount_usdt"],
                    "status": "ACTIVE",
                }
                await db_manager.save_active_trade(trade_record)

                # Kirim Notifikasi Instan ke Telegram & Channel
                if notifier:
                    msg = (
                        f"🎯 <b>NEW SPOT POSITION EXECUTED!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Symbol:</b> #{symbol.replace('/', '')} | 🟢 LONG\n"
                        f"💵 <b>Entry Price:</b> <code>${signal.entry_price:,.4f}</code>\n"
                        f"🛡️ <b>Stop Loss (2.0x ATR):</b> <code>${signal.stop_loss:,.4f}</code>\n"
                        f"🎯 <b>Take Profit (1:2.2):</b> <code>${signal.take_profit:,.4f}</code>\n"
                        f"📦 <b>Position Sizing:</b> <code>${sizing['notional_usdt']} USDT</code> ({qty} {symbol.split('/')[0]})\n"
                        f"⚡ <b>Strategy:</b> {signal.strategy_name.replace('_', ' ')}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🐝 <i>Automated by MONEY For HONEY Engine</i>"
                    )
                    await notifier.send_telegram_message(msg, broadcast_to_channel=True)

    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as ex:
        logger.debug(f"Pair evaluation skip for {symbol}: {ex}")
    except Exception as ex:  # noqa: BLE001
        logger.warning(f"Unexpected error in pair evaluation for {symbol}: {ex}")


async def autonomous_trading_loop() -> None:
    """Main continuous multi-pair polling loop."""
    logger.info("⚡ MONEY For HONEY Multi-Pair Engine Loop Activated!")
    tick = 0
    while True:
        try:
            # Evaluasi seluruh pair secara berputar
            for pair in SCAN_PAIRS:
                tick += 1
                await evaluate_pair_opportunity(pair, tick)
                await asyncio.sleep(2)  # Jeda aman per pair agar bebas rate-limit

            # Evaluasi Trailing Stops & Take Profit untuk posisi yang sedang aktif
            active_trades = await db_manager.get_active_trades()
            for trade in active_trades:
                sym = trade["symbol"]
                ticker = await exchange_service.fetch_ticker(sym)
                mark_price = float(ticker.get("last") or trade["entry_price"])

                # Hitung kondisi TP / SL
                entry = float(trade["entry_price"])
                sl = float(trade.get("stop_loss", 0))
                tp = float(trade.get("take_profit", 0))
                qty = float(trade["quantity"])

                # Cek Take Profit
                if mark_price >= tp > 0:
                    profit = round((mark_price - entry) * qty, 2)
                    await exchange_service.execute_order(sym, "SELL", qty, "market")
                    await db_manager.close_trade(trade["id"], mark_price, profit)

                    # Waterfall distribution (70% Reinvest, 30% Vault)
                    if profit > 0:
                        vault_manager.distribute_trade_profit(profit)

                    if notifier:
                        tp_msg = (
                            f"🎉 <b>TAKE PROFIT HIT! (+${profit:.2f} USDT)</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"📊 <b>Symbol:</b> #{sym.replace('/', '')}\n"
                            f"💵 <b>Entry:</b> <code>${entry:,.4f}</code> ➡️ <b>Exit:</b> <code>${mark_price:,.4f}</code>\n"
                            f"🍯 <b>Distribution:</b> 70% Reinvested (${profit * 0.7:.2f}), 30% Binance Earn Vault (${profit * 0.3:.2f})\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                        )
                        await notifier.send_telegram_message(
                            tp_msg, broadcast_to_channel=True
                        )

                # Cek Stop Loss Protektif
                elif mark_price <= sl and sl > 0:
                    loss = round((mark_price - entry) * qty, 2)
                    await exchange_service.execute_order(sym, "SELL", qty, "market")
                    await db_manager.close_trade(trade["id"], mark_price, loss)
                    if notifier:
                        sl_msg = (
                            f"🛡️ <b>STOP LOSS EXECUTED (CAPITAL PROTECTED)</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"📊 <b>Symbol:</b> #{sym.replace('/', '')}\n"
                            f"💵 <b>Entry:</b> <code>${entry:,.4f}</code> ➡️ <b>Exit:</b> <code>${mark_price:,.4f}</code>\n"
                            f"📉 <b>PnL:</b> <code>-${abs(loss):.2f} USDT</code>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                        )
                        await notifier.send_telegram_message(
                            sl_msg, broadcast_to_channel=True
                        )

        except (RuntimeError, ValueError, KeyError, TypeError, OSError) as err:
            logger.warning(f"Engine loop handled error: {err}")
        except Exception as err:  # noqa: BLE001
            logger.error(f"Engine loop unexpected error: {err}")

        await asyncio.sleep(5)
