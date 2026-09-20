import React, { useState, useMemo } from "react";
import {
  Search,
  Filter,
  Download,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  XCircle,
  FileSpreadsheet,
  FileText,
  Clock,
  Zap,
  TrendingUp,
  Percent,
} from "lucide-react";
import { HistoricalTrade, PnLCardConfig } from "../types";

interface TradeHistoryViewProps {
  trades: HistoricalTrade[];
  onOpenCardGenerator: (config: PnLCardConfig) => void;
}

export const TradeHistoryView: React.FC<TradeHistoryViewProps> = ({
  trades,
  onOpenCardGenerator,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterResult, setFilterResult] = useState<"ALL" | "WIN" | "LOSS">("ALL");
  const [filterStrategy, setFilterStrategy] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<"time" | "pnl" | "roi">("time");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  // Strategy list for dropdown
  const strategies = useMemo(() => {
    const list = Array.from(new Set(trades.map((t) => t.strategy)));
    return ["ALL", ...list];
  }, [trades]);

  // Filtered and sorted trades
  const filteredTrades = useMemo(() => {
    return trades
      .filter((trade) => {
        const matchesQuery =
          trade.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
          trade.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          trade.strategy.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesResult = filterResult === "ALL" || trade.status === filterResult;
        const matchesStrategy = filterStrategy === "ALL" || trade.strategy === filterStrategy;
        return matchesQuery && matchesResult && matchesStrategy;
      })
      .sort((a, b) => {
        let diff = 0;
        if (sortBy === "time") {
          diff = new Date(b.closedAt).getTime() - new Date(a.closedAt).getTime();
        } else if (sortBy === "pnl") {
          diff = b.realizedPnlUsdt - a.realizedPnlUsdt;
        } else if (sortBy === "roi") {
          diff = b.roiPct - a.roiPct;
        }
        return sortOrder === "desc" ? diff : -diff;
      });
  }, [trades, searchQuery, filterResult, filterStrategy, sortBy, sortOrder]);

  // Overall Stats
  const totalTrades = trades.length;
  const winTrades = trades.filter((t) => t.status === "WIN").length;
  const winRate = totalTrades > 0 ? ((winTrades / totalTrades) * 100).toFixed(1) : "0.0";
  const totalRealizedPnl = trades.reduce((acc, t) => acc + t.realizedPnlUsdt, 0);
  const bestTrade = trades.reduce(
    (max, t) => (t.roiPct > (max?.roiPct || -Infinity) ? t : max),
    trades[0]
  );

  // Generate Card from this trade
  const handleGenerateCard = (trade: HistoricalTrade) => {
    const config: PnLCardConfig = {
      symbol: trade.symbol,
      roiPct: trade.roiPct,
      profitUsdt: trade.realizedPnlUsdt,
      stakeUsdt: trade.stakeUsdt,
      duration: trade.duration,
      riskProfile: trade.riskProfile,
      winScore: trade.winScore,
      botHandle: "@MoneyForHoneyBot",
      referralLink: `https://t.me/MoneyForHoneyBot?start=ref_${trade.symbol.replace(/[^a-zA-Z0-9]/g, "")}`,
      theme: "golden_wave_surfer",
      aspectRatio: "16:9",
      showQrCode: true,
    };
    onOpenCardGenerator(config);
  };

  // Export to CSV
  const handleExportCsv = () => {
    const headers = [
      "Trade ID",
      "Symbol",
      "Strategy",
      "Side",
      "Entry Price",
      "Exit Price",
      "Stake USDT",
      "Realized PnL USDT",
      "ROI %",
      "Duration",
      "Status",
      "Fee (5%)",
      "Reinvest (70%)",
      "Vault (30%)",
      "Closed At",
    ];

    const rows = filteredTrades.map((t) => [
      t.id,
      t.symbol,
      t.strategy,
      t.side,
      t.entryPrice,
      t.exitPrice,
      t.stakeUsdt,
      t.realizedPnlUsdt,
      `${t.roiPct}%`,
      t.duration,
      t.status,
      t.feeUsdt,
      t.reinvestUsdt,
      t.vaultUsdt,
      t.closedAt,
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `MONEY_FOR_HONEY_TRADE_HISTORY_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Export to JSON
  const handleExportJson = () => {
    const dataStr =
      "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(filteredTrades, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute(
      "download",
      `MONEY_FOR_HONEY_TRADE_HISTORY_${new Date().toISOString().slice(0, 10)}.json`
    );
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="space-y-6">
      {/* Summary KPI Header */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="uppercase font-semibold">Total Closed Trades</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="font-mono text-2xl font-bold text-white tracking-tight">
            {totalTrades} Trades
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400">
            <span className="text-emerald-400 font-bold">{winTrades} Wins</span> ·{" "}
            <span className="text-rose-400">{totalTrades - winTrades} Losses</span>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="uppercase font-semibold">Win Rate (Realized)</span>
            <Percent className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="font-mono text-2xl font-bold text-emerald-400 tracking-tight">
            {winRate}%
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400">
            Scale-Agnostic 1.5% Risk Sizing
          </div>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="uppercase font-semibold">Cumulative Realized PnL</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="font-mono text-2xl font-bold text-emerald-400 tracking-tight">
            +${totalRealizedPnl.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400">
            Waterfall: 70% Reinvest / 30% Vault
          </div>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="uppercase font-semibold">Top Harvest Trade</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          {bestTrade ? (
            <div>
              <div className="font-mono text-2xl font-bold text-amber-300 tracking-tight flex items-baseline gap-2">
                +{bestTrade.roiPct}%
                <span className="text-xs text-emerald-400 font-normal">
                  (+${bestTrade.realizedPnlUsdt.toFixed(2)})
                </span>
              </div>
              <div className="mt-2 text-[11px] font-mono text-slate-400">
                {bestTrade.symbol} · {bestTrade.duration}
              </div>
            </div>
          ) : (
            <div className="text-slate-500 font-mono text-sm">No trades yet</div>
          )}
        </div>
      </div>

      {/* Filter and Control Bar */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search by Symbol (e.g. BTC, JOD/CNY), Trade ID, Strategy..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3.5 py-2 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-400"
          />
        </div>

        {/* Win/Loss Toggle */}
        <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-mono">
          {(["ALL", "WIN", "LOSS"] as const).map((r) => (
            <button
              key={r}
              onClick={() => setFilterResult(r)}
              className={`px-3 py-1.5 rounded transition-colors ${
                filterResult === r
                  ? "bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {r === "ALL" ? "All Results" : r === "WIN" ? "Wins Only" : "Losses Only"}
            </button>
          ))}
        </div>

        {/* Strategy Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-500">Strategy:</span>
          <select
            value={filterStrategy}
            onChange={(e) => setFilterStrategy(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-xs font-mono text-slate-300 focus:border-amber-400 focus:outline-none"
          >
            {strategies.map((st) => (
              <option key={st} value={st}>
                {st.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCsv}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 text-xs font-mono text-slate-300 hover:text-white transition-colors"
            title="Download CSV report"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={handleExportJson}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 text-xs font-mono text-slate-300 hover:text-white transition-colors"
            title="Export raw JSON"
          >
            <FileText className="w-3.5 h-3.5 text-sky-400" />
            <span>JSON</span>
          </button>
        </div>
      </div>

      {/* Trades Data Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/90 shadow-sm">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/70 text-slate-400 uppercase tracking-wider">
              <th className="p-4">Trade ID / Time</th>
              <th className="p-4">Symbol & Exchange</th>
              <th className="p-4">Strategy & Side</th>
              <th className="p-4">Entry / Exit Price</th>
              <th className="p-4">Stake & Duration</th>
              <th className="p-4">Realized Profit (PnL)</th>
              <th className="p-4">Waterfall Allocation</th>
              <th className="p-4 text-right">Viral Brag</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredTrades.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-slate-500 font-mono">
                  No trade history matched your filter criteria.
                </td>
              </tr>
            ) : (
              filteredTrades.map((trade) => {
                const isWin = trade.status === "WIN";
                return (
                  <tr key={trade.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-4">
                      <div className="font-bold text-white flex items-center gap-1.5">
                        {isWin ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                        )}
                        <span>{trade.id}</span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{trade.closedAt}</div>
                    </td>

                    <td className="p-4">
                      <div className="font-bold text-slate-200 text-sm">{trade.symbol}</div>
                      <div className="text-[11px] text-amber-400/80">{trade.exchange}</div>
                    </td>

                    <td className="p-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-amber-300 border border-slate-700 mb-1">
                        {trade.strategy.replace(/_/g, " ")}
                      </span>
                      <div className="text-slate-400 text-[11px]">
                        <span className={trade.side === "BUY" ? "text-emerald-400" : "text-amber-400"}>
                          {trade.side}
                        </span>{" "}
                        · {trade.riskProfile}
                      </div>
                    </td>

                    <td className="p-4">
                      <div className="text-slate-300">
                        In: ${trade.entryPrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-slate-400">
                        Out: ${trade.exitPrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </div>
                    </td>

                    <td className="p-4">
                      <div className="font-bold text-slate-200">${trade.stakeUsdt} USDT</div>
                      <div className="text-[11px] text-slate-500">{trade.duration}</div>
                    </td>

                    <td className="p-4">
                      <div
                        className={`font-bold text-sm ${
                          isWin ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {isWin ? "+" : ""}${trade.realizedPnlUsdt.toFixed(2)}
                      </div>
                      <div
                        className={`text-xs font-bold ${
                          isWin ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {isWin ? "+" : ""}
                        {trade.roiPct}%
                      </div>
                    </td>

                    <td className="p-4 text-[11px] text-slate-400">
                      {isWin ? (
                        <div className="space-y-0.5">
                          <div>
                            Fee (5%): <span className="text-slate-300">${trade.feeUsdt.toFixed(2)}</span>
                          </div>
                          <div>
                            Reinvest (70%):{" "}
                            <span className="text-emerald-400 font-semibold">
                              ${trade.reinvestUsdt.toFixed(2)}
                            </span>
                          </div>
                          <div>
                            Vault (30%):{" "}
                            <span className="text-amber-400 font-semibold">
                              ${trade.vaultUsdt.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-600">No Waterfall (Loss)</span>
                      )}
                    </td>

                    <td className="p-4 text-right">
                      <button
                        onClick={() => handleGenerateCard(trade)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 hover:border-amber-400 font-bold transition-all shadow-xs group"
                        title="Generate Viral PnL Card like screenshot"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-amber-400 group-hover:rotate-12 transition-transform" />
                        <span>PnL Card</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TradeHistoryView;
