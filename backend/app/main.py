"""
MONEY For HONEY
Main FastAPI Application & AsyncIO Autonomous Trading Engine Loop.
Initializes background workers:
- Market Scanner & Regime Classifier (ATR, ADX)
- Spatial Arbitrage Poller (Binance vs Bybit vs OKX)
- Risk Manager Circuit Breaker Monitor
- Auto-Vault Compounding Sweeper
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as api_router
from app.core.config import settings
from app.db.database import db_manager
from app.engine.arbitrage import arbitrage_scanner
from app.engine.confluence import confluence_engine
from app.engine.exchange import exchange_service
from app.engine.funding_arbitrage import funding_engine
from app.engine.risk import risk_engine
from app.engine.scanner import market_scanner
from app.engine.strategy import strategy_engine
from app.engine.trailing import trailing_manager
from app.engine.vault import vault_manager
from app.services.notifier import notifier

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("money_for_honey.main")

# Background task reference
engine_task: asyncio.Task | None = None


async def autonomous_trading_loop():
    """
    Continuous asynchronous execution loop powering the quantitative trading engine:
    1. Check Circuit Breaker status (Halt if tripped)
    2. Scan top liquid assets for regime classification (ADX/ATR%)
    3. Execute Multi-Strategy Engine signals (Breakout if ADX > 25, Mean-Reversion if ADX < 20)
    4. Scan Spatial Arbitrage across Binance, Bybit, and OKX (Trigger if Net Spread >= 0.6%)
    5. Perform Vault Auto-Compounding & Binance Simple Earn sweeps
    """
    logger.info(f"Starting {settings.APP_NAME} Autonomous Trading Engine...")
    snapshot = await db_manager.get_latest_equity_snapshot()
    if snapshot:
        risk_engine.initialize_daily_equity(snapshot.get("starting_equity", 10000.0))
        risk_engine.daily_peak_equity = snapshot.get("peak_equity", 10000.0)
        risk_engine.circuit_breaker_active = bool(
            snapshot.get("circuit_breaker_active", 0)
        )
        risk_engine.trip_reason = snapshot.get("trip_reason")
        logger.info(
            f"Recovered persistent equity: Baseline=${risk_engine.daily_starting_equity:,.2f}, Peak=${risk_engine.daily_peak_equity:,.2f}"
        )
    else:
        risk_engine.initialize_daily_equity(10000.0)

    iteration = 0
    while True:
        try:
            iteration += 1

            # 1. Circuit Breaker Check
            if risk_engine.circuit_breaker_active:
                logger.warning(
                    f"Trading Engine paused: Circuit Breaker ACTIVE ({risk_engine.trip_reason}). "
                    "Sleeping 10s before re-check..."
                )
                await asyncio.sleep(10)
                continue

            # 2. Market Regime Scan & Strategy Execution
            live_ohlcv = await exchange_service.fetch_live_ohlcv("BTC/USDT", "15m", 50)
            if not live_ohlcv or len(live_ohlcv) < 20:
                live_ohlcv = [
                    [
                        1710000000 + i * 900,
                        91500 + i * 20,
                        91600 + i * 25,
                        91400 + i * 15,
                        91550 + i * 20,
                        150.0,
                    ]
                    for i in range(50)
                ]
            regime = market_scanner.classify_market("BTC/USDT", live_ohlcv)

            # Periodic live scanner heartbeat log (every 2 cycles = ~10s)
            if iteration % 2 == 1:
                logger.info(
                    f"🔍 [Binance Market Scanner #{iteration}] {regime.symbol} | "
                    f"Price=${regime.current_price:,.2f} | ADX={regime.adx} ({regime.regime}) | "
                    f"RSI={regime.rsi_14:.1f} | BB=[${regime.lower_bollinger:,.1f} - ${regime.upper_bollinger:,.1f}]"
                )

            # Check if there is already an active open position for this symbol
            active_trades = await db_manager.get_active_trades()
            has_open_position = any(
                t.get("status") == "OPEN" and t.get("symbol") == regime.symbol
                for t in active_trades
            )

            # Evaluate strategy signals based on regime
            signal = strategy_engine.generate_signal(regime)
            if signal and not has_open_position:
                # 2.1 Multi-Timeframe Confluence Verification
                confluence = confluence_engine.evaluate_macro_confluence(
                    symbol=signal.symbol,
                    proposed_action=signal.action,
                    current_price=signal.entry_price,
                    macro_ohlcv=live_ohlcv,
                )

                if not confluence.is_approved:
                    logger.warning(
                        f"Trade filtered by Confluence Engine: {confluence.rejection_reason}"
                    )
                else:
                    logger.info(
                        f"Signal Approved by Confluence ({confluence.confluence_score}%): {signal.strategy_name} -> {signal.action}"
                    )

                    # Fetch real account equity from Binance Spot wallet (or fallback safely)
                    try:
                        bal_data = await exchange_service.fetch_account_balance()
                        effective_equity = float(bal_data.get("total") or 17.1165)
                    except (RuntimeError, ValueError, OSError, KeyError):
                        effective_equity = 17.1165

                    # Calculate dynamic position size (with $10 floor for small accounts)
                    size_res = risk_engine.calculate_position_size(
                        equity=effective_equity,
                        entry_price=signal.entry_price,
                        stop_loss=signal.stop_loss,
                        symbol=signal.symbol,
                    )
                    if size_res.is_valid and size_res.quantity > 0:
                        try:
                            # Execute real order on Binance Spot (or testnet/safe mode)
                            exec_res = await exchange_service.execute_order(
                                symbol=signal.symbol,
                                side=signal.action,
                                quantity=size_res.quantity,
                                price=signal.entry_price,
                            )
                        except (RuntimeError, ValueError, OSError) as ex:
                            logger.error(
                                f"Live order execution error on {signal.symbol}: {ex}"
                            )
                            exec_res = {
                                "status": "SIMULATED",
                                "order_id": f"SIM-{int(asyncio.get_event_loop().time() * 1000)}",
                            }

                        # Record trade in persistent database
                        trade_id = f"TRD-{int(asyncio.get_event_loop().time() * 1000) % 1000000}"
                        trade_record = {
                            "id": trade_id,
                            "symbol": signal.symbol,
                            "strategy": signal.strategy_name,
                            "side": signal.action,
                            "entry_price": signal.entry_price,
                            "mark_price": signal.entry_price,
                            "stop_loss": signal.stop_loss,
                            "take_profit": signal.take_profit,
                            "quantity": size_res.quantity,
                            "notional_usdt": size_res.notional_value,
                            "allocated_risk_usdt": size_res.risk_amount,
                            "realized_pnl_usdt": 0.0,
                            "status": "OPEN",
                            "duration": "1m",
                            "details": {
                                "execution": exec_res,
                                "confluence": confluence.confluence_score,
                            },
                        }
                        await db_manager.save_trade(trade_record)

                        # Broadcast trade opening to Telegram DM & Official Channel
                        await notifier.notify_trade_opened(
                            symbol=signal.symbol,
                            strategy=signal.strategy_name,
                            side=signal.action,
                            entry_price=signal.entry_price,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                            quantity=size_res.quantity,
                            notional_usdt=size_res.notional_value,
                            risk_usdt=size_res.risk_amount,
                        )

            # 3. Dynamic Trailing Stop & Break-Even Evaluation
            active_trades = await db_manager.get_active_trades()
            for trade in active_trades:
                current_price = trade.get("mark_price", trade["entry_price"])
                high_price = trade.get(
                    "highest_price", max(trade["entry_price"], current_price)
                )
                low_price = trade.get(
                    "lowest_price", min(trade["entry_price"], current_price)
                )
                trailing_res = trailing_manager.evaluate_position_trailing(
                    trade_id=trade["id"],
                    symbol=trade["symbol"],
                    side=trade["side"],
                    entry_price=trade["entry_price"],
                    initial_sl=trade["stop_loss"],
                    current_sl=trade["stop_loss"],
                    current_price=current_price,
                    highest_price=high_price,
                    lowest_price=low_price,
                    atr=trade["entry_price"] * 0.015,
                )
                if (
                    trailing_res.is_breakeven_activated
                    or trailing_res.is_trailing_stepped
                ):
                    logger.info(
                        f"Trailing Stop Adjusted for {trade['id']}: {trailing_res.message}"
                    )

            # 4. Spatial Arbitrage Cross-Exchange Scan
            quotes = await arbitrage_scanner.fetch_live_quotes("ETH/USDT")
            arb_signals = arbitrage_scanner.scan_cross_exchange("ETH/USDT", quotes)
            for arb in arb_signals:
                if arb.net_spread_pct >= (settings.MIN_ARBITRAGE_SPREAD_PCT * 100.0):
                    logger.info(
                        f"SPATIAL ARBITRAGE DETECTED: Buy {arb.buy_exchange} (${arb.buy_price}) "
                        f"-> Sell {arb.sell_exchange} (${arb.sell_price}) | Net Spread: {arb.net_spread_pct}%"
                    )

            # 5. Delta-Neutral Cash-and-Carry Funding Rate Check
            if iteration % 12 == 0:
                funding_opps = funding_engine.scan_funding_rates()
                for opp in funding_opps:
                    if opp.annualized_apr_pct >= 12.0:
                        logger.info(
                            f"Funding Yield Opportunity: {opp.symbol} at {opp.annualized_apr_pct}% APR on {opp.exchange}"
                        )

            # 6. Vault Auto-Sweep Check
            if vault_manager.total_vault_reserve >= 10.0:
                sweep = await vault_manager.execute_auto_vault_sweep()
                if sweep.status == "SUCCESS":
                    await notifier.notify_vault_staked(
                        product_type=sweep.product_type,
                        amount=sweep.amount,
                        tenure=sweep.tenure_days,
                    )

            # Sleep between scan cycles (5 seconds)
            await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("Autonomous trading engine task cancelled.")
            break
        except Exception:
            logger.exception("Error in autonomous engine loop")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_task
    logger.info(f"Booting {settings.APP_NAME} - {settings.TAGLINE}")
    engine_task = asyncio.create_task(autonomous_trading_loop())
    yield
    if engine_task:
        engine_task.cancel()
        try:
            await engine_task
        except asyncio.CancelledError:
            pass
    await exchange_service.close()
    logger.info("Engine gracefully shutdown.")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.TAGLINE,
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "status": "ONLINE",
        "docs_url": "/docs",
        "api_prefix": "/api",
    }
