import React, { useState, useEffect } from "react";
import confetti from "canvas-confetti";
import { X, Sparkles, Sliders, RefreshCw, Share2, Layers, Smartphone, Monitor } from "lucide-react";
import { PnLCardConfig, PnLCardTheme } from "../types";
import PnLCard from "./PnLCard";

interface PnLCardGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialConfig: PnLCardConfig;
}

export const PnLCardGeneratorModal: React.FC<PnLCardGeneratorModalProps> = ({
  isOpen,
  onClose,
  initialConfig,
}) => {
  const [config, setConfig] = useState<PnLCardConfig>(initialConfig);
  const [activeTab, setActiveTab] = useState<"preview" | "customize">("preview");

  useEffect(() => {
    setConfig(initialConfig);
    if (isOpen && initialConfig.roiPct > 0) {
      // Trigger festive quant confetti
      try {
        confetti({
          particleCount: 75,
          spread: 70,
          origin: { y: 0.6 },
          colors: ["#10FF85", "#F59E0B", "#38BDF8", "#FFFFFF"],
        });
      } catch {
        // Safe fallback
      }
    }
  }, [isOpen, initialConfig]);

  if (!isOpen) return null;

  const themes: Array<{ id: PnLCardTheme; name: string; icon: string; desc: string }> = [
    {
      id: "golden_wave_surfer",
      name: "Golden Radiant Waves",
      icon: "🌊",
      desc: "Cinematic golden barrel ocean sunset with radiant amber shimmer",
    },
    {
      id: "money_for_honey_hive",
      name: "Cyber Honey Hive",
      icon: "🍯",
      desc: "Glowing gold honeycomb & green quant candlestick",
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
      desc: "Deep space nebula & galaxy stardust",
    },
    {
      id: "matrix_alpha",
      name: "Matrix Alpha Terminal",
      icon: "💻",
      desc: "Cyberpunk high-frequency binary stream",
    },
    {
      id: "luxury_dark_gold",
      name: "Luxury Dark Gold",
      icon: "👑",
      desc: "Minimal matte carbon with 24K gold accents",
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-5xl rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden flex flex-col my-auto max-h-[95vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white font-mono flex items-center gap-2">
                Auto PnL Card Generator
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  VIRAL READY
                </span>
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Generate high-converting share cards for Telegram, WhatsApp, Twitter & Discord
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Aspect Ratio Toggle */}
            <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-1 text-xs font-mono">
              <button
                onClick={() => setConfig({ ...config, aspectRatio: "16:9" })}
                className={`flex items-center gap-1 px-2.5 py-1 rounded transition-colors ${
                  config.aspectRatio === "16:9"
                    ? "bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30"
                    : "text-slate-400 hover:text-white"
                }`}
                title="Landscape 16:9 (Telegram, Twitter, Discord)"
              >
                <Monitor className="w-3.5 h-3.5" />
                <span>16:9</span>
              </button>
              <button
                onClick={() => setConfig({ ...config, aspectRatio: "9:16" })}
                className={`flex items-center gap-1 px-2.5 py-1 rounded transition-colors ${
                  config.aspectRatio === "9:16"
                    ? "bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30"
                    : "text-slate-400 hover:text-white"
                }`}
                title="Story 9:16 (WhatsApp Status, Instagram Story, TikTok)"
              >
                <Smartphone className="w-3.5 h-3.5" />
                <span>9:16</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Quick Theme Selector Bar */}
          <div>
            <label className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2.5 block">
              Choose Visual Theme:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
              {themes.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setConfig({ ...config, theme: t.id })}
                  className={`p-2.5 rounded-xl border text-left flex flex-col justify-between transition-all ${
                    config.theme === t.id
                      ? "bg-amber-500/10 border-amber-500/60 shadow-md shadow-amber-500/10 ring-1 ring-amber-400"
                      : "bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="text-lg mb-1">{t.icon}</div>
                  <div className="font-mono text-xs font-bold text-white truncate">{t.name}</div>
                  <div className="text-[10px] text-slate-500 line-clamp-1">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Centerpiece: Live High-Resolution Card */}
          <div className="flex justify-center bg-slate-950/70 p-4 sm:p-6 rounded-2xl border border-slate-800/80">
            <PnLCard config={config} />
          </div>

          {/* Live Customizer Accordion / Fields */}
          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold uppercase text-slate-300 flex items-center gap-2">
                <Sliders className="w-3.5 h-3.5 text-amber-400" />
                Customize Card Data & Social Tags
              </span>
              <button
                onClick={() =>
                  setConfig({
                    ...config,
                    symbol: "JOD/CNY OTC",
                    roiPct: 512,
                    profitUsdt: 51.2,
                    stakeUsdt: 10,
                    duration: "2m 51s",
                    riskProfile: "Aggressive",
                    winScore: "5/5",
                    botHandle: "@SuperTradingAIbot",
                  })
                }
                className="text-[11px] font-mono text-amber-400 hover:underline flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                Reset to Screenshot Values
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div>
                <label className="text-slate-400 block mb-1">Pair / Symbol</label>
                <input
                  type="text"
                  value={config.symbol}
                  onChange={(e) => setConfig({ ...config, symbol: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white font-bold focus:border-amber-400 focus:outline-none"
                  placeholder="BTC/USDT"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">ROI % (Return)</label>
                <input
                  type="number"
                  value={config.roiPct}
                  onChange={(e) => {
                    const roi = parseFloat(e.target.value) || 0;
                    const profit = parseFloat(((config.stakeUsdt * roi) / 100).toFixed(2));
                    setConfig({ ...config, roiPct: roi, profitUsdt: profit });
                  }}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-emerald-400 font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Stake / Margin ($)</label>
                <input
                  type="number"
                  value={config.stakeUsdt}
                  onChange={(e) => {
                    const stake = parseFloat(e.target.value) || 0;
                    const profit = parseFloat(((stake * config.roiPct) / 100).toFixed(2));
                    setConfig({ ...config, stakeUsdt: stake, profitUsdt: profit });
                  }}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Net Profit ($)</label>
                <input
                  type="number"
                  value={config.profitUsdt}
                  onChange={(e) => setConfig({ ...config, profitUsdt: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-emerald-400 font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Trade Duration</label>
                <input
                  type="text"
                  value={config.duration}
                  onChange={(e) => setConfig({ ...config, duration: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:border-amber-400 focus:outline-none"
                  placeholder="2m 51s"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Strategy / Profile</label>
                <input
                  type="text"
                  value={config.riskProfile}
                  onChange={(e) => setConfig({ ...config, riskProfile: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:border-amber-400 focus:outline-none"
                  placeholder="Aggressive"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Win Score</label>
                <input
                  type="text"
                  value={config.winScore}
                  onChange={(e) => setConfig({ ...config, winScore: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:border-amber-400 focus:outline-none"
                  placeholder="5/5"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Bot / Referral Tag</label>
                <input
                  type="text"
                  value={config.botHandle}
                  onChange={(e) => setConfig({ ...config, botHandle: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-amber-400 font-bold focus:border-amber-400 focus:outline-none"
                  placeholder="@MoneyForHoneyBot"
                />
              </div>
            </div>

            {/* Referral Link & QR toggle */}
            <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
              <div className="flex-1 min-w-[280px]">
                <label className="text-slate-400 block mb-1">Dynamic Referral Link (Embedded in QR Code)</label>
                <input
                  type="text"
                  value={config.referralLink}
                  onChange={(e) => setConfig({ ...config, referralLink: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-sky-400 focus:border-amber-400 focus:outline-none"
                  placeholder="https://t.me/MoneyForHoneyBot?start=ref_vip"
                />
              </div>

              <div className="flex items-center gap-2 pt-4">
                <input
                  type="checkbox"
                  id="modal-toggle-qr"
                  checked={config.showQrCode}
                  onChange={(e) => setConfig({ ...config, showQrCode: e.target.checked })}
                  className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-amber-400 focus:ring-amber-400"
                />
                <label htmlFor="modal-toggle-qr" className="text-slate-300 select-none cursor-pointer">
                  Show Referral QR Code badge
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/90 flex items-center justify-between text-xs font-mono text-slate-400">
          <span>Resolution: {config.aspectRatio === "16:9" ? "1280 × 720 px" : "720 × 1280 px"}</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          >
            Close Window
          </button>
        </div>
      </div>
    </div>
  );
};

export default PnLCardGeneratorModal;
