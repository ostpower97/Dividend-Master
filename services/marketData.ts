import { StockData } from '../types';

// Erweiterte Offline-Datenbank für gängige Dividenden-Titel
// PayoutFrequency: 12=Monatlich, 4=Quartalsweise, 1=Jährlich
const MARKET_DB: Record<string, StockData> = {
  // --- MONATSZAHLER (Monthly) ---
  'O': { symbol: 'O', name: 'Realty Income', price: 52.50, dividendYield: 5.8, dividendGrowth: 3.1, priceGrowth: 2.5, payoutFrequency: 12 },
  'MAIN': { symbol: 'MAIN', name: 'Main Street Capital', price: 49.80, dividendYield: 6.1, dividendGrowth: 3.5, priceGrowth: 4.2, payoutFrequency: 12 },
  'STAG': { symbol: 'STAG', name: 'STAG Industrial', price: 36.20, dividendYield: 4.1, dividendGrowth: 0.7, priceGrowth: 3.0, payoutFrequency: 12 },
  'LTC': { symbol: 'LTC', name: 'LTC Properties', price: 33.50, dividendYield: 6.8, dividendGrowth: 0.5, priceGrowth: 1.0, payoutFrequency: 12 },
  'EPR': { symbol: 'EPR', name: 'EPR Properties', price: 42.00, dividendYield: 7.8, dividendGrowth: 1.5, priceGrowth: -1.0, payoutFrequency: 12 },
  'ADC': { symbol: 'ADC', name: 'Agree Realty', price: 61.00, dividendYield: 4.8, dividendGrowth: 5.5, priceGrowth: 6.0, payoutFrequency: 12 },

  // --- QUARTALSZAHLER (Quarterly) - USA ---
  'MSFT': { symbol: 'MSFT', name: 'Microsoft Corp.', price: 405.00, dividendYield: 0.7, dividendGrowth: 10.2, priceGrowth: 15.0, payoutFrequency: 4 },
  'AAPL': { symbol: 'AAPL', name: 'Apple Inc.', price: 175.00, dividendYield: 0.5, dividendGrowth: 5.8, priceGrowth: 12.0, payoutFrequency: 4 },
  'JNJ': { symbol: 'JNJ', name: 'Johnson & Johnson', price: 148.00, dividendYield: 3.2, dividendGrowth: 5.4, priceGrowth: 3.0, payoutFrequency: 4 },
  'KO': { symbol: 'KO', name: 'Coca-Cola', price: 59.50, dividendYield: 3.3, dividendGrowth: 4.5, priceGrowth: 4.0, payoutFrequency: 4 },
  'PEP': { symbol: 'PEP', name: 'PepsiCo', price: 168.00, dividendYield: 3.1, dividendGrowth: 7.2, priceGrowth: 6.0, payoutFrequency: 4 },
  'PG': { symbol: 'PG', name: 'Procter & Gamble', price: 162.00, dividendYield: 2.4, dividendGrowth: 5.1, priceGrowth: 5.5, payoutFrequency: 4 },
  'MCD': { symbol: 'MCD', name: 'McDonald\'s', price: 275.00, dividendYield: 2.4, dividendGrowth: 8.0, priceGrowth: 7.0, payoutFrequency: 4 },
  'SBUX': { symbol: 'SBUX', name: 'Starbucks', price: 92.00, dividendYield: 2.5, dividendGrowth: 9.0, priceGrowth: 8.0, payoutFrequency: 4 },
  'HD': { symbol: 'HD', name: 'Home Depot', price: 360.00, dividendYield: 2.6, dividendGrowth: 12.0, priceGrowth: 9.0, payoutFrequency: 4 },
  'LOW': { symbol: 'LOW', name: 'Lowe\'s', price: 235.00, dividendYield: 1.8, dividendGrowth: 15.0, priceGrowth: 10.0, payoutFrequency: 4 },
  'AVGO': { symbol: 'AVGO', name: 'Broadcom', price: 1250.00, dividendYield: 1.6, dividendGrowth: 12.0, priceGrowth: 20.0, payoutFrequency: 4 },
  'CSCO': { symbol: 'CSCO', name: 'Cisco Systems', price: 48.00, dividendYield: 3.3, dividendGrowth: 2.8, priceGrowth: 3.0, payoutFrequency: 4 },
  'PFE': { symbol: 'PFE', name: 'Pfizer', price: 28.00, dividendYield: 6.0, dividendGrowth: 2.5, priceGrowth: -2.0, payoutFrequency: 4 },
  'ABBV': { symbol: 'ABBV', name: 'AbbVie', price: 175.00, dividendYield: 3.5, dividendGrowth: 6.5, priceGrowth: 8.0, payoutFrequency: 4 },
  'MMM': { symbol: 'MMM', name: '3M Company', price: 95.00, dividendYield: 6.2, dividendGrowth: 0.5, priceGrowth: -4.0, payoutFrequency: 4 },
  'T': { symbol: 'T', name: 'AT&T', price: 17.20, dividendYield: 6.4, dividendGrowth: 0.0, priceGrowth: 1.0, payoutFrequency: 4 },
  'VZ': { symbol: 'VZ', name: 'Verizon', price: 40.50, dividendYield: 6.6, dividendGrowth: 1.9, priceGrowth: 0.5, payoutFrequency: 4 },
  'XOM': { symbol: 'XOM', name: 'Exxon Mobil', price: 115.00, dividendYield: 3.3, dividendGrowth: 3.5, priceGrowth: 6.0, payoutFrequency: 4 },
  'CVX': { symbol: 'CVX', name: 'Chevron', price: 155.00, dividendYield: 4.2, dividendGrowth: 6.0, priceGrowth: 4.0, payoutFrequency: 4 },
  'V': { symbol: 'V', name: 'Visa', price: 280.00, dividendYield: 0.7, dividendGrowth: 15.0, priceGrowth: 12.0, payoutFrequency: 4 },
  'MA': { symbol: 'MA', name: 'Mastercard', price: 460.00, dividendYield: 0.6, dividendGrowth: 16.0, priceGrowth: 13.0, payoutFrequency: 4 },

  // --- JAHRESZAHLER (Deutschland/Europa) ---
  'ALV.DE': { symbol: 'ALV.DE', name: 'Allianz SE', price: 285.00, dividendYield: 5.0, dividendGrowth: 5.8, priceGrowth: 6.5, payoutFrequency: 1 },
  'BAS.DE': { symbol: 'BAS.DE', name: 'BASF SE', price: 48.00, dividendYield: 7.1, dividendGrowth: 1.0, priceGrowth: 0.0, payoutFrequency: 1 },
  'MUV2.DE': { symbol: 'MUV2.DE', name: 'Münchener Rück', price: 470.00, dividendYield: 3.2, dividendGrowth: 5.0, priceGrowth: 8.0, payoutFrequency: 1 },
  'BMW.DE': { symbol: 'BMW.DE', name: 'BMW AG', price: 105.00, dividendYield: 5.8, dividendGrowth: 9.0, priceGrowth: 3.0, payoutFrequency: 1 },
  'DTE.DE': { symbol: 'DTE.DE', name: 'Deutsche Telekom', price: 22.50, dividendYield: 3.4, dividendGrowth: 4.0, priceGrowth: 5.0, payoutFrequency: 1 },
  'DHL.DE': { symbol: 'DHL.DE', name: 'DHL Group', price: 39.00, dividendYield: 4.7, dividendGrowth: 3.5, priceGrowth: 3.0, payoutFrequency: 1 },
  'SIE.DE': { symbol: 'SIE.DE', name: 'Siemens AG', price: 180.00, dividendYield: 2.6, dividendGrowth: 6.0, priceGrowth: 9.0, payoutFrequency: 1 },
  'SAP.DE': { symbol: 'SAP.DE', name: 'SAP SE', price: 175.00, dividendYield: 1.2, dividendGrowth: 5.0, priceGrowth: 12.0, payoutFrequency: 1 },
  'VNA.DE': { symbol: 'VNA.DE', name: 'Vonovia SE', price: 27.50, dividendYield: 3.3, dividendGrowth: 2.0, priceGrowth: 2.0, payoutFrequency: 1 },
  'MBG.DE': { symbol: 'MBG.DE', name: 'Mercedes-Benz', price: 72.00, dividendYield: 7.0, dividendGrowth: 3.0, priceGrowth: 2.0, payoutFrequency: 1 },

  // --- INTERNATIONALE ---
  'NESN.SW': { symbol: 'NESN.SW', name: 'Nestlé', price: 95.00, dividendYield: 3.1, dividendGrowth: 2.5, priceGrowth: 2.0, payoutFrequency: 1 },
  'ROG.SW': { symbol: 'ROG.SW', name: 'Roche', price: 230.00, dividendYield: 3.9, dividendGrowth: 3.0, priceGrowth: 1.0, payoutFrequency: 1 },
  'NOVN.SW': { symbol: 'NOVN.SW', name: 'Novartis', price: 90.00, dividendYield: 3.6, dividendGrowth: 3.5, priceGrowth: 3.0, payoutFrequency: 1 },
  'SHEL': { symbol: 'SHEL', name: 'Shell', price: 33.00, dividendYield: 3.8, dividendGrowth: 4.0, priceGrowth: 5.0, payoutFrequency: 4 },
  'ASML': { symbol: 'ASML', name: 'ASML Holding', price: 900.00, dividendYield: 0.7, dividendGrowth: 20.0, priceGrowth: 18.0, payoutFrequency: 4 }, // often pays quarterly now
};

export const getMarketData = (tickerInput: string): StockData | null => {
  if (!tickerInput) return null;
  
  const cleanTicker = tickerInput.trim().toUpperCase();
  
  // 1. Direct Match
  if (MARKET_DB[cleanTicker]) {
    return MARKET_DB[cleanTicker];
  }

  // 2. Partial Match (e.g. input "Allianz" -> matches "ALV.DE")
  const foundKey = Object.keys(MARKET_DB).find(k => {
    const stock = MARKET_DB[k];
    return stock.symbol.includes(cleanTicker) || stock.name.toUpperCase().includes(cleanTicker);
  });

  if (foundKey) {
    return MARKET_DB[foundKey];
  }

  // 3. Fallback: Return a generic template if not found so user can edit manually
  // This allows the app to work for ANY stock, even if not in DB
  return null;
};