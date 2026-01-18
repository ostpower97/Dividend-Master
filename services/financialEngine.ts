import { PortfolioItem, UserSettings, YearProjection } from '../types';

const TAX_RATE = 0.26375; // 25% Abgeltung + 5.5% Soli
const PROJECTION_YEARS = 30;

export const calculateProjections = (
  initialPortfolio: PortfolioItem[],
  settings: UserSettings
): YearProjection[] => {
  const projections: YearProjection[] = [];

  // 1. Prepare Simulation State
  // We need to track the current state of each stock (shares, price, div/share) through months
  let simStocks = initialPortfolio.map(p => ({
    ...p,
    currentPrice: p.currentPrice || 100,
    // Annual Dividend per Share
    currentAnnualDivPerShare: (p.currentPrice || 100) * ((p.dividendYield || 0) / 100),
    dividendGrowth: p.dividendGrowth || 0,
    priceGrowth: p.priceGrowth !== undefined ? p.priceGrowth : (p.dividendGrowth || 0),
    monthlyContribution: p.monthlyContribution || 0,
    shares: p.shares, // This will mutate
    payoutFrequency: p.payoutFrequency || 1 // Default to annual if missing
  }));

  const totalMonths = PROJECTION_YEARS * 12;

  // Trackers for current year aggregation
  let currentYear = 1;
  let yearGrossAccumulator = 0;
  let yearTaxAccumulator = 0;
  let yearNetAccumulator = 0;
  let yearTickerGross: Record<string, number> = {};
  let remainingPauschbetrag = settings.pauschbetrag;

  // Initialize breakdown map
  simStocks.forEach(s => yearTickerGross[s.symbol] = 0);

  // --- MONTHLY SIMULATION LOOP ---
  for (let m = 1; m <= totalMonths; m++) {
    
    // A. Handle New Year (Reset Tax Free Allowance, Apply Annual Growth stats)
    if ((m - 1) % 12 === 0 && m > 1) {
      // It's January of a new year
      currentYear++;
      remainingPauschbetrag = settings.pauschbetrag; // Reset Freibetrag

      // Apply Annual Growth to Fundamentals (Price & Dividend)
      simStocks.forEach(stock => {
        stock.currentAnnualDivPerShare *= (1 + (stock.dividendGrowth / 100));
        // Note: Price usually moves daily, but for projection we can stick to annual jumps 
        // OR monthly compounding. Let's do annual jumps for fundamentals to keep inputs consistent with CAGR.
        // However, specifically for savings plans, monthly price adjustments are smoother.
        // Let's stick to annual Step-Up for simplicity and robustness of 'Yearly Growth' inputs.
        stock.currentPrice *= (1 + (stock.priceGrowth / 100));
      });
    }

    // B. Process Monthly Logic for each Stock
    simStocks.forEach(stock => {
      
      // 1. Monthly Savings Plan (Sparplan) -> Happens BEFORE Dividend (usually) or doesn't matter much
      if (stock.monthlyContribution > 0) {
        const sharesBought = stock.monthlyContribution / stock.currentPrice;
        stock.shares += sharesBought;
      }

      // 2. Dividend Payout Check
      // We need to determine if this stock pays in this month 'm'.
      // Frequency 12 = Every month.
      // Frequency 4  = Every 3rd month.
      // Frequency 1  = Once a year (Let's assume Month 6 for distribution).
      
      let paysThisMonth = false;
      if (stock.payoutFrequency === 12) {
        paysThisMonth = true;
      } else if (stock.payoutFrequency === 4) {
        // Pays in 3, 6, 9, 12 relative to year start
        paysThisMonth = m % 3 === 0; 
      } else if (stock.payoutFrequency === 1) {
        // Pays once. Let's assume mid-year (Month 6 of the year)
        paysThisMonth = (m % 12) === 6;
      } else if (stock.payoutFrequency === 2) {
        // Semi-annual: 6, 12
        paysThisMonth = m % 6 === 0;
      }

      if (paysThisMonth) {
        // Calculate Payout Amount
        // Dividend per payout = Annual / Frequency
        const divPerShareThisPayout = stock.currentAnnualDivPerShare / stock.payoutFrequency;
        const grossPayout = stock.shares * divPerShareThisPayout;

        if (grossPayout > 0) {
          // Tax Calculation (Atomic per payout)
          let tax = 0;
          let net = grossPayout;

          if (grossPayout > remainingPauschbetrag) {
             const taxable = grossPayout - remainingPauschbetrag;
             tax = taxable * TAX_RATE;
             remainingPauschbetrag = 0;
          } else {
             remainingPauschbetrag -= grossPayout;
             tax = 0;
          }
          net = grossPayout - tax;

          // Reinvestment (DRIP) - Immediately buy shares
          if (stock.reinvest) {
            const dripShares = net / stock.currentPrice;
            stock.shares += dripShares;
          }

          // Accumulate for Yearly Reporting
          yearGrossAccumulator += grossPayout;
          yearTaxAccumulator += tax;
          yearNetAccumulator += net;
          yearTickerGross[stock.symbol] = (yearTickerGross[stock.symbol] || 0) + grossPayout; // Store gross, we scale to net in report
        }
      }
    });

    // C. End of Year Aggregation -> Push to Projections
    if (m % 12 === 0) {
      // Calculate effective tax rate for the breakdown visualization
      const effectiveTaxRate = yearGrossAccumulator > 0 ? yearTaxAccumulator / yearGrossAccumulator : 0;
      
      const breakdownNet: Record<string, number> = {};
      Object.keys(yearTickerGross).forEach(sym => {
        breakdownNet[sym] = yearTickerGross[sym] * (1 - effectiveTaxRate);
      });

      const currentShareCounts: Record<string, number> = {};
      simStocks.forEach(s => currentShareCounts[s.symbol] = s.shares);

      const totalVal = simStocks.reduce((sum, s) => sum + (s.shares * s.currentPrice), 0);

      projections.push({
        year: m / 12,
        grossDividend: yearGrossAccumulator,
        netDividend: yearNetAccumulator,
        taxPaid: yearTaxAccumulator,
        totalPortfolioValue: totalVal,
        tickerBreakdown: breakdownNet,
        accumulatedShares: currentShareCounts
      });

      // Reset Accumulators for next year
      yearGrossAccumulator = 0;
      yearTaxAccumulator = 0;
      yearNetAccumulator = 0;
      simStocks.forEach(s => yearTickerGross[s.symbol] = 0);
    }
  }

  return projections;
};