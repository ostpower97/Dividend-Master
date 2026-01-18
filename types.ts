export interface StockData {
  symbol: string;
  name: string;
  price: number;
  dividendYield: number; // as percentage
  dividendGrowth: number; // as percentage (Dividend CAGR)
  priceGrowth: number; // as percentage (Capital Appreciation CAGR)
  payoutFrequency: number; // 1 = Yearly, 4 = Quarterly, 12 = Monthly
}

export interface PortfolioItem {
  id: string;
  symbol: string;
  shares: number;
  buyPrice: number;
  reinvest: boolean;
  monthlyContribution?: number;
  // Merged data from "market"
  name?: string;
  currentPrice?: number;
  dividendYield?: number;
  dividendGrowth?: number;
  priceGrowth?: number; // New field
  payoutFrequency?: number; // Defaults to 1 if unknown
}

export interface UserSettings {
  pauschbetrag: number;
  initialLumpSum: number;
}

export interface YearProjection {
  year: number;
  grossDividend: number;
  netDividend: number;
  taxPaid: number;
  totalPortfolioValue: number;
  tickerBreakdown: Record<string, number>;
  accumulatedShares: Record<string, number>;
}

export enum SimulationMode {
  STATIC = 'STATIC',
  REINVEST_DRIP = 'REINVEST_DRIP',
  SMART_ALLOCATION = 'SMART_ALLOCATION'
}