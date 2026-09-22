export interface ActiveTrade {
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

export interface HistoricalTrade {
  id: string;
  symbol: string;
  strategy: string;
  side: "BUY" | "SELL" | "ARBITRAGE";
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  stakeUsdt: number;
  realizedPnlUsdt: number;
  roiPct: number;
  duration: string;
  riskProfile: string;
  winScore: string; // e.g. "5/5", "4/5"
  closedAt: string;
  status: "WIN" | "LOSS" | "BREAKEVEN";
  feeUsdt: number;
  reinvestUsdt: number;
  vaultUsdt: number;
  exchange: string;
}

export interface PnLLedgerEntry {
  id: string;
  tradeId: string;
  symbol: string;
  timestamp: string;
  grossProfitUsdt: number;
  feeDeductedUsdt: number; // 5%
  netProfitUsdt: number;
  reinvestAllocUsdt: number; // 70%
  vaultReserveAllocUsdt: number; // 30%
  balanceAfterUsdt: number;
  vaultAfterUsdt: number;
}

export interface ArbitrageSignal {
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

export interface VaultData {
  totalVaultEquity: number;
  pendingReserve: number;
  flexibleStaked: number;
  lockedStaked: number;
  totalGrossProfitProcessed: number;
  totalMaintenanceFeesDeducted: number;
  totalReinvestedIntoTrading: number;
  estimatedApyPct: number;
  projectedMonthlyInterestUsdt: number;
  lockedTiers: Array<{
    tenure: string;
    amount: number;
    apy: number;
    autoRenew: boolean;
  }>;
  flexibleTier: {
    amount: number;
    asset: string;
    apy: number;
    autoSubscribe: boolean;
  };
}

export interface NotificationItem {
  id: string;
  channel: "TELEGRAM" | "WHATSAPP";
  message: string;
  timestamp: string;
  type: "TRADE" | "VAULT" | "CIRCUIT" | "ARBITRAGE" | "PNL_CARD";
}

export type PnLCardTheme =
  | "golden_wave_surfer" // exact like uploaded image
  | "money_for_honey_hive"
  | "midnight_neon_bull"
  | "cosmic_nebula"
  | "matrix_alpha"
  | "luxury_dark_gold";

export interface PnLCardConfig {
  symbol: string;
  roiPct: number;
  profitUsdt: number;
  stakeUsdt: number;
  duration: string;
  riskProfile: string;
  winScore: string;
  botHandle: string;
  referralLink: string;
  theme: PnLCardTheme;
  aspectRatio: "16:9" | "9:16";
  showQrCode: boolean;
}

export interface ServerBridgeConfig {
  serverHost: string; // e.g. "http://47.245.xxx.xxx:8000" or empty
  autoSync: boolean;
  isConnected: boolean;
  lastSyncTime: string;
  latencyMs: number;
  liveExchangeStatus: {
    exchange: string;
    accountEquity: number;
    usdtFree: number;
    activePositionsCount: number;
    circuitBreaker: boolean;
    testnetMode: boolean;
  };
}
