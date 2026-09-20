"use client";

import React, { useState, useEffect } from "react";
import Logo from "@/frontend/components/Logo";
import {
  ShieldAlert,
  TrendingUp,
  Vault,
  Zap,
  RefreshCw,
  Sliders,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  Lock,
  Layers,
  Activity,
  Send,
  Bell,
  Cpu,
  Clock,
  DollarSign,
  BarChart3,
  Percent,
} from "lucide-react";

// Dashboard state and data models
interface ActiveTrade {
  id: string;
  symbol: string;
  strategy: string;
  side: "BUY" | "SELL" | "ARBITRAGE";
  entryPrice: number;
  markPrice: number;
  stopLoss: number;
  takeProfit: number;
  quantity: number;
  notionalUsdt: number;
  allocatedRiskUsdt: number;
  unrealizedPnlUsdt: number;
  unrealizedPnlPct: number;
  duration: string;
  leverage: string;
  trailingStopActive: boolean;
}

interface ArbitrageSignal {
  symbol: string;
  buyExchange: string;
  sellExchange: string;
  buyPrice: number;
  sellPrice: number;
  grossSpreadPct: number;
  netSpreadPct: number;
  takerFeePct: number;
  estimatedProfitUsdt: number;
  isExecutable: boolean;
  status: string;
}

interface VaultData {
  totalVaultEquity: number;
  pendingReserve: number;
  flexibleStaked: number;
  lockedStaked: number;
  totalGrossProfitProcessed: number;
  totalMaintenanceFeesDeducted: number;
  totalReinvestedIntoTrading: number;
  estimatedApyPct: number;
  projectedMonthlyInterestUsdt: number;
  lockedTiers: Array<{ tenure: string; amount: number; apy: number; autoRenew: boolean }>;
  flexibleTier: { amount: number; asset: string; apy: number; autoSubscribe: boolean };
}

