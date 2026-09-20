import React, { useState } from "react";
import {
  TrendingUp,
  Vault,
  PieChart,
  BarChart3,
  DollarSign,
  ShieldCheck,
  Percent,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  Download,
  Calendar,
  Zap,
} from "lucide-react";
import { HistoricalTrade, PnLLedgerEntry, VaultData } from "../types";

interface PnLHistoryViewProps {
  trades: HistoricalTrade[];
  ledger: PnLLedgerEntry[];
  vaultData: VaultData;
  totalEquity: number;
  onOpenCardGenerator: () => void;
}

export const PnLHistoryView: React.FC<PnLHistoryViewProps> = ({
  trades,
  ledger,
  vaultData,
  totalEquity,
  onOpenCardGenerator,
}) => {
  const [timeframe, setTimeframe] = useState<"7D" | "30D" | "ALL">("30D");

  // Quant Calculations
  const winningTrades = trades.filter((t) => t.status === "WIN");
  const losingTrades = trades.filter((t) => t.status === "LOSS");

  const grossProfit = winningTrades.reduce((acc, t) => acc + t.realizedPnlUsdt, 0);
  const grossLoss = Math.abs(losingTrades.reduce((acc, t) => acc + t.realizedPnlUsdt, 0));
  const netRealizedProfit = grossProfit - grossLoss;

  const profitFactor = grossLoss > 0 ? (grossProfit / grossLoss).toFixed(2) : "∞";
  const avgWin = winningTrades.length > 0 ? (grossProfit / winningTrades.length).toFixed(2) : "0.00";
  const avgLoss = losingTrades.length > 0 ? (grossLoss / losingTrades.length).toFixed(2) : "0.00";
  const winRate = trades.length > 0 ? ((winningTrades.length / trades.length) * 100).toFixed(1) : "0.0";

  // Strategy PnL Distribution
  const strategyStats = trades.reduce((acc, t) => {
    if (!acc[t.strategy]) {
      acc[t.strategy] = { count: 0, profit: 0, wins: 0 };
    }
    acc[t.strategy].count += 1;
    acc[t.strategy].profit += t.realizedPnlUsdt;
    if (t.status === "WIN") acc[t.strategy].wins += 1;
    return acc;
  }, {} as Record<string, { count: number; profit: number; wins: number }>);

  return (
    <div className="space-y-6">
      {/* Top Level Quant KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Net Realized PnL */}
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span className="uppercase font-semibold tracking-wider">Net Realized PnL</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="font-mono text-2xl lg:text-3xl font-bold text-emerald-400 tracking-tight">
            +${netRealizedProfit.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
          <div className="mt-2.5 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Gross: +${grossProfit.toFixed(0)}</span>
            <span className="text-rose-400">Loss: -${grossLoss.toFixed(0)}</span>
          </div>
        </div>

        {/* Profit Factor & Sharpe */}
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span className="uppercase font-semibold tracking-wider">Profit Factor & Sharpe</span>
            <BarChart3 className="w-4 h-4 text-amber-400" />
          </div>
          <div className="font-mono text-2xl lg:text-3xl font-bold text-amber-300 tracking-tight flex items-baseline gap-2">
            {profitFactor}
            <span className="text-xs font-semibold text-slate-400">Factor</span>
          </div>
          <div className="mt-2.5 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Sharpe Ratio: <strong className="text-emerald-400">2.84</strong></span>
            <span>Sortino: <strong className="text-emerald-400">3.41</strong></span>
          </div>
        </div>

        {/* Win/Loss Metrics */}
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span className="uppercase font-semibold tracking-wider">Avg Win / Avg Loss</span>
            <Percent className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="font-mono text-2xl lg:text-3xl font-bold text-white tracking-tight flex items-baseline gap-2">
            <span className="text-emerald-400">+${avgWin}</span>
            <span className="text-slate-600 text-lg">/</span>
            <span className="text-rose-400 text-lg">-${avgLoss}</span>
          </div>
          <div className="mt-2.5 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Win Rate: <strong className="text-emerald-400">{winRate}%</strong></span>
            <span>Payoff Ratio: <strong>{(parseFloat(avgWin) / (parseFloat(avgLoss) || 1)).toFixed(2)}</strong></span>
          </div>
        </div>

        {/* Auto-Vault Compounding Total */}
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span className="uppercase font-semibold tracking-wider">Compounded to Vault (30%)</span>
            <Vault className="w-4 h-4 text-amber-400" />
          </div>
          <div className="font-mono text-2xl lg:text-3xl font-bold text-amber-400 tracking-tight">
            ${vaultData.totalVaultEquity.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
          <div className="mt-2.5 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Flex: ${vaultData.flexibleStaked.toFixed(0)}</span>
            <span>Locked: ${vaultData.lockedStaked.toFixed(0)}</span>
          </div>
        </div>
      </div>

      {/* Waterfall Mechanism Explained Banner */}
      <div className="p-5 rounded-xl bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/30 border border-amber-500/20 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white font-mono">
              Autonomous Profit Waterfall & Wealth Compounding Engine
            </h3>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Every winning trade automatically executes: <strong>5% Platform Fee</strong> ➔{" "}
              <strong>70% Trading Equity Reinvestment</strong> ➔ <strong>30% Binance Simple Earn Lockup</strong>
            </p>
          </div>
        </div>

        <button
          onClick={onOpenCardGenerator}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono text-xs font-bold transition-all shadow-md shadow-amber-500/20"
        >
          <Sparkles className="w-4 h-4" />
          <span>Launch PnL Card Studio</span>
        </button>
      </div>

      {/* Strategy Efficiency Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <PieChart className="w-4 h-4 text-amber-400" />
              Strategy Net Realized Returns
            </h3>
            <span className="text-xs font-mono text-slate-400">Automated Regime Switching</span>
          </div>

          <div className="space-y-3">
            {(Object.entries(strategyStats) as [string, { count: number; profit: number; wins: number }][]).map(([strategyName, stats]) => {
              const strategyWinRate = ((stats.wins / stats.count) * 100).toFixed(0);
              const allStats = Object.values(strategyStats) as { count: number; profit: number; wins: number }[];
              const maxProfit = Math.max(...allStats.map((s) => s.profit), 1000);
              const pctWidth = Math.min(100, Math.max(10, (stats.profit / maxProfit) * 100));

              return (
                <div key={strategyName} className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="font-bold text-slate-200">{strategyName.replace(/_/g, " ")}</span>
                    <span className="font-bold text-emerald-400">+${stats.profit.toFixed(2)} USDT</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-emerald-400 rounded-full transition-all duration-500"
                      style={{ width: `${pctWidth}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                    <span>{stats.count} executions</span>
                    <span>Win Rate: <strong className="text-slate-300">{strategyWinRate}%</strong></span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk & Safety Limits */}
        <div className="p-6 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Capital Preservation Bounds
          </h3>

          <div className="space-y-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-slate-400 mb-1">Max Trade Risk Budget:</div>
              <div className="text-emerald-400 font-bold text-sm">1.50% of Portfolio Equity</div>
              <div className="text-[10px] text-slate-500 mt-1">
                Strict stop distance sizing: Qty = (Equity × 1.5%) / |Entry - SL|
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-slate-400 mb-1">Daily Drawdown Breaker Limit:</div>
              <div className="text-amber-400 font-bold text-sm">5.00% Circuit Breaker</div>
              <div className="text-[10px] text-slate-500 mt-1">
                Halts all order routing and auto-notifies via WhatsApp Cloud API
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-slate-400 mb-1">Max Position Allocation Cap:</div>
              <div className="text-slate-200 font-bold text-sm">30.00% Single Asset Ceiling</div>
              <div className="text-[10px] text-slate-500 mt-1">
                Prevents over-concentration in any individual asset
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Profit & Loss Waterfall Ledger */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2 font-mono">
            <TrendingUp className="w-4 h-4 text-amber-400" />
            Historical Profit & Loss Waterfall Ledger ({ledger.length} events)
          </h3>
          <span className="text-xs font-mono text-slate-400">Deduction & Allocation Log</span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/90 shadow-sm">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/70 text-slate-400 uppercase tracking-wider">
                <th className="p-4">Ledger ID / Time</th>
                <th className="p-4">Origin Trade</th>
                <th className="p-4">Gross Realized</th>
                <th className="p-4">5% Maint Fee</th>
                <th className="p-4">70% Reinvested</th>
                <th className="p-4">30% Vault Reserve</th>
                <th className="p-4 text-right">Trading Balance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {ledger.map((entry) => (
                <tr key={entry.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-4">
                    <div className="font-bold text-white">{entry.id}</div>
                    <div className="text-[11px] text-slate-500">{entry.timestamp}</div>
                  </td>

                  <td className="p-4">
                    <span className="font-bold text-amber-400">{entry.symbol}</span>
                    <div className="text-[11px] text-slate-500">{entry.tradeId}</div>
                  </td>

                  <td className="p-4 font-bold text-emerald-400 text-sm">
                    +${entry.grossProfitUsdt.toFixed(2)}
                  </td>

                  <td className="p-4 text-rose-400">
                    -${entry.feeDeductedUsdt.toFixed(2)}
                  </td>

                  <td className="p-4 font-bold text-emerald-400">
                    +${entry.reinvestAllocUsdt.toFixed(2)}
                  </td>

                  <td className="p-4 font-bold text-amber-400">
                    +${entry.vaultReserveAllocUsdt.toFixed(2)}
                  </td>

                  <td className="p-4 text-right">
                    <div className="font-bold text-slate-200">
                      ${entry.balanceAfterUsdt.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </div>
                    <div className="text-[10px] text-slate-500">
                      Vault: ${entry.vaultAfterUsdt.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PnLHistoryView;
