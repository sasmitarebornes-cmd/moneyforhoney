import { ActiveTrade, HistoricalTrade, VaultData } from "../types";

export interface BackendStatusResponse {
  engine_status?: string;
  active_trades_count?: number;
  daily_drawdown_pct?: number;
  circuit_breaker_active?: boolean;
  total_equity_usdt?: number;
  testnet_mode?: boolean;
  account_balance?: {
    free?: number;
    total?: number;
    currency?: string;
  };
}

export class LiveBridgeService {
  private static host: string = localStorage.getItem("MFH_BACKEND_HOST") || "";

  public static getHost(): string {
    return this.host;
  }

  public static setHost(newHost: string): void {
    this.host = newHost;
    if (newHost) {
      localStorage.setItem("MFH_BACKEND_HOST", newHost);
    } else {
      localStorage.removeItem("MFH_BACKEND_HOST");
    }
  }

  public static async testConnection(
    targetHost?: string,
  ): Promise<{
    success: boolean;
    data?: any;
    latency: number;
    error?: string;
  }> {
    const url = targetHost || this.host;
    if (!url) {
      return { success: false, latency: 0, error: "Endpoint belum dimasukkan" };
    }

    const cleanUrl = url.endsWith("/") ? url.slice(0, -1) : url;
    const start = performance.now();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      // Try /api/engine/status or /docs or /
      const response = await fetch(`${cleanUrl}/api/engine/status`, {
        method: "GET",
        signal: controller.signal,
        headers: { Accept: "application/json" },
      }).catch(async () => {
        // Fallback to /api/health
        return await fetch(`${cleanUrl}/api/health`, {
          method: "GET",
          signal: controller.signal,
          headers: { Accept: "application/json" },
        });
      });

      clearTimeout(timeoutId);
      const latency = Math.round(performance.now() - start);

      if (response && response.ok) {
        const json = await response.json();
        return { success: true, data: json, latency };
      } else {
        return {
          success: false,
          latency,
          error: `HTTP ${response?.status || "Unknown"}`,
        };
      }
    } catch (err: any) {
      const latency = Math.round(performance.now() - start);
      return {
        success: false,
        latency,
        error:
          err.name === "AbortError"
            ? "Koneksi timeout (6s). Periksa endpoint atau firewall Anda."
            : err.message,
      };
    }
  }

  public static async fetchEngineStatus(): Promise<BackendStatusResponse | null> {
    if (!this.host) return null;
    const cleanUrl = this.host.endsWith("/")
      ? this.host.slice(0, -1)
      : this.host;
    try {
      const res = await fetch(`${cleanUrl}/api/engine/status`);
      if (res.ok) return await res.json();
    } catch {
      // silent fallback
    }
    return null;
  }

  public static async fetchLiveTrades(): Promise<ActiveTrade[] | null> {
    if (!this.host) return null;
    const cleanUrl = this.host.endsWith("/")
      ? this.host.slice(0, -1)
      : this.host;
    try {
      const res = await fetch(`${cleanUrl}/api/trades/active`);
      if (res.ok) {
        const raw = await res.json();
        if (Array.isArray(raw)) {
          return raw.map((t: any) => {
            const entry = Number(t.entry_price ?? t.entryPrice ?? 0);
            const mark = Number(t.mark_price ?? t.markPrice ?? entry);
            const sl = Number(t.stop_loss ?? t.stopLoss ?? 0);
            const tp = Number(t.take_profit ?? t.takeProfit ?? 0);
            const qty = Number(t.quantity ?? 0);
            const rawNotional = t.notional_usdt ?? t.notionalUsdt;
            const notional =
              rawNotional != null
                ? Number(rawNotional)
                : entry * qty > 0
                  ? entry * qty
                  : 10;
            const risk = Number(
              t.allocated_risk_usdt ?? t.allocatedRiskUsdt ?? notional * 0.015,
            );
            const pnl = Number(
              t.unrealized_pnl_usdt ?? t.unrealizedPnlUsdt ?? 0,
            );
            const pnlPct = notional > 0 ? (pnl / notional) * 100 : 0;
            return {
              id: String(
                t.id || `live-${Math.random().toString(36).slice(2, 7)}`,
              ),
              symbol: String(t.symbol || "BTC/USDT"),
              strategy: String(t.strategy || "DYNAMIC_RANGE_ACCUMULATOR"),
              side: (t.side || "BUY").toUpperCase() as
                | "BUY"
                | "SELL"
                | "ARBITRAGE",
              entryPrice: entry,
              markPrice: mark,
              stopLoss: sl,
              takeProfit: tp,
              quantity: qty,
              notionalUsdt: notional,
              allocatedRiskUsdt: risk,
              unrealizedPnlUsdt: pnl,
              unrealizedPnlPct: Number(pnlPct.toFixed(2)),
              duration: String(t.duration || "15m"),
              leverage: String(t.leverage || "Spot 1x"),
              trailingStopActive: Boolean(
                t.trailing_stop_active ?? t.trailingStopActive ?? false,
              ),
            };
          });
        }
      }
    } catch {
      // silent fallback
    }
    return null;
  }

  public static async fetchClosedTrades(): Promise<HistoricalTrade[] | null> {
    if (!this.host) return null;
    const cleanUrl = this.host.endsWith("/")
      ? this.host.slice(0, -1)
      : this.host;
    try {
      const res = await fetch(`${cleanUrl}/api/trades/closed?limit=50`);
      if (res.ok) {
        const raw = await res.json();
        if (Array.isArray(raw)) {
          return raw.map((item: any) => {
            const realized = Number(
              item.realized_pnl_usdt ?? item.realizedPnlUsdt ?? 0,
            );
            const entry = Number(item.entry_price ?? item.entryPrice ?? 1);
            const exit = Number(item.mark_price ?? item.exitPrice ?? entry);
            const qty = Number(item.quantity ?? 0);
            const rawNotional = item.notional_usdt ?? item.notionalUsdt;
            const stake =
              rawNotional != null
                ? Number(rawNotional)
                : entry * qty > 0
                  ? entry * qty
                  : 10;
            const roi = stake > 0 ? (realized / stake) * 100 : 0;
            const fee = realized > 0 ? realized * 0.05 : 0;
            const net = realized > 0 ? realized - fee : 0;
            return {
              id: String(item.id || `tr-${Math.random()}`),
              symbol: String(item.symbol || "BTC/USDT"),
              strategy: String(item.strategy || "DYNAMIC_RANGE_ACCUMULATOR"),
              side: (item.side || "BUY").toUpperCase() as "BUY" | "SELL",
              entryPrice: entry,
              exitPrice: exit,
              quantity: qty,
              stakeUsdt: stake > 0 ? stake : 10,
              realizedPnlUsdt: realized,
              roiPct: roi,
              status: realized >= 0 ? "WIN" : "LOSS",
              feeUsdt: fee,
              reinvestUsdt: net * 0.7,
              vaultUsdt: net * 0.3,
              exchange: "BINANCE",
              closedAt: item.created_at || new Date().toISOString(),
              duration: "15m",
              riskProfile: "Moderate",
              winScore: realized >= 0 ? "5/5" : "3/5",
            };
          });
        }
      }
    } catch {
      // silent fallback
    }
    return null;
  }

  public static async triggerChatCommand(cmd: string): Promise<string> {
    if (!this.host) {
      return `Private Node Gateway belum terkonfigurasi. Hubungkan gateway Anda di header dashboard.`;
    }
    const cleanUrl = this.host.endsWith("/")
      ? this.host.slice(0, -1)
      : this.host;
    try {
      const res = await fetch(`${cleanUrl}/api/telegram/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd }),
      });
      if (res.ok) {
        const json = await res.json();
        return (
          json.response || json.message || "Command executed successfully."
        );
      }
      return `Error executing command: HTTP ${res.status}`;
    } catch (e: any) {
      return `Gagal menghubungi node: ${e.message}`;
    }
  }
}
