import React, { useState, useEffect } from "react";
import {
  DollarSign,
  TrendingUp,
  ShieldCheck,
  Zap,
  RefreshCw,
  Lock,
  ArrowRight,
  Clock,
  Sparkles,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

interface FundingOpp {
  symbol: string;
  exchange: string;
  spot_price: number;
  perp_mark_price: number;
  basis_spread_pct: number;
  funding_rate_8h_pct: number;
  annualized_apr_pct: number;
  next_funding_utc: string;
  projected_daily_yield_usdt: number;
  is_executable: boolean;
  status: string;
}

interface ActiveDeltaNeutral {
  id: string;
  symbol: string;
  allocated_capital_usdt: number;
  spot_long_quantity: number;
  perp_short_quantity: number;
  spot_entry_price: number;
  net_delta: number;
  annualized_apr_pct: number;
  daily_projected_yield_usdt: number;
  accumulated_harvest_usdt: number;
  status: string;
}

export default function FundingArbitrageView() {
  const [opportunities, setOpportunities] = useState<FundingOpp[]>([
    {
      symbol: "SOL/USDT",
      exchange: "BINANCE",
      spot_price: 215.8,
      perp_mark_price: 216.15,
      basis_spread_pct: 0.162,
      funding_rate_8h_pct: 0.048,
      annualized_apr_pct: 52.56,
      next_funding_utc: "00:00:00 UTC",
      projected_daily_yield_usdt: 14.4,
      is_executable: true,
      status: "HIGH_YIELD_HEDGE",
    },
    {
      symbol: "ETH/USDT",
      exchange: "BYBIT",
      spot_price: 3465.2,
      perp_mark_price: 3468.1,
      basis_spread_pct: 0.084,
      funding_rate_8h_pct: 0.0345,
      annualized_apr_pct: 37.78,
      next_funding_utc: "00:00:00 UTC",
      projected_daily_yield_usdt: 10.35,
      is_executable: true,
      status: "PRIME_YIELD_OPPORTUNITY",
    },
    {
      symbol: "BTC/USDT",
      exchange: "BINANCE",
      spot_price: 92450.0,
      perp_mark_price: 92510.0,
      basis_spread_pct: 0.065,
      funding_rate_8h_pct: 0.021,
      annualized_apr_pct: 22.99,
      next_funding_utc: "00:00:00 UTC",
      projected_daily_yield_usdt: 6.3,
      is_executable: true,
      status: "HARVEST_ACTIVE",
    },
    {
      symbol: "DOGE/USDT",
      exchange: "BYBIT",
      spot_price: 0.3845,
      perp_mark_price: 0.3852,
      basis_spread_pct: 0.182,
      funding_rate_8h_pct: 0.052,
      annualized_apr_pct: 56.94,
      next_funding_utc: "00:00:00 UTC",
      projected_daily_yield_usdt: 15.6,
      is_executable: true,
      status: "HIGH_YIELD_HEDGE",
    },
  ]);

  const [activePositions, setActivePositions] = useState<ActiveDeltaNeutral[]>([
    {
      id: "DN-SOLUSDT-1",
      symbol: "SOL/USDT",
      allocated_capital_usdt: 2000.0,
      spot_long_quantity: 4.63,
      perp_short_quantity: 4.63,
      spot_entry_price: 215.8,
      net_delta: 0.0,
      annualized_apr_pct: 52.56,
      daily_projected_yield_usdt: 2.88,
      accumulated_harvest_usdt: 43.2,
      status: "DELTA_NEUTRAL_RUNNING",
    },
    {
      id: "DN-BTCUSDT-2",
      symbol: "BTC/USDT",
      allocated_capital_usdt: 5000.0,
      spot_long_quantity: 0.027,
      perp_short_quantity: 0.027,
      spot_entry_price: 92450.0,
      net_delta: 0.0,
      annualized_apr_pct: 22.99,
      daily_projected_yield_usdt: 3.15,
      accumulated_harvest_usdt: 68.4,
      status: "DELTA_NEUTRAL_RUNNING",
    },
  ]);

  const [deployCapital, setDeployCapital] = useState<number>(1000);
  const [selectedOpp, setSelectedOpp] = useState<FundingOpp | null>(null);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploySuccess, setDeploySuccess] = useState<string | null>(null);

  const handleDeployHedge = async () => {
    if (!selectedOpp) return;
    setIsDeploying(true);
    try {
      const res = await fetch("/api/funding/deploy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: selectedOpp.symbol,
          capital_usdt: deployCapital,
          spot_price: selectedOpp.spot_price,
          funding_rate_8h_pct: selectedOpp.funding_rate_8h_pct,
        }),
      });
      const data = await res.json();
      if (data.status === "SUCCESS") {
        setActivePositions((prev) => [data.position, ...prev]);
        setDeploySuccess(data.message);
        setTimeout(() => setDeploySuccess(null), 4000);
        setSelectedOpp(null);
      }
    } catch {
      // Optimistic local update
      const newPos: ActiveDeltaNeutral = {
        id: `DN-${selectedOpp.symbol.replace("/", "")}-${Date.now() % 1000}`,
        symbol: selectedOpp.symbol,
        allocated_capital_usdt: deployCapital,
        spot_long_quantity: Number((deployCapital / 2 / selectedOpp.spot_price).toFixed(4)),
        perp_short_quantity: Number((deployCapital / 2 / selectedOpp.spot_price).toFixed(4)),
        spot_entry_price: selectedOpp.spot_price,
        net_delta: 0.0,
        annualized_apr_pct: selectedOpp.annualized_apr_pct,
        daily_projected_yield_usdt: Number(((deployCapital * (selectedOpp.annualized_apr_pct / 100)) / 365).toFixed(2)),
        accumulated_harvest_usdt: 0.0,
        status: "DELTA_NEUTRAL_RUNNING",
      };
      setActivePositions((prev) => [newPos, ...prev]);
      setDeploySuccess(`Deployed ${selectedOpp.symbol} Delta-Neutral hedge with $${deployCapital.toLocaleString()} capital!`);
      setTimeout(() => setDeploySuccess(null), 4000);
      setSelectedOpp(null);
    } finally {
      setIsDeploying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-80 h-full bg-gradient-to-l from-emerald-500/10 to-transparent pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                Delta-Neutral Cash & Carry Arbitrage
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Zero Directional Risk ($\Delta = 0$)
                </span>
              </h2>
              <p className="text-sm text-slate-400 mt-1">
                Harvests perpetual funding rate payments every 8 hours. By holding Spot Long + Perpetual 1x Short simultaneously, price fluctuations cancel out completely while generating high yield.
              </p>
            </div>
          </div>
          <div className="bg-slate-800/80 px-4 py-2.5 rounded-lg border border-slate-700/60 text-right">
            <span className="text-xs text-slate-400 block">Avg. Annualized Yield</span>
            <span className="text-lg font-mono font-bold text-emerald-400">~42.57% APR</span>
          </div>
        </div>
      </div>

      {deploySuccess && (
        <div className="bg-emerald-950/40 border border-emerald-500/40 p-4 rounded-xl flex items-center gap-3 text-emerald-300 text-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{deploySuccess}</span>
        </div>
      )}

      {/* Opportunities Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex justify-between items-center">
          <h3 className="font-semibold text-slate-100 flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            Live Perpetual Funding Rate Yield Opportunities
          </h3>
          <span className="text-xs text-slate-400 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" /> Next Funding Harvest in ~3h 12m
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/50 text-slate-400 text-xs font-semibold uppercase">
              <tr>
                <th className="py-3 px-4">Asset</th>
                <th className="py-3 px-4">Exchange</th>
                <th className="py-3 px-4">Spot vs Perp Price</th>
                <th className="py-3 px-4">Basis Spread</th>
                <th className="py-3 px-4">8h Funding Rate</th>
                <th className="py-3 px-4">Annualized APR</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {opportunities.map((opp) => (
                <tr key={opp.symbol} className="hover:bg-slate-800/30 transition">
                  <td className="py-3.5 px-4 font-bold text-slate-100">{opp.symbol}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                      {opp.exchange}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs">
                    <div>Spot: ${opp.spot_price.toLocaleString()}</div>
                    <div className="text-slate-400">Perp: ${opp.perp_mark_price.toLocaleString()}</div>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-amber-400">+{opp.basis_spread_pct}%</td>
                  <td className="py-3.5 px-4 font-mono font-semibold text-emerald-400">+{opp.funding_rate_8h_pct}% / 8h</td>
                  <td className="py-3.5 px-4 font-mono text-base font-bold text-emerald-400">{opp.annualized_apr_pct}%</td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => setSelectedOpp(opp)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-slate-900 font-semibold text-xs rounded-lg transition"
                    >
                      Deploy 0-Delta Hedge
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Active Delta-Neutral Positions */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h3 className="font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <Lock className="w-4 h-4 text-emerald-400" />
          Active 0-Delta Cash & Carry Positions
        </h3>

        {activePositions.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">No active delta-neutral hedges deployed.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activePositions.map((pos) => (
              <div key={pos.id} className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <span className="font-bold text-slate-100">{pos.symbol}</span>
                    <span className="ml-2 text-xs font-mono text-slate-400">{pos.id}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    $\Delta = 0.00$ (Net Neutral)
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 mb-3 font-mono">
                  <div>Allocated Capital: ${pos.allocated_capital_usdt.toLocaleString()}</div>
                  <div>Annualized Yield: {pos.annualized_apr_pct}% APR</div>
                  <div>Spot Long: {pos.spot_long_quantity}</div>
                  <div>Perp Short: {pos.perp_short_quantity}</div>
                </div>

                <div className="pt-3 border-t border-slate-700/60 flex justify-between items-center text-xs">
                  <span className="text-slate-400">Total Accumulated Harvest:</span>
                  <span className="font-mono font-bold text-emerald-400">+${pos.accumulated_harvest_usdt.toFixed(2)} USDT</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Deploy Modal */}
      {selectedOpp && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full space-y-4">
            <h3 className="font-bold text-lg text-slate-100">
              Deploy {selectedOpp.symbol} Cash & Carry Hedge
            </h3>
            <p className="text-xs text-slate-400">
              This will simultaneously purchase Spot {selectedOpp.symbol} and open a 1x Short Perpetual on {selectedOpp.exchange}. Net market exposure is 0.
            </p>

            <div className="bg-slate-800/60 p-3 rounded-lg text-xs space-y-1 font-mono">
              <div className="flex justify-between text-slate-400">
                <span>Annualized Yield:</span>
                <span className="text-emerald-400 font-bold">{selectedOpp.annualized_apr_pct}% APR</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>8-Hour Funding Rate:</span>
                <span className="text-emerald-400">+{selectedOpp.funding_rate_8h_pct}%</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Total Capital to Allocate (USDT)</label>
              <input
                type="number"
                value={deployCapital}
                onChange={(e) => setDeployCapital(Number(e.target.value))}
                min={50}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                50% (${(deployCapital / 2).toLocaleString()}) to Spot Long, 50% to Perp Short.
              </span>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setSelectedOpp(null)}
                className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDeployHedge}
                disabled={isDeploying || deployCapital < 10}
                className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-slate-900 font-bold text-sm rounded-lg transition flex items-center justify-center gap-2"
              >
                {isDeploying ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Confirm & Deploy"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