export default function DashboardPage() {
  // Circuit Breaker State
  const [circuitBreakerActive, setCircuitBreakerActive] = useState<boolean>(false);
  const [circuitBreakerReason, setCircuitBreakerReason] = useState<string | null>(null);
  const [dailyDrawdownPct, setDailyDrawdownPct] = useState<number>(1.84);
  const [maxDrawdownLimitPct] = useState<number>(5.0);

  // Timeframe and Navigation
  const [selectedTimeframe, setSelectedTimeframe] = useState<"1H" | "24H" | "7D" | "30D" | "ALL">("24H");
  const [activeTab, setActiveTab] = useState<"overview" | "trades" | "vault" | "arbitrage" | "regime">("overview");

  // Live Metric Telemetry
  const [totalEquity, setTotalEquity] = useState<number>(24850.25);
  const [todayPnl, setTodayPnl] = useState<number>(845.20);
  const [todayPnlPct, setTodayPnlPct] = useState<number>(3.52);
  const [winRate, setWinRate] = useState<number>(68.4);
  const [adxValue, setAdxValue] = useState<number>(28.6);
  const [atrPct, setAtrPct] = useState<number>(1.95);
  const [marketRegime, setMarketRegime] = useState<"BREAKOUT" | "MEAN_REVERSION" | "TRANSITION">("BREAKOUT");

  // Notifications Log
  const [notificationLogs, setNotificationLogs] = useState<Array<{ id: string; channel: "TELEGRAM" | "WHATSAPP"; message: string; timestamp: string }>>([
    {
      id: "nt-1",
      channel: "TELEGRAM",
      message: "Trade BUY BTC/USDT filled at $91,850.00 | Allocated Risk: $150.00 (1.5%)",
      timestamp: "10 mins ago",
    },
    {
      id: "nt-2",
      channel: "TELEGRAM",
      message: "Profit Waterfall: Gross +$420.00 -> 5% Fee ($21.00), 70% Reinvest ($279.30), 30% Vault ($119.70)",
      timestamp: "32 mins ago",
    },
    {
      id: "nt-3",
      channel: "TELEGRAM",
      message: "Binance Simple Earn Sweep: Subscribed $119.70 to Locked 30-Days @ 9.8% APY",
      timestamp: "32 mins ago",
    },
  ]);

  // Active Trades
  const [activeTrades, setActiveTrades] = useState<ActiveTrade[]>([
    {
      id: "TRD-88219",
      symbol: "BTC/USDT",
      strategy: "DYNAMIC_BREAKOUT_MOMENTUM",
      side: "BUY",
      entryPrice: 91850.00,
      markPrice: 93420.50,
      stopLoss: 90400.00,
      takeProfit: 95475.00,
      quantity: 0.1035,
      notionalUsdt: 9668.02,
      allocatedRiskUsdt: 150.00,
      unrealizedPnlUsdt: 162.51,
      unrealizedPnlPct: 1.71,
      duration: "2h 45m",
      leverage: "1x Spot",
      trailingStopActive: true,
    },
    {
      id: "TRD-88220",
      symbol: "SOL/USDT",
      strategy: "STATISTICAL_MEAN_REVERSION",
      side: "BUY",
      entryPrice: 212.40,
      markPrice: 217.10,
      stopLoss: 208.50,
      takeProfit: 222.15,
      quantity: 12.8,
      notionalUsdt: 2778.88,
      allocatedRiskUsdt: 49.92,
      unrealizedPnlUsdt: 60.16,
      unrealizedPnlPct: 2.21,
      duration: "48m",
      leverage: "1x Spot",
      trailingStopActive: false,
    },
    {
      id: "TRD-88221",
      symbol: "ETH/USDT",
      strategy: "SPATIAL_ARBITRAGE_TRILATERAL",
      side: "ARBITRAGE",
      entryPrice: 3445.10,
      markPrice: 3474.20,
      stopLoss: 3420.00,
      takeProfit: 3495.00,
      quantity: 0.85,
      notionalUsdt: 2953.07,
      allocatedRiskUsdt: 21.33,
      unrealizedPnlUsdt: 24.73,
      unrealizedPnlPct: 0.84,
      duration: "14m",
      leverage: "Cross-Exch",
      trailingStopActive: false,
    },
  ]);

  // Spatial Arbitrage Matrix
  const [arbitrageSignals, setArbitrageSignals] = useState<ArbitrageSignal[]>([
    {
      symbol: "ETH/USDT",
      buyExchange: "BINANCE",
      sellExchange: "BYBIT",
      buyPrice: 3462.10,
      sellPrice: 3488.50,
      grossSpreadPct: 0.762,
      netSpreadPct: 0.627,
      takerFeePct: 0.135,
      estimatedProfitUsdt: 62.70,
      isExecutable: true,
      status: "ARBITRAGE_TRIGGERED",
    },
    {
      symbol: "BTC/USDT",
      buyExchange: "BYBIT",
      sellExchange: "OKX",
      buyPrice: 92380.00,
      sellPrice: 93120.00,
      grossSpreadPct: 0.801,
      netSpreadPct: 0.661,
      takerFeePct: 0.140,
      estimatedProfitUsdt: 132.20,
      isExecutable: true,
      status: "ARBITRAGE_TRIGGERED",
    },
    {
      symbol: "SOL/USDT",
      buyExchange: "OKX",
      sellExchange: "BINANCE",
      buyPrice: 214.30,
      sellPrice: 215.85,
      grossSpreadPct: 0.723,
      netSpreadPct: 0.568,
      takerFeePct: 0.155,
      estimatedProfitUsdt: 45.44,
      isExecutable: false,
      status: "SPREAD_BELOW_0.6%",
    },
    {
      symbol: "BNB/USDT",
      buyExchange: "BINANCE",
      sellExchange: "OKX",
      buyPrice: 642.50,
      sellPrice: 645.10,
      grossSpreadPct: 0.404,
      netSpreadPct: 0.249,
      takerFeePct: 0.155,
      estimatedProfitUsdt: 19.92,
      isExecutable: false,
      status: "SPREAD_BELOW_0.6%",
    },
  ]);

  // Vault Staking Status
  const [vaultData, setVaultData] = useState<VaultData>({
    totalVaultEquity: 5120.45,
    pendingReserve: 88.50,
    flexibleStaked: 1450.00,
    lockedStaked: 3581.95,
    totalGrossProfitProcessed: 14620.00,
    totalMaintenanceFeesDeducted: 731.00,
    totalReinvestedIntoTrading: 9722.30,
    estimatedApyPct: 13.85,
    projectedMonthlyInterestUsdt: 59.10,
    lockedTiers: [
      { tenure: "90 Days Locked", amount: 2150.00, apy: 14.50, autoRenew: true },
      { tenure: "60 Days Locked", amount: 964.10, apy: 12.20, autoRenew: true },
      { tenure: "30 Days Locked", amount: 467.85, apy: 9.80, autoRenew: true },
    ],
    flexibleTier: { amount: 1450.00, asset: "USDT", apy: 7.20, autoSubscribe: true },
  });

  // Simulated live ticker oscillation
  useEffect(() => {
    const interval = setInterval(() => {
      if (circuitBreakerActive) return;

      // Subtle mark price updates
      setActiveTrades((prev) =>
        prev.map((trade) => {
          const delta = (Math.random() - 0.48) * (trade.markPrice * 0.0006);
          const newMark = parseFloat((trade.markPrice + delta).toFixed(2));
          const pnlUsdt =
            trade.side === "BUY"
              ? (newMark - trade.entryPrice) * trade.quantity
              : (trade.entryPrice - newMark) * trade.quantity;
          const pnlPct = (pnlUsdt / trade.notionalUsdt) * 100;
          return {
            ...trade,
            markPrice: newMark,
            unrealizedPnlUsdt: parseFloat(pnlUsdt.toFixed(2)),
            unrealizedPnlPct: parseFloat(pnlPct.toFixed(2)),
          };
        })
      );

      // Fluctuate arbitrage spreads slightly
      setArbitrageSignals((prev) =>
        prev.map((sig) => {
          const delta = (Math.random() - 0.5) * 0.02;
          const newNet = parseFloat((sig.netSpreadPct + delta).toFixed(3));
          const executable = newNet >= 0.60;
          return {
            ...sig,
            netSpreadPct: newNet,
            isExecutable: executable,
            status: executable ? "ARBITRAGE_TRIGGERED" : "SPREAD_BELOW_0.6%",
            estimatedProfitUsdt: parseFloat((1000 * (newNet / 100)).toFixed(2)),
          };
        })
      );
    }, 2800);

    return () => clearInterval(interval);
  }, [circuitBreakerActive]);

  // Toggle Circuit Breaker
  const handleToggleCircuitBreaker = () => {
    const nextState = !circuitBreakerActive;
    setCircuitBreakerActive(nextState);
    if (nextState) {
      setCircuitBreakerReason("Emergency Manual Halt triggered via Operator Dashboard");
      setNotificationLogs((prev) => [
        {
          id: `nt-${Date.now()}`,
          channel: "WHATSAPP",
          message: "🚨 EMERGENCY ALERT: Circuit Breaker ENGAGED manually. All order flow suspended!",
          timestamp: "Just now",
        },
        ...prev,
      ]);
    } else {
      setCircuitBreakerReason(null);
      setNotificationLogs((prev) => [
        {
          id: `nt-${Date.now()}`,
          channel: "TELEGRAM",
          message: "✅ Circuit Breaker RESET. Trading engine resumed normal multi-strategy execution.",
          timestamp: "Just now",
        },
        ...prev,
      ]);
    }
  };

  // Close active trade handler
  const handleCloseTrade = (tradeId: string) => {
    const trade = activeTrades.find((t) => t.id === tradeId);
    if (!trade) return;

    setActiveTrades((prev) => prev.filter((t) => t.id !== tradeId));
    const profit = Math.max(0, trade.unrealizedPnlUsdt);

    if (profit > 0) {
      // Execute profit waterfall: 5% fee, 70% reinvest, 30% vault
      const fee = profit * 0.05;
      const net = profit - fee;
      const reinvest = net * 0.70;
      const vaultAlloc = net * 0.30;

      setVaultData((prev) => ({
        ...prev,
        pendingReserve: parseFloat((prev.pendingReserve + vaultAlloc).toFixed(2)),
        totalGrossProfitProcessed: parseFloat((prev.totalGrossProfitProcessed + profit).toFixed(2)),
        totalMaintenanceFeesDeducted: parseFloat((prev.totalMaintenanceFeesDeducted + fee).toFixed(2)),
        totalReinvestedIntoTrading: parseFloat((prev.totalReinvestedIntoTrading + reinvest).toFixed(2)),
      }));

      setNotificationLogs((prev) => [
        {
          id: `nt-${Date.now()}`,
          channel: "TELEGRAM",
          message: `Closed ${trade.symbol} (${trade.strategy}) | Realized: +$${profit.toFixed(2)} USDT -> 5% Fee ($${fee.toFixed(2)}), 70% Reinvest ($${reinvest.toFixed(2)}), 30% Vault ($${vaultAlloc.toFixed(2)})`,
          timestamp: "Just now",
        },
        ...prev,
      ]);
    }
  };

  // Manual trigger for Binance Earn auto-sweep
  const handleTriggerSweep = () => {
    if (vaultData.pendingReserve <= 5) return;
    const amount = vaultData.pendingReserve;

    if (amount >= 100) {
      // Locked sweep
      setVaultData((prev) => ({
        ...prev,
        pendingReserve: 0,
        lockedStaked: parseFloat((prev.lockedStaked + amount).toFixed(2)),
      }));
      setNotificationLogs((prev) => [
        {
          id: `nt-${Date.now()}`,
          channel: "TELEGRAM",
          message: `🔒 Binance Simple Earn Locked Sweep: Subscribed $${amount.toFixed(2)} USDT for 60 Days @ 12.2% APY`,
          timestamp: "Just now",
        },
        ...prev,
      ]);
    } else {
      // Flexible sweep
      setVaultData((prev) => ({
        ...prev,
        pendingReserve: 0,
        flexibleStaked: parseFloat((prev.flexibleStaked + amount).toFixed(2)),
      }));
      setNotificationLogs((prev) => [
        {
          id: `nt-${Date.now()}`,
          channel: "TELEGRAM",
          message: `⚡ Binance Simple Earn Flexible Sweep: Subscribed $${amount.toFixed(2)} USDT @ 7.2% APY`,
          timestamp: "Just now",
        },
        ...prev,
      ]);
    }
  };

  // Manual Arbitrage execution
  const handleExecuteArbitrage = (sig: ArbitrageSignal) => {
    if (!sig.isExecutable || circuitBreakerActive) return;

    setNotificationLogs((prev) => [
      {
        id: `nt-${Date.now()}`,
        channel: "TELEGRAM",
        message: `⚡ SPATIAL ARBITRAGE EXECUTED: Buy ${sig.buyExchange} ($${sig.buyPrice}) -> Sell ${sig.sellExchange} ($${sig.sellPrice}) | Net Spread: +${sig.netSpreadPct}% | Profit: +$${sig.estimatedProfitUsdt} USDT`,
        timestamp: "Just now",
      },
      ...prev,
    ]);

    // Add to active positions or harvest
    setTodayPnl((prev) => parseFloat((prev + sig.estimatedProfitUsdt).toFixed(2)));
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-amber-500/30 selection:text-amber-200">
      {/* Top Precision Navigation Bar */}
      <header className="border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md sticky top-0 z-40 px-4 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <Logo size="md" />

        {/* System State & Emergency Circuit Breaker */}
        <div className="flex items-center gap-3">
          {/* Market Regime Badge */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <span className="text-slate-400">Regime:</span>
            <span className="font-mono font-bold text-amber-400">{marketRegime}</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">ADX:</span>
            <span className="font-mono text-emerald-400 font-semibold">{adxValue}</span>
          </div>

          {/* Drawdown Gauge */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <span className="text-slate-400">Daily DD:</span>
            <span
              className={`font-mono font-bold ${
                dailyDrawdownPct > 3.5 ? "text-rose-400" : "text-emerald-400"
              }`}
            >
              {dailyDrawdownPct}%
            </span>
            <span className="text-slate-500">/ {maxDrawdownLimitPct}% Cap</span>
          </div>

          {/* Circuit Breaker Emergency Toggle Button */}
          <button
            id="circuit-breaker-toggle-button"
            onClick={handleToggleCircuitBreaker}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-mono text-xs font-bold transition-all shadow-md ${
              circuitBreakerActive
                ? "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-900/40 animate-pulse border border-rose-400"
                : "bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 hover:border-amber-500/40"
            }`}
          >
            <ShieldAlert className={`w-4 h-4 ${circuitBreakerActive ? "text-white" : "text-amber-400"}`} />
            <span>
              {circuitBreakerActive ? "CIRCUIT BREAKER: TRIPPED (HALTED)" : "CIRCUIT BREAKER: ARMED"}
            </span>
          </button>
        </div>
      </header>

      {/* Circuit Breaker Emergency Alert Banner */}
      {circuitBreakerActive && (
        <div className="bg-rose-950/80 border-b border-rose-800/80 px-4 py-2.5 flex items-center justify-between text-xs text-rose-200">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 animate-bounce" />
            <span className="font-semibold">EMERGENCY HALT ACTIVE:</span>
            <span>{circuitBreakerReason || "All order generation suspended to protect capital."}</span>
          </div>
          <button
            onClick={handleToggleCircuitBreaker}
            className="px-2.5 py-1 rounded bg-rose-800 hover:bg-rose-700 text-white font-mono text-[11px] font-bold"
          >
            Reset Engine
          </button>
        </div>
      )}

      {/* Main Trading Workspace */}
      <main className="flex-1 p-4 lg:p-8 max-w-[1680px] w-full mx-auto space-y-6">
        {/* Top Key Metrics Row */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Account Equity */}
          <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 transition-colors shadow-sm">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="uppercase tracking-wider font-semibold">Total Portfolio Equity</span>
              <DollarSign className="w-4 h-4 text-amber-400" />
            </div>
            <div className="flex items-baseline gap-2.5">
              <span className="font-mono text-2xl lg:text-3xl font-bold text-white tracking-tight">
                ${totalEquity.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </span>
              <span className="text-xs font-mono font-semibold text-emerald-400 flex items-center">
                <ArrowUpRight className="w-3.5 h-3.5" />
                +{todayPnlPct}%
              </span>
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 font-mono">
              <span>Risk Sizing Cap: 1.5%</span>
              <span className="text-slate-500">Max Alloc: 30%</span>
            </div>
          </div>

          {/* 24h Realized & Unrealized PnL */}
          <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 transition-colors shadow-sm">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="uppercase tracking-wider font-semibold">24h Net Profit & Harvest</span>
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="flex items-baseline gap-2.5">
              <span className="font-mono text-2xl lg:text-3xl font-bold text-emerald-400 tracking-tight">
                +${todayPnl.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </span>
              <span className="text-xs font-mono text-slate-400">USDT</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 font-mono">
              <span>Win Rate: <strong className="text-emerald-400">{winRate}%</strong></span>
              <span className="text-slate-500">70/30 Compounded</span>
            </div>
          </div>

          {/* Binance Simple Earn Auto-Vault */}
          <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 transition-colors shadow-sm">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="uppercase tracking-wider font-semibold">Binance Earn Vault Equity</span>
              <Vault className="w-4 h-4 text-amber-400" />
            </div>
            <div className="flex items-baseline gap-2.5">
              <span className="font-mono text-2xl lg:text-3xl font-bold text-amber-300 tracking-tight">
                ${vaultData.totalVaultEquity.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </span>
              <span className="text-xs font-mono font-semibold text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                {vaultData.estimatedApyPct}% APY
              </span>
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 font-mono">
              <span>Flex: ${vaultData.flexibleStaked.toFixed(0)}</span>
              <span>Locked (30-90d): ${vaultData.lockedStaked.toFixed(0)}</span>
            </div>
          </div>

          {/* Spatial Arbitrage Live Status */}
          <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 transition-colors shadow-sm">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="uppercase tracking-wider font-semibold">Spatial Arbitrage Matrix</span>
              <Zap className="w-4 h-4 text-yellow-400" />
            </div>
            <div className="flex items-baseline gap-2.5">
              <span className="font-mono text-2xl lg:text-3xl font-bold text-white tracking-tight">
                {arbitrageSignals.filter((s) => s.isExecutable).length} Active
              </span>
              <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                ≥ 0.6% Spread
              </span>
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 font-mono">
              <span>Binance · Bybit · OKX</span>
              <span className="text-emerald-400 font-semibold">Auto-Execute ON</span>
            </div>
          </div>
        </section>

        {/* Interactive Charts & Telemetry Grid */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Real-Time PnL & Equity Growth Curve (2 cols on large screen) */}
          <div className="lg:col-span-2 p-6 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-amber-400" />
                  Autonomous Real-Time Equity & PnL Curve
                </h3>
                <p className="text-xs text-slate-400 mt-0.5 font-mono">
                  Scale-agnostic risk compounding with 1.5% stop guard & automated vault lockup
                </p>
              </div>

              {/* Timeframe Selector */}
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-mono">
                {(["1H", "24H", "7D", "30D", "ALL"] as const).map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setSelectedTimeframe(tf)}
                    className={`px-2.5 py-1 rounded transition-colors ${
                      selectedTimeframe === tf
                        ? "bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>

            {/* SVG High-Performance Reactive Chart */}
            <div className="h-64 sm:h-72 w-full relative">
              <svg className="w-full h-full overflow-visible" viewBox="0 0 800 240" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="pnlGlowGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10B981" stopOpacity="0.35" />
                    <stop offset="70%" stopColor="#F59E0B" stopOpacity="0.10" />
                    <stop offset="100%" stopColor="#020617" stopOpacity="0.0" />
                  </linearGradient>
                  <linearGradient id="strokeGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#F59E0B" />
                    <stop offset="40%" stopColor="#34D399" />
                    <stop offset="100%" stopColor="#10B981" />
                  </linearGradient>
                </defs>

                {/* Grid Lines */}
                <line x1="0" y1="40" x2="800" y2="40" stroke="#1E293B" strokeDasharray="3 3" />
                <line x1="0" y1="100" x2="800" y2="100" stroke="#1E293B" strokeDasharray="3 3" />
                <line x1="0" y1="160" x2="800" y2="160" stroke="#1E293B" strokeDasharray="3 3" />
                <line x1="0" y1="220" x2="800" y2="220" stroke="#1E293B" />

                {/* Area Gradient Fill */}
                <path
                  d="M 0 210 Q 100 190, 200 160 T 400 120 T 600 70 T 800 25 L 800 220 L 0 220 Z"
                  fill="url(#pnlGlowGrad)"
                />

                {/* Main Equity Path */}
                <path
                  d="M 0 210 Q 100 190, 200 160 T 400 120 T 600 70 T 800 25"
                  fill="none"
                  stroke="url(#strokeGrad)"
                  strokeWidth="3.2"
                  strokeLinecap="round"
                />

                {/* Milestone Nodes */}
                <circle cx="200" cy="160" r="4" fill="#F59E0B" />
                <circle cx="400" cy="120" r="4" fill="#34D399" />
                <circle cx="600" cy="70" r="4" fill="#10B981" />
                <circle cx="800" cy="25" r="6" fill="#10B981" className="animate-pulse" />
                <circle cx="800" cy="25" r="2.5" fill="#FFFFFF" />
              </svg>

              {/* Chart Overlay Annotations */}
              <div className="absolute top-2 right-4 bg-slate-950/90 border border-slate-800 rounded px-2.5 py-1 text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                Current: $24,850.25 (ATH Peak)
              </div>
            </div>

            {/* Bottom Legend */}
            <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 font-mono">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  Active Growth (70% Reinvest)
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                  Vault Staking (30% Locked)
                </span>
              </div>
              <span>Platform Maintenance Fee: 5.0% flat</span>
            </div>
          </div>

          {/* Engine Parameters & Smart Router Status (1 col) */}
          <div className="p-6 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between space-y-5">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2 mb-1">
                <Cpu className="w-4 h-4 text-amber-400" />
                Smart Order Router & Risk Guard
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                Orderbook Depth Guard (<span className="text-amber-400">&lt;0.05%</span> slippage) & TWAP
              </p>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
                <span className="text-slate-400">Execution Sizer:</span>
                <span className="text-emerald-400 font-bold">Scale-Agnostic (1.5% Risk)</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
                <span className="text-slate-400">Daily DD Cap (Circuit):</span>
                <span className="text-amber-400 font-bold">5.00% Max</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
                <span className="text-slate-400">Binance Min Notional:</span>
                <span className="text-slate-200 font-bold">$10.00 USDT Floor</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
                <span className="text-slate-400">Arbitrage Net Threshold:</span>
                <span className="text-emerald-400 font-bold">≥ 0.60% Net Spread</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
                <span className="text-slate-400">TWAP Slicer Sizing:</span>
                <span className="text-slate-200 font-bold">&gt; $2,500 USDT (5 Batches)</span>
              </div>
            </div>

            {/* Simulated Telegram / WhatsApp Status */}
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5 text-xs">
              <div className="flex items-center justify-between text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Send className="w-3.5 h-3.5 text-sky-400" />
                  Telegram Bot & Channel:
                </span>
                <span className="text-emerald-400 font-mono font-bold">CONNECTED</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Bell className="w-3.5 h-3.5 text-emerald-400" />
                  WhatsApp Emergency API:
                </span>
                <span className="text-emerald-400 font-mono font-bold">READY</span>
              </div>
            </div>
          </div>
        </section>

        {/* Section Navigation Tabs */}
        <div className="flex border-b border-slate-800 gap-6 text-sm font-semibold">
          <button
            onClick={() => setActiveTab("overview")}
            className={`pb-3 transition-colors border-b-2 ${
              activeTab === "overview"
                ? "border-amber-400 text-amber-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Active Positions ({activeTrades.length})
          </button>
          <button
            onClick={() => setActiveTab("arbitrage")}
            className={`pb-3 transition-colors border-b-2 flex items-center gap-2 ${
              activeTab === "arbitrage"
                ? "border-amber-400 text-amber-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Spatial Arbitrage Matrix
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-500/20 text-emerald-400">
              ≥ 0.6% Live
            </span>
          </button>
          <button
            onClick={() => setActiveTab("vault")}
            className={`pb-3 transition-colors border-b-2 flex items-center gap-2 ${
              activeTab === "vault"
                ? "border-amber-400 text-amber-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Binance Simple Earn Auto-Vault
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-amber-500/20 text-amber-400">
              30-90d Locked
            </span>
          </button>
          <button
            onClick={() => setActiveTab("regime")}
            className={`pb-3 transition-colors border-b-2 ${
              activeTab === "regime"
                ? "border-amber-400 text-amber-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Market Scanner & Regime
          </button>
        </div>

        {/* Tab 1: Active Trades */}
        {activeTab === "overview" && (
          <section className="space-y-4">
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/90 shadow-sm">
              <table className="w-full text-left border-collapse text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase tracking-wider">
                    <th className="p-4">Symbol / ID</th>
                    <th className="p-4">Strategy & Side</th>
                    <th className="p-4">Entry / Mark</th>
                    <th className="p-4">SL / TP</th>
                    <th className="p-4">Position Notional</th>
                    <th className="p-4">Allocated Risk (1.5%)</th>
                    <th className="p-4">Unrealized PnL</th>
                    <th className="p-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {activeTrades.map((trade) => (
                    <tr key={trade.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="p-4">
                        <div className="font-bold text-white text-sm">{trade.symbol}</div>
                        <div className="text-[11px] text-slate-500">{trade.id} · {trade.duration}</div>
                      </td>
                      <td className="p-4">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-amber-300 border border-slate-700 mb-1">
                          {trade.strategy.replace(/_/g, " ")}
                        </span>
                        <div className="text-emerald-400 font-bold">{trade.side} ({trade.leverage})</div>
                      </td>
                      <td className="p-4">
                        <div className="text-slate-300">Entry: ${trade.entryPrice.toLocaleString()}</div>
                        <div className="text-emerald-400 font-bold">Mark: ${trade.markPrice.toLocaleString()}</div>
                      </td>
                      <td className="p-4">
                        <div className="text-rose-400">SL: ${trade.stopLoss.toLocaleString()}</div>
                        <div className="text-emerald-400">TP: ${trade.takeProfit.toLocaleString()}</div>
                      </td>
                      <td className="p-4">
                        <div className="text-slate-200 font-bold">${trade.notionalUsdt.toLocaleString()}</div>
                        <div className="text-slate-500">{trade.quantity} units</div>
                      </td>
                      <td className="p-4">
                        <div className="text-amber-400 font-bold">${trade.allocatedRiskUsdt.toFixed(2)}</div>
                        <div className="text-[10px] text-slate-500">Max 1.5% Cap</div>
                      </td>
                      <td className="p-4">
                        <div className={`font-bold text-sm ${trade.unrealizedPnlUsdt >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {trade.unrealizedPnlUsdt >= 0 ? "+" : ""}${trade.unrealizedPnlUsdt.toFixed(2)}
                        </div>
                        <div className={`text-[11px] ${trade.unrealizedPnlPct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          ({trade.unrealizedPnlPct >= 0 ? "+" : ""}{trade.unrealizedPnlPct.toFixed(2)}%)
                        </div>
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => handleCloseTrade(trade.id)}
                          className="px-3 py-1.5 rounded bg-slate-800 hover:bg-rose-900/60 hover:text-rose-300 text-slate-300 text-xs font-bold border border-slate-700 transition-colors"
                        >
                          Close & Harvest
                        </button>
                      </td>
                    </tr>
                  ))}
                  {activeTrades.length === 0 && (
                    <tr>
                      <td colSpan={8} className="p-8 text-center text-slate-500">
                        No active trades currently open. Engine scanner is monitoring market regimes.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Tab 2: Spatial Arbitrage Matrix */}
        {activeTab === "arbitrage" && (
          <section className="space-y-4">
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400 shrink-0" />
                <span>
                  <strong>Spatial Arbitrage Rule:</strong> Scans Binance vs Bybit vs OKX orderbooks concurrently.
                  Automatically executes if <strong>Net Spread ≥ 0.60%</strong> after subtracting exchange taker fees (0.06% - 0.08%) and slippage buffers.
                </span>
              </div>
              <span className="font-mono text-emerald-400 font-bold">CCXT Async Live Poller</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {arbitrageSignals.map((sig, idx) => (
                <div
                  key={idx}
                  className={`p-5 rounded-xl border transition-all ${
                    sig.isExecutable
                      ? "bg-slate-900 border-emerald-500/50 shadow-lg shadow-emerald-950/20"
                      : "bg-slate-900/60 border-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-base font-mono">{sig.symbol}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          sig.isExecutable
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {sig.status}
                      </span>
                    </div>
                    <span className="font-mono text-xs text-slate-400">Order: $1,000 USDT</span>
                  </div>

                  {/* Execution Route Visualizer */}
                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs mb-3">
                    <div>
                      <div className="text-slate-500 text-[10px]">BUY EXCHANGE</div>
                      <div className="font-bold text-amber-400">{sig.buyExchange}</div>
                      <div className="text-slate-300">${sig.buyPrice.toLocaleString()}</div>
                    </div>
                    <div className="text-center px-3">
                      <ArrowUpRight className="w-5 h-5 text-emerald-400 mx-auto" />
                      <div className="text-[10px] text-slate-500 mt-0.5">Route</div>
                    </div>
                    <div className="text-right">
                      <div className="text-slate-500 text-[10px]">SELL EXCHANGE</div>
                      <div className="font-bold text-emerald-400">{sig.sellExchange}</div>
                      <div className="text-slate-300">${sig.sellPrice.toLocaleString()}</div>
                    </div>
                  </div>

                  {/* Spread breakdown */}
                  <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono mb-4">
                    <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                      <div className="text-slate-500 text-[10px]">GROSS SPREAD</div>
                      <div className="text-slate-300 font-semibold">+{sig.grossSpreadPct}%</div>
                    </div>
                    <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                      <div className="text-slate-500 text-[10px]">TAKER FEES</div>
                      <div className="text-rose-400 font-semibold">-{sig.takerFeePct}%</div>
                    </div>
                    <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                      <div className="text-slate-500 text-[10px]">NET PROFIT</div>
                      <div className={`font-bold ${sig.isExecutable ? "text-emerald-400" : "text-slate-400"}`}>
                        +{sig.netSpreadPct}%
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-xs font-mono">
                      <span className="text-slate-400">Est. Profit: </span>
                      <strong className="text-emerald-400">+${sig.estimatedProfitUsdt} USDT</strong>
                    </div>
                    <button
                      disabled={!sig.isExecutable || circuitBreakerActive}
                      onClick={() => handleExecuteArbitrage(sig)}
                      className={`px-3.5 py-1.5 rounded text-xs font-bold font-mono transition-colors ${
                        sig.isExecutable && !circuitBreakerActive
                          ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow"
                          : "bg-slate-800 text-slate-500 cursor-not-allowed"
                      }`}
                    >
                      Instant Arbitrage Route
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Tab 3: Binance Simple Earn Auto-Vault */}
        {activeTab === "vault" && (
          <section className="space-y-6">
            {/* Auto-compounding Rules Description */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
              <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-amber-400 font-bold block mb-1">1. 5% Platform Maintenance Fee</span>
                <p className="text-slate-400">Automatically deducted from gross trading profits prior to capital distribution.</p>
              </div>
              <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-emerald-400 font-bold block mb-1">2. 70% Reinvested into Trading</span>
                <p className="text-slate-400">Automatically scales active account equity for exponential compounding effect.</p>
              </div>
              <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-amber-300 font-bold block mb-1">3. 30% Binance Earn Vault</span>
                <p className="text-slate-400">Under $100: Flexible Earn. Over $100: Auto-sweep to Locked Staking (30/60/90 days).</p>
              </div>
            </div>

            {/* Staking Tiers Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Binance Simple Earn Locked Staking Tier */}
              <div className="p-6 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Lock className="w-5 h-5 text-amber-400" />
                    <div>
                      <h4 className="font-bold text-white text-sm">Binance Locked Staking (30 - 90 Days)</h4>
                      <p className="text-slate-400 text-xs font-mono">Trigger: Vault Reserve ≥ $100 USDT</p>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded text-xs font-bold font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30">
                    Up to 14.5% APY
                  </span>
                </div>

                <div className="space-y-3 font-mono text-xs">
                  {vaultData.lockedTiers.map((tier, i) => (
                    <div key={i} className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
                      <div>
                        <div className="font-bold text-slate-200">{tier.tenure}</div>
                        <div className="text-[11px] text-emerald-400 font-semibold">{tier.apy}% Yield APY</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-amber-300">${tier.amount.toLocaleString()} USDT</div>
                        <div className="text-[10px] text-slate-500">Auto-Renew: Active</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Binance Simple Earn Flexible Tier */}
              <div className="p-6 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Layers className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-bold text-white text-sm">Binance Flexible Earn</h4>
                      <p className="text-slate-400 text-xs font-mono">Trigger: Vault Reserve &lt; $100 USDT</p>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded text-xs font-bold font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    7.2% APY
                  </span>
                </div>

                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Flexible Balance:</span>
                    <strong className="text-white text-sm">${vaultData.flexibleStaked.toFixed(2)} USDT</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Unallocated Reserve Pool:</span>
                    <strong className="text-amber-400 text-sm">${vaultData.pendingReserve.toFixed(2)} USDT</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Projected Monthly Yield:</span>
                    <strong className="text-emerald-400 text-sm">+${vaultData.projectedMonthlyInterestUsdt} USDT</strong>
                  </div>

                  <button
                    onClick={handleTriggerSweep}
                    disabled={vaultData.pendingReserve <= 5}
                    className={`w-full py-2 rounded text-xs font-bold transition-all mt-2 ${
                      vaultData.pendingReserve > 5
                        ? "bg-amber-500 hover:bg-amber-400 text-slate-950 font-sans"
                        : "bg-slate-800 text-slate-500 cursor-not-allowed"
                    }`}
                  >
                    Execute Binance Simple Earn Auto-Sweep Now
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Tab 4: Market Scanner & Regime */}
        {activeTab === "regime" && (
          <section className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase font-semibold">ADX Momentum Metric</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="font-mono text-3xl font-bold text-emerald-400">{adxValue}</span>
                  <span className="text-xs text-slate-400 font-mono">&gt; 25 = Breakout</span>
                </div>
                <div className="mt-3 text-xs text-slate-400 font-mono">
                  Current Regime: <strong className="text-amber-400 font-bold">BREAKOUT STRATEGY ACTIVE</strong>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase font-semibold">ATR Volatility Metric</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="font-mono text-3xl font-bold text-amber-400">{atrPct}%</span>
                  <span className="text-xs text-slate-400 font-mono">14 Periods Wilder</span>
                </div>
                <div className="mt-3 text-xs text-slate-400 font-mono">
                  Stop Distance: <strong className="text-slate-200">1.8x ATR Multiplier</strong>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase font-semibold">Regime Strategy Filter</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="font-mono text-xl font-bold text-white">Donchian 20 Break</span>
                </div>
                <div className="mt-3 text-xs text-slate-400 font-mono">
                  Mean-Reversion switches ON when ADX &lt; 20.0
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Live Multi-Channel Notification Stream */}
        <section className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-400" />
              <h4 className="text-xs uppercase tracking-wider font-bold text-slate-300">
                Live Notification Dispatch Ledger (Telegram & WhatsApp API)
              </h4>
            </div>
            <span className="text-[11px] font-mono text-slate-500">Synchronized Event Bus</span>
          </div>

          <div className="space-y-2 font-mono text-xs">
            {notificationLogs.map((log) => (
              <div
                key={log.id}
                className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 flex items-start justify-between gap-4"
              >
                <div className="flex items-start gap-2.5">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[9px] font-bold shrink-0 ${
                      log.channel === "WHATSAPP"
                        ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                        : "bg-sky-500/20 text-sky-400 border border-sky-500/30"
                    }`}
                  >
                    {log.channel}
                  </span>
                  <span className="text-slate-300 leading-relaxed">{log.message}</span>
                </div>
                <span className="text-slate-500 text-[10px] shrink-0">{log.timestamp}</span>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500 font-mono">
        MONEY For HONEY · autonomous Trading system and build self wealth engine for the future · Production V2
      </footer>
    </div>
  );
}
