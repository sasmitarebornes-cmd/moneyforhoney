import React, { useState } from "react";
import confetti from "canvas-confetti";
import {
  Sparkles,
  Sliders,
  Share2,
  Send,
  MessageCircle,
  Download,
  Copy,
  Check,
  RefreshCw,
  Monitor,
  Smartphone,
  Layers,
  Zap,
  Globe,
  Flame,
} from "lucide-react";
import { HistoricalTrade, PnLCardConfig, PnLCardTheme } from "../types";
import PnLCard from "./PnLCard";

interface PnLCardStudioViewProps {
  recentTrades: HistoricalTrade[];
  onBroadcastNotification: (msg: string) => void;
}

export const PnLCardStudioView: React.FC<PnLCardStudioViewProps> = ({
  recentTrades,
  onBroadcastNotification,
}) => {
  const [config, setConfig] = useState<PnLCardConfig>({
    symbol: "JOD/CNY OTC",
    roiPct: 512,
    profitUsdt: 51.2,
    stakeUsdt: 10,
    duration: "2m 51s",
    riskProfile: "Aggressive",
    winScore: "5/5",
    botHandle: "@MoneyForHoneyBot",
    referralLink: "https://t.me/MoneyForHoneyBot?start=trade_vip",
    theme: "golden_wave_surfer",
    aspectRatio: "16:9",
    showQrCode: true,
  });

  const [webhookStatus, setWebhookStatus] = useState<string | null>(null);

  const themes: Array<{ id: PnLCardTheme; name: string; icon: string; desc: string }> = [
    {
      id: "golden_wave_surfer",
      name: "Golden Radiant Waves",
      icon: "🌊",
      desc: "Cinematic golden barrel ocean sunset with particle shimmer",
    },
    {
      id: "money_for_honey_hive",
      name: "Cyber Honey Hive",
      icon: "🍯",
      desc: "Futuristic gold honeycomb & quant candlestick",
    },
    {
      id: "midnight_neon_bull",
      name: "Midnight Neon Bull",
      icon: "🐂",
      desc: "Dubai & Wall St quant laser matrix grid",
    },
    {
      id: "cosmic_nebula",
      name: "Cosmic Nebula Moon",
      icon: "🚀",
      desc: "Deep space galaxy stardust & momentum trajectory",
    },
    {
      id: "matrix_alpha",
      name: "Matrix Alpha Terminal",
      icon: "💻",
      desc: "Cyberpunk binary orderbook high-frequency feed",
    },
    {
      id: "luxury_dark_gold",
      name: "Luxury Dark Gold",
      icon: "👑",
      desc: "Minimal matte carbon with 24K gold accents",
    },
  ];

  // Quick preset from recent winning trades
  const handleSelectRecentTrade = (trade: HistoricalTrade) => {
    setConfig({
      ...config,
      symbol: trade.symbol,
      roiPct: trade.roiPct,
      profitUsdt: trade.realizedPnlUsdt,
      stakeUsdt: trade.stakeUsdt,
      duration: trade.duration,
      riskProfile: trade.riskProfile,
      winScore: trade.winScore,
    });

    try {
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.6 },
        colors: ["#10FF85", "#F59E0B", "#38BDF8"],
      });
    } catch {
      // safe fallback
    }
  };

  // Simulate Webhook Auto-Broadcast
  const handleSimulateWebhook = () => {
    setWebhookStatus("broadcasting");
    setTimeout(() => {
      setWebhookStatus("success");
      onBroadcastNotification(
        `🚀 AUTO-BROADCAST: PnL Card for ${config.symbol} (+${config.roiPct}%) dispatched to Telegram Channel & VIP WhatsApp Group!`
      );
      setTimeout(() => setWebhookStatus(null), 4000);
    }, 1200);
  };

  return (
    <div className="space-y-6">
      {/* Studio Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/40 border border-amber-500/20 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Sparkles className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white font-mono flex items-center gap-2">
              Viral PnL Card Generator Studio
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                PRO EDITION
              </span>
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Instantly generate high-converting trade brag cards matching the screenshot with dynamic QR codes and multiple themes
            </p>
          </div>
        </div>

        {/* Aspect Ratio & Reset */}
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-1 text-xs font-mono">
            <button
              onClick={() => setConfig({ ...config, aspectRatio: "16:9" })}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-colors ${
                config.aspectRatio === "16:9"
                  ? "bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Monitor className="w-3.5 h-3.5" />
              <span>16:9 Landscape</span>
            </button>
            <button
              onClick={() => setConfig({ ...config, aspectRatio: "9:16" })}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-colors ${
                config.aspectRatio === "9:16"
                  ? "bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Smartphone className="w-3.5 h-3.5" />
              <span>9:16 Story</span>
            </button>
          </div>

          <button
            onClick={() =>
              setConfig({
                symbol: "BTC/USDT",
                roiPct: 245,
                profitUsdt: 245.0,
                stakeUsdt: 100,
                duration: "18m 32s",
                riskProfile: "Moderate",
                winScore: "5/5",
                botHandle: "@MoneyForHoneyBot",
                referralLink: "https://t.me/MoneyForHoneyBot?start=trade_vip",
                theme: "golden_wave_surfer",
                aspectRatio: "16:9",
                showQrCode: true,
              })
            }
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>
        </div>
      </div>

      {/* Main Studio Grid: Left Canvas, Right Controls */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Left Column: Live High-Res Card Canvas Preview (7 cols) */}
        <div className="xl:col-span-7 flex flex-col items-center p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-5">
          <div className="w-full flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="flex items-center gap-2 font-bold text-white uppercase">
              <Flame className="w-4 h-4 text-amber-400" />
              Live Rendered Output
            </span>
            <span>{config.aspectRatio === "16:9" ? "1280 × 720 px (HD)" : "720 × 1280 px (Vertical)"}</span>
          </div>

          <div className="w-full flex justify-center py-2">
            <PnLCard config={config} />
          </div>

          {/* Social Webhook Auto-Broadcast simulation */}
          <div className="w-full max-w-[860px] p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
            <div>
              <span className="font-bold text-slate-200 block">Automated Social Bot Dispatcher:</span>
              <span className="text-slate-500 text-[11px]">
                Sends high-res image & brag caption to Telegram Channel & WhatsApp Community
              </span>
            </div>

            <button
              onClick={handleSimulateWebhook}
              disabled={webhookStatus === "broadcasting"}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold transition-all disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>
                {webhookStatus === "broadcasting"
                  ? "Dispatching..."
                  : webhookStatus === "success"
                  ? "Dispatched Successfully!"
                  : "Dispatch to Channels"}
              </span>
            </button>
          </div>
        </div>

        {/* Right Column: Customizer & Recent Trades (5 cols) */}
        <div className="xl:col-span-5 space-y-6">
          {/* Quick Theme Selector */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
            <label className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold block">
              Card Background Visual Theme:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {themes.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setConfig({ ...config, theme: t.id })}
                  className={`p-2.5 rounded-xl border text-left flex flex-col justify-between transition-all ${
                    config.theme === t.id
                      ? "bg-amber-500/15 border-amber-500 text-white shadow-md ring-1 ring-amber-400"
                      : "bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="text-lg">{t.icon}</div>
                  <div className="font-mono text-xs font-bold text-slate-200 truncate mt-1">{t.name}</div>
                  <div className="text-[10px] text-slate-500 line-clamp-1">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Quick-Pick From Winning Trades */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400 font-bold uppercase">1-Click Load Recent Trade:</span>
              <span className="text-emerald-400 font-semibold">{recentTrades.filter((t) => t.status === "WIN").length} Wins Available</span>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {recentTrades.slice(0, 5).map((t) => (
                <button
                  key={t.id}
                  onClick={() => handleSelectRecentTrade(t)}
                  className="w-full p-2.5 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/40 text-left flex items-center justify-between transition-colors text-xs font-mono"
                >
                  <div>
                    <span className="font-bold text-white">{t.symbol}</span>
                    <span className="text-slate-500 text-[11px] ml-2">({t.strategy.replace(/_/g, " ")})</span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-emerald-400">+{t.roiPct}%</span>
                    <span className="text-slate-400 text-[11px] ml-1.5">(+${t.realizedPnlUsdt.toFixed(2)})</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Data Controls Form */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <span className="text-xs font-mono font-bold uppercase text-slate-300 flex items-center gap-2">
              <Sliders className="w-3.5 h-3.5 text-amber-400" />
              Tune Data & Text Fields
            </span>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div>
                <label className="text-slate-400 block mb-1">Pair / Symbol</label>
                <input
                  type="text"
                  value={config.symbol}
                  onChange={(e) => setConfig({ ...config, symbol: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-white font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">ROI % (Multiplier)</label>
                <input
                  type="number"
                  value={config.roiPct}
                  onChange={(e) => {
                    const roi = parseFloat(e.target.value) || 0;
                    const profit = parseFloat(((config.stakeUsdt * roi) / 100).toFixed(2));
                    setConfig({ ...config, roiPct: roi, profitUsdt: profit });
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-emerald-400 font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Stake ($)</label>
                <input
                  type="number"
                  value={config.stakeUsdt}
                  onChange={(e) => {
                    const stake = parseFloat(e.target.value) || 0;
                    const profit = parseFloat(((stake * config.roiPct) / 100).toFixed(2));
                    setConfig({ ...config, stakeUsdt: stake, profitUsdt: profit });
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-white font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Profit Harvest ($)</label>
                <input
                  type="number"
                  value={config.profitUsdt}
                  onChange={(e) => setConfig({ ...config, profitUsdt: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-emerald-400 font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Duration</label>
                <input
                  type="text"
                  value={config.duration}
                  onChange={(e) => setConfig({ ...config, duration: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Risk Profile</label>
                <input
                  type="text"
                  value={config.riskProfile}
                  onChange={(e) => setConfig({ ...config, riskProfile: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Win Score</label>
                <input
                  type="text"
                  value={config.winScore}
                  onChange={(e) => setConfig({ ...config, winScore: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Bot / Referral Tag</label>
                <input
                  type="text"
                  value={config.botHandle}
                  onChange={(e) => setConfig({ ...config, botHandle: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-amber-400 font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-800 text-xs font-mono">
              <label className="text-slate-400 block">Referral Link (Embedded in QR Code)</label>
              <input
                type="text"
                value={config.referralLink}
                onChange={(e) => setConfig({ ...config, referralLink: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-sky-400 focus:border-amber-400 focus:outline-none"
              />

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="studio-toggle-qr"
                  checked={config.showQrCode}
                  onChange={(e) => setConfig({ ...config, showQrCode: e.target.checked })}
                  className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-amber-400 focus:ring-amber-400"
                />
                <label htmlFor="studio-toggle-qr" className="text-slate-300 select-none cursor-pointer">
                  Display Referral QR code block on card
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PnLCardStudioView;
