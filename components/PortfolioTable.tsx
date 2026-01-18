import React from 'react';
import { PortfolioItem } from '../types';

interface Props {
  portfolio: PortfolioItem[];
  setPortfolio: (p: PortfolioItem[]) => void;
}

export const PortfolioTable: React.FC<Props> = ({ portfolio, setPortfolio }) => {
  
  const updateItem = (id: string, field: keyof PortfolioItem, value: any) => {
    setPortfolio(portfolio.map(p => {
      if (p.id !== id) return p;
      return { ...p, [field]: value };
    }));
  };

  const removeItem = (id: string) => {
    if (window.confirm("Position wirklich löschen?")) {
      setPortfolio(portfolio.filter(p => p.id !== id));
    }
  };

  if (portfolio.length === 0) {
    return (
      <div className="bg-slate-800/50 border border-dashed border-slate-600 rounded-xl p-8 text-center text-slate-400">
        <p>Dein Portfolio ist leer. Füge oben eine Aktie hinzu!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-end">
        <h2 className="text-xl font-bold text-white">Dein Portfolio</h2>
        <span className="text-sm text-slate-400">{portfolio.length} Positionen</span>
      </div>

      {/* --- DESKTOP TABLE VIEW (Hidden on Mobile) --- */}
      <div className="hidden md:block bg-slate-800 rounded-xl shadow-lg border border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900 text-xs uppercase text-slate-400 font-bold tracking-wider">
              <tr>
                <th className="px-4 py-4">Ticker</th>
                <th className="px-4 py-4 w-20">Stück</th>
                <th className="px-4 py-4 w-24">Kurs €</th>
                <th className="px-4 py-4 w-20">Div.%</th>
                <th className="px-4 py-4 w-20" title="Dividendenwachstum">D-CAGR</th>
                <th className="px-4 py-4 w-20" title="Kurswachstum">K-CAGR</th>
                <th className="px-4 py-4 w-24">Spar €</th>
                <th className="px-4 py-4 w-24">Zyklus</th>
                <th className="px-4 py-4 text-center">Reinvest</th>
                <th className="px-4 py-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {portfolio.map((item) => (
                <tr key={item.id} className="hover:bg-slate-700/50 transition-colors">
                  {/* Ticker */}
                  <td className="px-4 py-3">
                    <div className="font-bold text-white">{item.symbol}</div>
                    <div className="text-xs text-slate-500 truncate max-w-[120px]">{item.name}</div>
                  </td>

                  {/* Shares */}
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      value={item.shares}
                      onChange={(e) => updateItem(item.id, 'shares', parseFloat(e.target.value))}
                      className="w-full bg-transparent border-b border-transparent hover:border-slate-500 focus:border-teal-500 text-right focus:outline-none transition-colors"
                    />
                  </td>

                  {/* Price */}
                  <td className="px-4 py-3">
                     <input
                      type="number"
                      value={item.currentPrice}
                      onChange={(e) => updateItem(item.id, 'currentPrice', parseFloat(e.target.value))}
                      className="w-full bg-transparent border-b border-transparent hover:border-slate-500 focus:border-teal-500 text-right text-teal-300 focus:outline-none transition-colors"
                    />
                  </td>

                  {/* Yield */}
                  <td className="px-4 py-3">
                     <input
                      type="number"
                      value={item.dividendYield}
                      onChange={(e) => updateItem(item.id, 'dividendYield', parseFloat(e.target.value))}
                      className="w-full bg-transparent border-b border-transparent hover:border-slate-500 focus:border-teal-500 text-right text-orange-300 focus:outline-none transition-colors"
                    />
                  </td>

                  {/* Div Growth */}
                  <td className="px-4 py-3">
                     <input
                      type="number"
                      value={item.dividendGrowth}
                      onChange={(e) => updateItem(item.id, 'dividendGrowth', parseFloat(e.target.value))}
                      className="w-full bg-transparent border-b border-transparent hover:border-slate-500 focus:border-teal-500 text-right text-purple-300 focus:outline-none transition-colors"
                    />
                  </td>

                  {/* Price Growth */}
                  <td className="px-4 py-3">
                     <input
                      type="number"
                      value={item.priceGrowth}
                      onChange={(e) => updateItem(item.id, 'priceGrowth', parseFloat(e.target.value))}
                      className="w-full bg-transparent border-b border-transparent hover:border-slate-500 focus:border-teal-500 text-right text-indigo-300 focus:outline-none transition-colors"
                    />
                  </td>

                  {/* Monthly Contribution */}
                  <td className="px-4 py-3">
                     <input
                      type="number"
                      value={item.monthlyContribution}
                      onChange={(e) => updateItem(item.id, 'monthlyContribution', parseFloat(e.target.value))}
                      className="w-full bg-slate-900/50 border border-slate-600 rounded px-2 py-1 text-right text-blue-300 focus:border-teal-500 focus:outline-none transition-colors"
                    />
                  </td>

                  {/* Frequency */}
                  <td className="px-4 py-3">
                     <select
                      value={item.payoutFrequency}
                      onChange={(e) => updateItem(item.id, 'payoutFrequency', parseInt(e.target.value))}
                      className="w-full bg-transparent text-xs text-slate-300 focus:outline-none cursor-pointer"
                     >
                       <option value={1}>1x / Jahr</option>
                       <option value={2}>2x / Jahr</option>
                       <option value={4}>4x / Jahr</option>
                       <option value={12}>12x / Jahr</option>
                     </select>
                  </td>

                  {/* Reinvest */}
                  <td className="px-4 py-3 text-center">
                    <input
                      type="checkbox"
                      checked={item.reinvest}
                      onChange={(e) => updateItem(item.id, 'reinvest', e.target.checked)}
                      className="w-4 h-4 text-teal-600 bg-slate-700 border-slate-600 rounded focus:ring-teal-500 cursor-pointer"
                    />
                  </td>

                  {/* Delete */}
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => removeItem(item.id)} className="text-slate-500 hover:text-red-400 transition-colors p-1">
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- MOBILE CARD VIEW (Visible on Mobile) --- */}
      <div className="md:hidden grid grid-cols-1 gap-4">
        {portfolio.map((item) => (
          <div key={item.id} className="bg-slate-800 border border-slate-700 rounded-xl p-4 shadow-sm relative">
             <div className="flex justify-between items-start mb-4 border-b border-slate-700 pb-2">
                <div>
                   <h3 className="text-lg font-bold text-white">{item.symbol}</h3>
                   <p className="text-xs text-slate-400">{item.name}</p>
                </div>
                <button onClick={() => removeItem(item.id)} className="text-slate-500 hover:text-red-400">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
             </div>
             
             <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                
                {/* Row 1: Amount & Price */}
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Anzahl</label>
                  <input 
                     type="number" 
                     value={item.shares} 
                     onChange={(e) => updateItem(item.id, 'shares', parseFloat(e.target.value))}
                     className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white" 
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Kurs (€)</label>
                  <input 
                     type="number" 
                     value={item.currentPrice} 
                     onChange={(e) => updateItem(item.id, 'currentPrice', parseFloat(e.target.value))}
                     className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-teal-400 font-medium" 
                  />
                </div>

                {/* Row 2: Yield & Savings */}
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Div. Rendite %</label>
                  <input 
                     type="number" 
                     value={item.dividendYield} 
                     onChange={(e) => updateItem(item.id, 'dividendYield', parseFloat(e.target.value))}
                     className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-orange-300" 
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Sparrate €/Mt</label>
                  <input 
                     type="number" 
                     value={item.monthlyContribution} 
                     onChange={(e) => updateItem(item.id, 'monthlyContribution', parseFloat(e.target.value))}
                     className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-blue-300" 
                  />
                </div>

                {/* Row 3: Growth Rates */}
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Div. Wachs. %</label>
                  <input 
                     type="number" 
                     value={item.dividendGrowth} 
                     onChange={(e) => updateItem(item.id, 'dividendGrowth', parseFloat(e.target.value))}
                     className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-purple-300" 
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Kurs Wachs. %</label>
                  <input 
                     type="number" 
                     value={item.priceGrowth} 
                     onChange={(e) => updateItem(item.id, 'priceGrowth', parseFloat(e.target.value))}
                     className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-indigo-300" 
                  />
                </div>

             </div>
             
             <div className="mt-4 pt-3 border-t border-slate-700 flex justify-between items-center">
                <div className="flex items-center gap-2">
                   <input
                      type="checkbox"
                      id={`reinvest-${item.id}`}
                      checked={item.reinvest}
                      onChange={(e) => updateItem(item.id, 'reinvest', e.target.checked)}
                      className="w-4 h-4 text-teal-600 bg-slate-900 border-slate-600 rounded"
                   />
                   <label htmlFor={`reinvest-${item.id}`} className="text-xs text-slate-300">Reinvestieren?</label>
                </div>
                
                <select
                  value={item.payoutFrequency}
                  onChange={(e) => updateItem(item.id, 'payoutFrequency', parseInt(e.target.value))}
                  className="bg-slate-900 border border-slate-700 text-xs rounded px-2 py-1 text-slate-300 outline-none"
                 >
                   <option value={1}>Jährlich</option>
                   <option value={4}>Quartalsweise</option>
                   <option value={12}>Monatlich</option>
                 </select>
             </div>
          </div>
        ))}
      </div>
    </div>
  );
};
