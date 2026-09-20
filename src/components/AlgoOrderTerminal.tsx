import React, { useState } from "react";
import {
  Send,
  ShieldCheck,
  AlertTriangle,
  Zap,
  TrendingUp,
  Percent,
  DollarSign,
  Lock,
  RefreshCw,
  Sliders,
  CheckCircle2,
  Cpu,
} from "lucide-react";
import { ActiveTrade } from "../types";
import { LiveTicker } from "../services/marketData";

interface AlgoOrderTerminalProps {
  totalEquity: number;
  livePrices: Record<string, LiveTicker>;
  circuitBreakerActive: boolean;
  onExecuteOrder: (trade: ActiveTrade) => void;
}

export const AlgoOrderTerminal: React.FC<AlgoOrderTerminalProps> = ({
  totalEquity,
  livePrices,
  circuitBreakerActive,
  onExecuteOrder,
}) => {
  const [symbol, setSymbol] = useState<string>("BTC/USDT");
  const [strategy, setStrategy] = useState<string>("DYNAMIC_BREAKOUT_MOMENTUM");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [stakeUsdt, setStakeUsdt] = useState<number>(200);
  const [leverage, setLeverage] = useState<number>(5);
  const [stopLossPct, setStopLossPct] = useState<number>(1.5);
  const [takeProfitPct, setTakeProfitPct] = useState<number>(4.5);
  const [orderType, setOrderType] = useState<"MARKET" | "ALGO_TRIGGER">("ALGO_TRIGGER");

  const currentPrice = livePrices[symbol]?.price || 90000;
  const notional = stakeUsdt * leverage;
  const quantity = parseFloat((notional / currentPrice).toFixed(6));

  // Risk Math
  const riskAmountUsdt = parseFloat(((notional * stopLossPct) / 100).toFixed(2));
  const maxRiskBudget = parseFloat((totalEquity * 0.015).toFixed(2)); // 1.5% Cap
  const maxNotionalCap = parseFloat((totalEquity * 0.3).toFixed(2)); // 30% Equity Cap
  const targetProfitUsdt = parseFloat(((notional * takeProfitPct) / 100).toFixed(2));
  const riskRewardRatio = (takeProfitPct / stopLossPct).toFixed(2);

  const isRiskCompliant = riskAmountUsdt <= maxRiskBudget;
  const isNotionalCompliant = notional <= maxNotionalCap;
  const isValid =
    isRiskCompliant &&
    isNotionalCompliant &&
    stakeUsdt >= 10 &&
    !circuitBreakerActive;

  const stopLossPrice =
    side === "BUY"
      ? parseFloat((currentPrice * (1 - stopLossPct / 100)).toFixed(2))
      : parseFloat((currentPrice * (1 + stopLossPct / 100)).toFixed(2));

  const takeProfitPrice =
    side === "BUY"
      ? parseFloat((currentPrice * (1 + takeProfitPct / 100)).toFixed(2))
      : parseFloat((currentPrice * (1 - takeProfitPct / 100)).toFixed(2));

  const handleLaunch = () => {
    if (!isValid) return;

    const newTrade: ActiveTrade = {
      id: `TRD-${Math.floor(10000 + Math.random() * 90000)}`,
      symbol,
      strategy,
      side,
      entryPrice: currentPrice,
      markPrice: currentPrice,
      stopLoss: stopLossPrice,
      takeProfit: takeProfitPrice,
      quantity,
      notionalUsdt: notional,
      allocatedRiskUsdt: riskAmountUsdt,
      unrealizedPnlUsdt: 0.0,
      unrealizedPnlPct: 0.0,
      duration: "1m 0s",
      leverage: `${leverage}x`,
      trailingStopActive: true,
    };

    onExecuteOrder(newTrade);
  };

  return (
    <div className="space-y-6">
      {/* Terminal Title Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/30 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Cpu className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white font-mono flex items-center gap-2">
              Algorithmic Execution Terminal
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                LIVE ENGINE
              </span>
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Precision quantitative order entry with automated 1.5% capital protection and Kelly position sizing
            </p>
          </div>
        </div>

        {/* Live Market Price Pill */}
        <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs">
          <span className="text-slate-400">Live {symbol}:</span>
          <span className="text-base font-bold text-emerald-400">
            ${currentPrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </span>
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
              (livePrices[symbol]?.change24h || 0) >= 0
                ? "bg-emerald-500/20 text-emerald-400"
                : "bg-rose-500/20 text-rose-400"
            }`}
          >
            {(livePrices[symbol]?.change24h || 0) >= 0 ? "+" : ""}
            {livePrices[symbol]?.change24h || 0}%
          </span>
        </div>
      </div>

      {/* Main Terminal Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Parameters (7 cols) */}
        <div className="lg:col-span-7 p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-5 font-mono text-xs">
          {/* Pair & Side Selector */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-slate-400 block mb-1 font-semibold uppercase">Trading Pair</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-bold focus:border-amber-400 outline-none"
              >
                {Object.keys(livePrices).map((p) => (
                  <option key={p} value={p}>
                    {p} (${livePrices[p].price.toLocaleString()})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-slate-400 block mb-1 font-semibold uppercase">Execution Direction</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSide("BUY")}
                  className={`py-2.5 rounded-xl font-bold transition-all ${
                    side === "BUY"
                      ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
                      : "bg-slate-950 text-slate-400 border border-slate-800 hover:text-white"
                  }`}
                >
                  BUY (LONG)
                </button>
                <button
                  type="button"
                  onClick={() => setSide("SELL")}
                  className={`py-2.5 rounded-xl font-bold transition-all ${
                    side === "SELL"
                      ? "bg-rose-500 text-white shadow-md shadow-rose-500/20"
                      : "bg-slate-950 text-slate-400 border border-slate-800 hover:text-white"
                  }`}
                >
                  SELL (SHORT)
                </button>
              </div>
            </div>
          </div>

          {/* Strategy & Order Type */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-slate-400 block mb-1 font-semibold uppercase">Algorithmic Strategy</label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-amber-400 font-bold focus:border-amber-400 outline-none"
              >
                <option value="DYNAMIC_BREAKOUT_MOMENTUM">Dynamic Breakout Momentum (ADX &gt; 25)</option>
                <option value="STATISTICAL_MEAN_REVERSION">Statistical Mean-Reversion (ADX &lt; 20)</option>
                <option value="SPATIAL_ARBITRAGE_TRILATERAL">Spatial Arbitrage Trilateral (Net Spread ≥ 0.6%)</option>
                <option value="MICRO_ORDERBOOK_SCALP">Micro Orderbook Imbalance Scalp</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 block mb-1 font-semibold uppercase">Execution Trigger</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setOrderType("ALGO_TRIGGER")}
                  className={`py-2.5 rounded-xl font-bold transition-all ${
                    orderType === "ALGO_TRIGGER"
                      ? "bg-amber-500 text-slate-950 shadow-md"
                      : "bg-slate-950 text-slate-400 border border-slate-800"
                  }`}
                >
                  ⚡ Algo Trigger
                </button>
                <button
                  type="button"
                  onClick={() => setOrderType("MARKET")}
                  className={`py-2.5 rounded-xl font-bold transition-all ${
                    orderType === "MARKET"
                      ? "bg-slate-800 text-white border border-slate-600"
                      : "bg-slate-950 text-slate-400 border border-slate-800"
                  }`}
                >
                  Direct Market
                </button>
              </div>
            </div>
          </div>

          {/* Capital Stake & Leverage */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-slate-400 font-semibold uppercase">Margin Stake ($ USDT)</label>
                <span className="text-[11px] text-slate-500">Min $10.00</span>
              </div>
              <input
                type="number"
                min={10}
                max={5000}
                step={10}
                value={stakeUsdt}
                onChange={(e) => setStakeUsdt(Math.max(10, parseFloat(e.target.value) || 10))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-bold focus:border-amber-400 outline-none text-sm"
              />
              <div className="flex items-center gap-1.5 mt-2">
                {[50, 100, 200, 500].map((amt) => (
                  <button
                    key={amt}
                    type="button"
                    onClick={() => setStakeUsdt(amt)}
                    className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-300 font-bold"
                  >
                    ${amt}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-slate-400 font-semibold uppercase">Leverage Multiplier</label>
                <span className="text-amber-400 font-bold text-sm">{leverage}x</span>
              </div>
              <input
                type="range"
                min={1}
                max={20}
                value={leverage}
                onChange={(e) => setLeverage(parseInt(e.target.value))}
                className="w-full h-2 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-amber-500 my-3"
              />
              <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                <span>1x (Spot)</span>
                <span>5x (Standard)</span>
                <span>10x (Quant)</span>
                <span>20x (Max)</span>
              </div>
            </div>
          </div>

          {/* SL & TP Settings */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
            <div>
              <label className="text-slate-400 block mb-1 font-semibold uppercase">
                Stop Loss (%)
              </label>
              <input
                type="number"
                min={0.5}
                max={10}
                step={0.1}
                value={stopLossPct}
                onChange={(e) => setStopLossPct(parseFloat(e.target.value) || 1.5)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-rose-400 font-bold focus:border-rose-400 outline-none"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                SL Trigger: ${stopLossPrice.toLocaleString()}
              </span>
            </div>

            <div>
              <label className="text-slate-400 block mb-1 font-semibold uppercase">
                Take Profit (%)
              </label>
              <input
                type="number"
                min={1}
                max={50}
                step={0.5}
                value={takeProfitPct}
                onChange={(e) => setTakeProfitPct(parseFloat(e.target.value) || 4.5)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-emerald-400 font-bold focus:border-emerald-400 outline-none"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                TP Target: ${takeProfitPrice.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Right Panel: Pre-Flight Audit & Launch Button (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 font-mono text-xs">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              Pre-Flight Risk Engine Audit
            </h3>

            <div className="space-y-2.5">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                <span className="text-slate-400">Total Notional Value:</span>
                <span className="font-bold text-white text-sm">${notional.toLocaleString()} USDT</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                <span className="text-slate-400">Order Quantity:</span>
                <span className="font-bold text-slate-200">
                  {quantity} {symbol.split("/")[0]}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                <span className="text-slate-400">Implied Capital Risk:</span>
                <span
                  className={`font-bold ${
                    isRiskCompliant ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  ${riskAmountUsdt} / Max ${maxRiskBudget} (1.5% Cap)
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                <span className="text-slate-400">Estimated Profit Target:</span>
                <span className="font-bold text-emerald-400">+${targetProfitUsdt} USDT</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                <span className="text-slate-400">Risk-to-Reward Ratio:</span>
                <span className="font-bold text-amber-300">1 : {riskRewardRatio}</span>
              </div>
            </div>

            {/* Compliance Status Checks */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <div className="flex items-center gap-2 text-[11px]">
                {isRiskCompliant ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                )}
                <span className={isRiskCompliant ? "text-slate-300" : "text-rose-400"}>
                  {isRiskCompliant
                    ? "Risk within 1.5% portfolio limit"
                    : `Risk ($${riskAmountUsdt}) exceeds 1.5% cap ($${maxRiskBudget})`}
                </span>
              </div>

              <div className="flex items-center gap-2 text-[11px]">
                {isNotionalCompliant ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                )}
                <span className={isNotionalCompliant ? "text-slate-300" : "text-rose-400"}>
                  {isNotionalCompliant
                    ? "Notional within 30% max allocation limit"
                    : `Notional exceeds 30% equity cap ($${maxNotionalCap})`}
                </span>
              </div>

              {circuitBreakerActive && (
                <div className="flex items-center gap-2 text-[11px] text-rose-400">
                  <Lock className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>Circuit Breaker Active: Order generation suspended</span>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="button"
              onClick={handleLaunch}
              disabled={!isValid}
              className={`w-full py-3.5 rounded-xl font-bold font-mono text-sm flex items-center justify-center gap-2 transition-all shadow-lg ${
                isValid
                  ? "bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-slate-950 shadow-amber-500/20 active:scale-98 cursor-pointer"
                  : "bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed opacity-60"
              }`}
            >
              <Send className="w-4 h-4" />
              <span>DISPATCH ORDER TO ALGO ENGINE</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlgoOrderTerminal;
