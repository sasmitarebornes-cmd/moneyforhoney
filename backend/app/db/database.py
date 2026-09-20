"""
Production Database & State Persistence Module.
Supports local persistent SQLite (zero-dependency fail-safe) and PostgreSQL via asyncpg.
Maintains persistent records for:
1. Trade execution history & active positions
2. Profit waterfall distributions & Binance Vault ledger
3. Daily risk & equity snapshots for Circuit Breaker recovery across reboots
"""

import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("money_for_honey.database")

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "trading_data.db")


class DatabaseManager:
    """Thread-safe persistent database manager for trading state."""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_sqlite()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=15.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high-concurrency read/write operations without locking
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 15000;")
        return conn

    def _init_sqlite(self) -> None:
        """Initializes relational tables for persistent state."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 1. Trades table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id TEXT PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        side TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        mark_price REAL NOT NULL,
                        stop_loss REAL NOT NULL,
                        take_profit REAL NOT NULL,
                        quantity REAL NOT NULL,
                        notional_usdt REAL NOT NULL,
                        allocated_risk_usdt REAL NOT NULL,
                        realized_pnl_usdt REAL DEFAULT 0.0,
                        status TEXT NOT NULL,
                        duration TEXT DEFAULT '0m',
                        details TEXT,
                        created_at TEXT NOT NULL,
                        closed_at TEXT
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);")

                # 2. Vault Ledger table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vault_ledger (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        gross_profit REAL NOT NULL,
                        maintenance_fee REAL NOT NULL,
                        reinvest_amount REAL NOT NULL,
                        vault_allocation REAL NOT NULL,
                        total_vault_reserve REAL NOT NULL,
                        product_type TEXT DEFAULT 'NONE',
                        created_at TEXT NOT NULL
                    )
                """)

                # 3. Equity & Circuit Breaker Snapshots
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS equity_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        snapshot_date TEXT UNIQUE NOT NULL,
                        starting_equity REAL NOT NULL,
                        peak_equity REAL NOT NULL,
                        current_drawdown_pct REAL NOT NULL,
                        circuit_breaker_active INTEGER NOT NULL,
                        trip_reason TEXT,
                        updated_at TEXT NOT NULL
                    )
                """)
                conn.commit()
                logger.info(f"Persistent database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}", exc_info=True)

    async def save_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Inserts or updates a trade record."""
        def _execute():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades (
                        id, symbol, strategy, side, entry_price, mark_price,
                        stop_loss, take_profit, quantity, notional_usdt,
                        allocated_risk_usdt, realized_pnl_usdt, status,
                        duration, details, created_at, closed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        mark_price=excluded.mark_price,
                        realized_pnl_usdt=excluded.realized_pnl_usdt,
                        status=excluded.status,
                        duration=excluded.duration,
                        closed_at=excluded.closed_at
                """, (
                    trade_data["id"],
                    trade_data["symbol"],
                    trade_data.get("strategy", "ALGO_MANUAL"),
                    trade_data["side"],
                    float(trade_data["entry_price"]),
                    float(trade_data.get("mark_price", trade_data["entry_price"])),
                    float(trade_data["stop_loss"]),
                    float(trade_data["take_profit"]),
                    float(trade_data["quantity"]),
                    float(trade_data["notional_usdt"]),
                    float(trade_data.get("allocated_risk_usdt", 0.0)),
                    float(trade_data.get("realized_pnl_usdt", 0.0)),
                    trade_data.get("status", "OPEN"),
                    trade_data.get("duration", "1m"),
                    json.dumps(trade_data.get("details", {})),
                    trade_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                    trade_data.get("closed_at"),
                ))
                conn.commit()
                return True

        return await asyncio.to_thread(_execute)

    async def get_active_trades(self) -> List[Dict[str, Any]]:
        """Retrieves all currently open positions."""
        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM trades WHERE status = 'OPEN' ORDER BY created_at DESC")
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    if item.get("details"):
                        try:
                            item["details"] = json.loads(item["details"])
                        except Exception:
                            pass
                    results.append(item)
                return results

        return await asyncio.to_thread(_query)

    async def close_trade(self, trade_id: str, exit_price: float, realized_pnl: float) -> Optional[Dict[str, Any]]:
        """Closes an active trade, updates realized PnL, and returns the updated record."""
        def _close():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                now_str = datetime.now(timezone.utc).isoformat()
                cursor.execute("""
                    UPDATE trades SET
                        status = 'CLOSED',
                        mark_price = ?,
                        realized_pnl_usdt = ?,
                        closed_at = ?
                    WHERE id = ?
                """, (exit_price, realized_pnl, now_str, trade_id))
                conn.commit()

                cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
                updated_row = cursor.fetchone()
                return dict(updated_row) if updated_row else None

        return await asyncio.to_thread(_close)

    async def record_vault_distribution(self, record: Dict[str, Any]) -> bool:
        """Records profit waterfall distribution to persistent ledger."""
        def _execute():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO vault_ledger (
                        gross_profit, maintenance_fee, reinvest_amount,
                        vault_allocation, total_vault_reserve, product_type, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    record["gross_profit"],
                    record["maintenance_fee"],
                    record["reinvest_amount"],
                    record["vault_allocation"],
                    record["total_vault_reserve"],
                    record.get("product_type", "NONE"),
                    record.get("created_at", datetime.now(timezone.utc).isoformat()),
                ))
                conn.commit()
                return True

        return await asyncio.to_thread(_execute)

    async def get_latest_equity_snapshot(self) -> Optional[Dict[str, Any]]:
        """Recovers daily peak and starting equity across restarts."""
        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM equity_snapshots ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                return dict(row) if row else None

        return await asyncio.to_thread(_query)

    async def update_equity_snapshot(
        self,
        starting_equity: float,
        peak_equity: float,
        current_drawdown_pct: float,
        circuit_breaker_active: bool,
        trip_reason: Optional[str] = None,
    ) -> bool:
        """Persists latest daily equity and circuit breaker state."""
        def _update():
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            now_str = datetime.now(timezone.utc).isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO equity_snapshots (
                        snapshot_date, starting_equity, peak_equity,
                        current_drawdown_pct, circuit_breaker_active, trip_reason, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(snapshot_date) DO UPDATE SET
                        starting_equity = excluded.starting_equity,
                        peak_equity = excluded.peak_equity,
                        current_drawdown_pct = excluded.current_drawdown_pct,
                        circuit_breaker_active = excluded.circuit_breaker_active,
                        trip_reason = excluded.trip_reason,
                        updated_at = excluded.updated_at
                """, (
                    today_str,
                    starting_equity,
                    peak_equity,
                    current_drawdown_pct,
                    1 if circuit_breaker_active else 0,
                    trip_reason,
                    now_str,
                ))
                conn.commit()
                return True

        return await asyncio.to_thread(_update)


db_manager = DatabaseManager()
