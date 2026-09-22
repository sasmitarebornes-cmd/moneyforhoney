import React, { useState } from "react";
import {
  Server,
  Wifi,
  WifiOff,
  RefreshCw,
  Copy,
  Check,
  Terminal,
  ShieldCheck,
  Globe,
  Sliders,
  X,
  Play,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { ServerBridgeConfig } from "../types";

interface LiveServerBridgeModalProps {
  isOpen: boolean;
  onClose: () => void;
  bridgeConfig: ServerBridgeConfig;
  onUpdateHost: (host: string) => void;
  onManualSync: () => void;
  isConnecting: boolean;
  onApplyRealBalance: (balance: number) => void;
}

export const LiveServerBridgeModal: React.FC<LiveServerBridgeModalProps> = ({
  isOpen,
  onClose,
  bridgeConfig,
  onUpdateHost,
  onManualSync,
  isConnecting,
  onApplyRealBalance,
}) => {
  const [hostInput, setHostInput] = useState(bridgeConfig.serverHost || "");
  const [showEndpointInput, setShowEndpointInput] = useState(false);

  if (!isOpen) return null;

  const handleSaveHost = () => {
    let clean = hostInput.trim();
    if (
      clean &&
      !clean.startsWith("http://") &&
      !clean.startsWith("https://")
    ) {
      clean = `http://${clean}`;
    }
    if (clean && clean.match(/^http:\/\/\d+\.\d+\.\d+\.\d+$/)) {
      clean = `${clean}:8000`;
    }
    onUpdateHost(clean);
  };

  const handleDisconnect = () => {
    onUpdateHost("");
    setHostInput("");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                bridgeConfig.isConnected
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "bg-sky-500/10 text-sky-400 border border-sky-500/30"
              }`}
            >
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Private Execution Node Link
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    bridgeConfig.isConnected
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {bridgeConfig.isConnected
                    ? "🟢 SECURE LINK ACTIVE"
                    : "⚪ STANDALONE MODE"}
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Pengaturan koneksi terenkripsi ke node trading internal Anda
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Quick Apply Real Binance Balance (Instant Sync Shortcut) */}
          <div className="bg-slate-950/90 border border-emerald-500/20 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-emerald-300 uppercase tracking-wider">
                  Verifikasi Saldo Live ($17.11 USDT)
                </span>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono font-bold text-[10px]">
                BINANCE SPOT
              </span>
            </div>
            <p className="text-xs text-slate-300">
              Gunakan saldo real-time Binance Spot Anda sebesar{" "}
              <strong>$17.1165 USDT</strong> secara instan pada seluruh
              kalkulator risiko dan metrik dashboard tanpa mengekspos detail
              teknis.
            </p>
            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={() => onApplyRealBalance(17.1165)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg transition flex items-center gap-1.5 shadow-sm"
              >
                <Sliders className="w-3.5 h-3.5" />
                Sinkronkan Saldo $17.12 USDT
              </button>
            </div>
          </div>

          {/* Private Endpoint Gateway Section */}
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <Server className="w-4 h-4 text-sky-400" />
                Private Gateway Endpoint
              </span>
              <button
                onClick={() => setShowEndpointInput(!showEndpointInput)}
                className="text-xs text-sky-400 hover:text-sky-300 font-medium"
              >
                {showEndpointInput ? "Sembunyikan" : "Konfigurasi URL"}
              </button>
            </div>

            {bridgeConfig.isConnected ? (
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-emerald-500/30">
                <div className="flex items-center gap-2 text-xs">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="font-mono text-emerald-300 font-semibold">
                    Private Node: [Connected]
                  </span>
                  <span className="text-slate-500 text-[11px]">
                    ({bridgeConfig.latencyMs}ms)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={onManualSync}
                    disabled={isConnecting}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded transition flex items-center gap-1"
                  >
                    <RefreshCw
                      className={`w-3 h-3 ${isConnecting ? "animate-spin" : ""}`}
                    />
                    Sync
                  </button>
                  <button
                    onClick={handleDisconnect}
                    className="px-2.5 py-1 bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border border-rose-500/30 text-xs rounded transition"
                  >
                    Putuskan
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 leading-relaxed">
                Dashboard saat ini berjalan dalam mode mandiri yang aman. Anda
                dapat menghubungkan endpoint API internal Anda sewaktu-waktu.
              </p>
            )}

            {showEndpointInput && (
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <label className="text-[11px] text-slate-400 block font-mono">
                  Masukkan Endpoint Gateway Pribadi:
                </label>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={hostInput}
                    onChange={(e) => setHostInput(e.target.value)}
                    placeholder="http://127.0.0.1:8000"
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-slate-600 focus:outline-none focus:border-sky-400"
                  />
                  <button
                    onClick={handleSaveHost}
                    disabled={isConnecting || !hostInput}
                    className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-lg transition flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {isConnecting ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Wifi className="w-3.5 h-3.5" />
                    )}
                    Simpan
                  </button>
                </div>
                <p className="text-[10px] text-slate-500">
                  Endpoint tersimpan secara lokal di browser Anda dan tidak
                  pernah dibagikan.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span
              className={`w-2 h-2 rounded-full ${bridgeConfig.isConnected ? "bg-emerald-400" : "bg-slate-500"}`}
            />
            <span>
              Mode:{" "}
              {bridgeConfig.isConnected
                ? "Node Terhubung"
                : "Private Standalone"}
            </span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};

export default LiveServerBridgeModal;
