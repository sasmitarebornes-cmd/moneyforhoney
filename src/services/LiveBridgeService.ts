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
      if (res.ok) return await res.json();
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
