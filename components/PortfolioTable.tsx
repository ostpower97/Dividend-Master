import React, { useState } from 'react';
import { PortfolioItem } from '../types';
import { getMarketData } from '../services/marketData';

interface Props {
  portfolio: PortfolioItem[];
  setPortfolio: (p: PortfolioItem[]) => void;
}

export const PortfolioTable: React.FC<Props> = ({ portfolio, setPortfolio }) => {
  
  const handleAdd = () => {
    const newItem: PortfolioItem = {
      id: Date.now().toString(),
      symbol: '',
      name: '',
      shares: 0,
      buyPrice: 0,
      reinvest: true,
      currentPrice: 0,
      dividendYield: 0,
      dividendGrowth: 0,
      priceGrowth: 0,
      monthlyContribution: 0,
      payoutFrequency: 1 
    };
    setPortfolio([...portfolio, newItem]);
  };

  const updateItem = (id: string, field: keyof PortfolioItem, value: any) => {
    setPortfolio(portfolio.map(p => {
      if (p.id !== id) return p;
      return { ...p, [field]: value };
    }));
  };

  const removeItem = (id: string) => {
    setPortfolio(portfolio.filter(p => p.id !== id));
  };

  const handleLookup = (id: string, ticker: string) => {
    if (!ticker) return;
    
    // Simulating async to feel like a "search"
    setTimeout(() => {
      const data = getMarketData(ticker);
      
      if (data) {
        setPortfolio(portfolio.map(p => {
          if (p.id !== id) return p;
          return {
            ...p,
            symbol: data.symbol || ticker, 
            name: data.name || '',
            currentPrice: data.price || 0,
            buyPrice: p.buyPrice === 0 ? (data.price || 0) : p.buyPrice,
            dividendYield: data.dividendYield || 0,
            dividendGrowth: data.dividendGrowth || 0,
            priceGrowth: data.priceGrowth || 0,
            payoutFrequency: data.payoutFrequency || 1
          };
        }));
      } else {
        // If not found, just uppercase the symbol and let user fill rest
        setPortfolio(portfolio.map(p => {
            if (p.id !== id) return p;
            return { ...p, symbol: ticker.toUpperCase(), name: 'Manuelle Eingabe' };
        }));
        alert(`Ticker '${ticker}' nicht in der Datenbank gefunden. Bitte Daten manuell eintragen.`);
      }
    }, 300);
  };

  return (
    <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 overflow-hidden">
      <div className="p-5 border-b border-gray-700 bg-gray-850 flex justify-between items-center">
        <div>
           <h2 className="text-xl font-bold text-white">Aktien-Portfolio</h2>
           <p className="text-sm text-gray-400 mt-1">Ticker eingeben (z.B. O, MSFT, ALV.DE) und Enter drücken. Datenbank enthält ~50 Top-Werte.</p>
        </div>
        <button 
          onClick={handleAdd}
          className="bg-teal-600 hover:bg-teal-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 shadow-lg"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
          </svg>
          Position hinzufügen
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-300">
          <thead className="bg-gray-900 text-xs uppercase text-gray-400 font-semibold tracking-wider">
            <tr>
              <th className="px-4 py-4">Ticker</th>
              <th className="px-4 py-4 w-16">Stück</th>
              <th className="px-4 py-4 w-20">Kurs €</th>
              <th className="px-4 py-4 w-16">Div.%</th>
              <th className="px-4 py-4 w-16">D.Wach%</th>
              <th className="px-4 py-4 w-16">K.Wach%</th>
              <th className="px-4 py-4 w-20">Spar €</th>
              <th className="px-4 py-4 w-24">Intervall</th>
              <th className="px-4 py-4 text-center">Reinv?</th>
              <th className="px-4 py-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {portfolio.map((item) => (
              <tr key={item.id} className="hover:bg-gray-750 transition-colors group">
                {/* Ticker & Lookup */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1 relative">
                    <input
                      type="text"
                      value={item.symbol}
                      onChange={(e) => updateItem(item.id, 'symbol', e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleLookup(item.id, item.symbol)}
                      placeholder="SYMBOL"
                      className="w-24 bg-transparent border border-gray-600 hover:border-gray-500 focus:border-teal-500 rounded px-2 py-1 text-white font-bold focus:outline-none focus:bg-gray-900 transition-all uppercase placeholder-gray-600"
                    />
                    <button 
                      onClick={() => handleLookup(item.id, item.symbol)} 
                      className="text-gray-500 hover:text-teal-400 p-1"
                      title="Suche in Datenbank"
                    >
                      <span>⚡</span>
                    </button>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 pl-1 truncate max-w-[120px] h-4">
                    {item.name || ''}
                  </div>
                </td>

                {/* Shares */}
                <td className="px-4 py-3">
                  <input
                    type="number"
                    value={item.shares || ''}
                    onChange={(e) => updateItem(item.id, 'shares', parseFloat(e.target.value))}
                    className="w-16 bg-transparent border border-transparent hover:border-gray-600 focus:border-teal-500 rounded px-2 py-1 text-right focus:outline-none focus:bg-gray-900 transition-all"
                    placeholder="0"
                  />
                </td>

                {/* Current Price */}
                <td className="px-4 py-3">
                   <input
                    type="number"
                    value={item.currentPrice || ''}
                    onChange={(e) => updateItem(item.id, 'currentPrice', parseFloat(e.target.value))}
                    className="w-20 bg-transparent border border-transparent hover:border-gray-600 focus:border-teal-500 rounded px-2 py-1 text-right text-teal-300 font-medium focus:outline-none focus:bg-gray-900 transition-all"
                  />
                </td>

                {/* Yield */}
                <td className="px-4 py-3">
                   <input
                    type="number"
                    value={item.dividendYield || ''}
                    onChange={(e) => updateItem(item.id, 'dividendYield', parseFloat(e.target.value))}
                    className="w-16 bg-transparent border border-transparent hover:border-gray-600 focus:border-teal-500 rounded px-2 py-1 text-right text-orange-300 focus:outline-none focus:bg-gray-900 transition-all"
                  />
                </td>

                {/* Div Growth */}
                <td className="px-4 py-3">
                   <input
                    type="number"
                    value={item.dividendGrowth || ''}
                    onChange={(e) => updateItem(item.id, 'dividendGrowth', parseFloat(e.target.value))}
                    className="w-16 bg-transparent border border-transparent hover:border-gray-600 focus:border-teal-500 rounded px-2 py-1 text-right text-purple-300 focus:outline-none focus:bg-gray-900 transition-all"
                  />
                </td>

                {/* Price Growth */}
                <td className="px-4 py-3">
                   <input
                    type="number"
                    value={item.priceGrowth || ''}
                    onChange={(e) => updateItem(item.id, 'priceGrowth', parseFloat(e.target.value))}
                    className="w-16 bg-transparent border border-transparent hover:border-gray-600 focus:border-teal-500 rounded px-2 py-1 text-right text-indigo-300 focus:outline-none focus:bg-gray-900 transition-all"
                  />
                </td>

                {/* Monthly Contribution */}
                <td className="px-4 py-3">
                   <input
                    type="number"
                    value={item.monthlyContribution || ''}
                    onChange={(e) => updateItem(item.id, 'monthlyContribution', parseFloat(e.target.value))}
                    className="w-20 bg-gray-900 border border-gray-600 focus:border-teal-500 rounded px-2 py-1 text-right text-blue-300 focus:outline-none transition-all shadow-inner placeholder-gray-700"
                    placeholder="€/Mt"
                  />
                </td>

                {/* Frequency Dropdown */}
                <td className="px-4 py-3">
                   <select
                    value={item.payoutFrequency || 1}
                    onChange={(e) => updateItem(item.id, 'payoutFrequency', parseInt(e.target.value))}
                    className="bg-gray-900 border border-gray-600 text-xs rounded px-1 py-1 text-gray-300 focus:outline-none hover:border-gray-500 transition-colors"
                   >
                     <option value={1}>Jährlich (1)</option>
                     <option value={2}>Halbjah. (2)</option>
                     <option value={4}>Quartal (4)</option>
                     <option value={12}>Monatlich (12)</option>
                   </select>
                </td>

                {/* Reinvest */}
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    checked={item.reinvest}
                    onChange={(e) => updateItem(item.id, 'reinvest', e.target.checked)}
                    className="w-5 h-5 text-teal-600 bg-gray-700 border-gray-600 rounded focus:ring-teal-500 cursor-pointer"
                  />
                </td>

                {/* Delete */}
                <td className="px-4 py-3 text-right">
                  <button onClick={() => removeItem(item.id)} className="text-gray-600 hover:text-red-400 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
            
            {portfolio.length === 0 && (
              <tr>
                <td colSpan={10} className="px-4 py-8 text-center text-gray-500">
                  Noch keine Aktien im Portfolio. Fügen Sie eine Position hinzu oder nutzen Sie die Suche (z.B. "MSFT").
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};