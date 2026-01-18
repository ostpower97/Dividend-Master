import React, { useMemo, useState } from 'react';
import { YearProjection, PortfolioItem } from '../types';

interface Props {
  projections: YearProjection[];
  portfolio: PortfolioItem[];
  pauschbetrag: number;
}

const formatEuro = (val: number) => 
  new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(val);

const formatCompact = (val: number) => {
  if (val >= 1000000) return (val / 1000000).toFixed(1) + 'M';
  if (val >= 1000) return (val / 1000).toFixed(1) + 'k';
  return val.toFixed(0);
};

export const Dashboard: React.FC<Props> = ({ projections }) => {
  const [selectedYear, setSelectedYear] = useState<number>(1);

  const currentYearData = useMemo(() => {
    return projections.find(p => p.year === selectedYear) || projections[0];
  }, [projections, selectedYear]);

  if (!projections.length) return null;

  return (
    <div className="space-y-12 py-8">
      
      {/* Year Selection Slider */}
      <div className="bg-gray-800 p-8 rounded-2xl border border-gray-700 shadow-xl max-w-4xl mx-auto">
        <div className="flex flex-col items-center gap-6">
           <div className="text-center">
              <h3 className="text-2xl font-bold text-white mb-1">
                 Zeitraum-Auswahl
              </h3>
              <p className="text-gray-400">Prognose für Jahr <span className="text-teal-400 font-bold text-xl ml-1">{selectedYear}</span></p>
           </div>
           
           <div className="w-full px-4">
              <input 
                type="range" 
                min={projections[0]?.year || 1} 
                max={projections[projections.length - 1]?.year || 30} 
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="w-full h-3 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-teal-500 hover:accent-teal-400 transition-all"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-2 font-medium">
                <span>Start (Jahr 1)</span>
                <span>Jahr {Math.floor(projections.length / 2)}</span>
                <span>Ende (Jahr {projections.length})</span>
              </div>
           </div>
        </div>
      </div>

      {/* KPI TILES GRID */}
      {currentYearData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          
          {/* Tile 1: Monthly Average */}
          <div className="bg-gray-800 border border-gray-700 rounded-2xl p-8 flex flex-col items-center justify-center relative overflow-hidden group shadow-lg hover:shadow-2xl transition-all hover:scale-105">
             <div className="absolute top-0 left-0 w-2 h-full bg-teal-500"></div>
             <span className="text-gray-400 text-sm uppercase tracking-widest font-bold mb-3">Ø Monatlich (Netto)</span>
             <span className="text-4xl md:text-5xl font-extrabold text-teal-400 tracking-tight">
               {formatEuro(currentYearData.netDividend / 12)}
             </span>
             <span className="text-sm text-teal-500/60 mt-2 font-medium">Verfügbarer Cashflow</span>
          </div>

          {/* Tile 2: Annual Total */}
          <div className="bg-gray-800 border border-gray-700 rounded-2xl p-8 flex flex-col items-center justify-center shadow-lg hover:shadow-2xl transition-all hover:scale-105">
             <span className="text-gray-400 text-sm uppercase tracking-widest font-bold mb-3">Jahressumme (Netto)</span>
             <span className="text-4xl md:text-5xl font-extrabold text-white tracking-tight">
               {formatEuro(currentYearData.netDividend)}
             </span>
             <span className="text-sm text-gray-500 mt-2">Nach Steuern</span>
          </div>

          {/* Tile 3: Portfolio Value */}
          <div className="bg-gray-800 border border-gray-700 rounded-2xl p-8 flex flex-col items-center justify-center shadow-lg hover:shadow-2xl transition-all hover:scale-105">
             <span className="text-gray-400 text-sm uppercase tracking-widest font-bold mb-3">Portfolio Gesamtwert</span>
             <span className="text-4xl md:text-5xl font-extrabold text-blue-400 tracking-tight">
               {formatCompact(currentYearData.totalPortfolioValue)} €
             </span>
             <span className="text-sm text-gray-500 mt-2">Inkl. Reinvest & Sparpläne</span>
          </div>

        </div>
      )}

      <div className="text-center text-gray-500 text-sm pt-8 max-w-2xl mx-auto">
        Hinweis: Diese Simulation berechnet monatliche Zinseszinseffekte. Sparpläne werden monatlich ausgeführt. Dividenden werden gemäß ihrer Ausschüttungsfrequenz (Monatlich, Quartalsweise, Jährlich) sofort reinvestiert.
      </div>

    </div>
  );
};