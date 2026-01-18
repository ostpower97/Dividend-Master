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
    if (window.confirm("Position entfernen?")) {
      setPortfolio(portfolio.filter(p => p.id !== id));
    }
  };

  if (portfolio.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-slate-800 rounded-2xl bg-slate-900/50">
        <div className="text-4xl mb-4 opacity-50">🌱</div>
        <p className="text-slate-400 font-medium">Dein Portfolio ist leer.</p>
        <p className="text-slate-600 text-sm mt-1">Füge oben die erste Aktie hinzu.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* --- DESKTOP TABLE (Hidden on Mobile) --- */}
      <div className="hidden md:block bg-slate-900 rounded-2xl shadow-xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-xs uppercase text-slate-500 font-bold tracking-wider">
              <tr>
                <th className="px-5 py-4">Asset</th>
                <th className="px-4 py-4 w-24 text-right">Anzahl</th>
                <th className="px-4 py-4 w-28 text-right">Kurs €</th>
                <th className="px-4 py-4 w-24 text-right">Div.%</th>
                <th className="px-4 py-4 w-24 text-right">D-CAGR</th>
                <th className="px-4 py-4 w-24 text-right">K-CAGR</th>
                <th className="px-4 py-4 w-28 text-right">Sparplan</th>
                <th className="px-4 py-4 w-32">Zyklus</th>
                <th className="px-4 py-4 text-center">Reinvest</th>
                <th className="px-4 py-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {portfolio.map((item) => (
                <tr key={item.id} className="group hover:bg-slate-800/50 transition-colors">
                  <td className="px-5 py-4">
                    <div className="font-bold text-white text-base">{item.symbol}</div>
                    <div className="text-xs text-slate-500 truncate max-w-[140px]">{item.name}</div>
                  </td>
                  <td className="px-4 py-4">
                    <input type="number" value={item.shares} onChange={(e) => updateItem(item.id, 'shares', parseFloat(e.target.value))} className="w-full bg-transparent border-b border-slate-800 hover:border-slate-500 focus:border-teal-500 text-right focus:outline-none transition-colors py-1" />
                  </td>
                  <td className="px-4 py-4">
                     <input type="number" value={item.currentPrice} onChange={(e) => updateItem(item.id, 'currentPrice', parseFloat(e.target.value))} className="w-full bg-transparent border-b border-slate-800 hover:border-slate-500 focus:border-teal-500 text-right text-white focus:outline-none transition-colors py-1" />
                  </td>
                  <td className="px-4 py-4">
                     <input type="number" value={item.dividendYield} onChange={(e) => updateItem(item.id, 'dividendYield', parseFloat(e.target.value))} className="w-full bg-transparent border-b border-slate-800 hover:border-slate-500 focus:border-teal-500 text-right text-orange-400 focus:outline-none transition-colors py-1" />
                  </td>
                  <td className="px-4 py-4">
                     <input type="number" value={item.dividendGrowth} onChange={(e) => updateItem(item.id, 'dividendGrowth', parseFloat(e.target.value))} className="w-full bg-transparent border-b border-slate-800 hover:border-slate-500 focus:border-teal-500 text-right text-purple-400 focus:outline-none transition-colors py-1" />
                  </td>
                  <td className="px-4 py-4">
                     <input type="number" value={item.priceGrowth} onChange={(e) => updateItem(item.id, 'priceGrowth', parseFloat(e.target.value))} className="w-full bg-transparent border-b border-slate-800 hover:border-slate-500 focus:border-teal-500 text-right text-indigo-400 focus:outline-none transition-colors py-1" />
                  </td>
                  <td className="px-4 py-4">
                     <input type="number" value={item.monthlyContribution} onChange={(e) => updateItem(item.id, 'monthlyContribution', parseFloat(e.target.value))} className="w-full bg-slate-800 rounded border border-transparent focus:border-teal-500 text-right text-blue-300 focus:outline-none transition-colors px-2 py-1" />
                  </td>
                  <td className="px-4 py-4">
                     <select value={item.payoutFrequency} onChange={(e) => updateItem(item.id, 'payoutFrequency', parseInt(e.target.value))} className="w-full bg-transparent text-xs text-slate-400 focus:text-white focus:outline-none cursor-pointer">
                       <option value={1}>Jährlich</option>
                       <option value={2}>Halbjährlich</option>
                       <option value={4}>Quartalsweise</option>
                       <option value={12}>Monatlich</option>
                     </select>
                  </td>
                  <td className="px-4 py-4 text-center">
                    <input type="checkbox" checked={item.reinvest} onChange={(e) => updateItem(item.id, 'reinvest', e.target.checked)} className="w-5 h-5 accent-teal-500 cursor-pointer rounded bg-slate-700 border-none" />
                  </td>
                  <td className="px-4 py-4 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => removeItem(item.id)} className="text-slate-600 hover:text-red-500 p-2">✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- MOBILE CARDS (Visible on Mobile) --- */}
      <div className="md:hidden grid grid-cols-1 gap-4">
        {portfolio.map((item) => (
          <div key={item.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
             
             {/* Header */}
             <div className="flex justify-between items-start mb-5">
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-sm font-bold text-white border border-slate-700">
                     {item.symbol.substring(0,2)}
                   </div>
                   <div>
                     <h3 className="text-lg font-bold text-white leading-none">{item.symbol}</h3>
                     <p className="text-xs text-slate-500 mt-1 truncate w-40">{item.name}</p>
                   </div>
                </div>
                <button onClick={() => removeItem(item.id)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-800 text-slate-500 hover:bg-red-500/10 hover:text-red-500 transition-colors">
                  ✕
                </button>
             </div>
             
             {/* Main Inputs Grid */}
             <div className="grid grid-cols-2 gap-4 mb-5">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Anteile (Stk.)</label>
                  <input 
                    type="number" 
                    value={item.shares} 
                    onChange={(e) => updateItem(item.id, 'shares', parseFloat(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white font-medium focus:border-teal-500 outline-none transition-colors"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Kurs (€)</label>
                  <input 
                    type="number" 
                    value={item.currentPrice} 
                    onChange={(e) => updateItem(item.id, 'currentPrice', parseFloat(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white font-medium focus:border-teal-500 outline-none transition-colors"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] uppercase tracking-wider text-orange-400/80 font-bold">Div. Rendite %</label>
                  <input 
                    type="number" 
                    value={item.dividendYield} 
                    onChange={(e) => updateItem(item.id, 'dividendYield', parseFloat(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-orange-300 font-medium focus:border-orange-500 outline-none transition-colors"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] uppercase tracking-wider text-blue-400/80 font-bold">Sparrate €</label>
                  <input 
                    type="number" 
                    value={item.monthlyContribution} 
                    onChange={(e) => updateItem(item.id, 'monthlyContribution', parseFloat(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-blue-300 font-medium focus:border-blue-500 outline-none transition-colors"
                  />
                </div>
             </div>
             
             {/* Advanced Settings Expander (Growth & Freq) */}
             <div className="bg-slate-950/50 rounded-xl p-3 border border-slate-800/50">
                <div className="flex justify-between items-center mb-3">
                   <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        checked={item.reinvest}
                        onChange={(e) => updateItem(item.id, 'reinvest', e.target.checked)}
                        className="w-4 h-4 accent-teal-500 rounded cursor-pointer"
                      />
                      <label className="text-xs text-slate-300 font-medium">Dividenden reinvestieren</label>
                   </div>
                   <select 
                      value={item.payoutFrequency}
                      onChange={(e) => updateItem(item.id, 'payoutFrequency', parseInt(e.target.value))}
                      className="bg-slate-800 text-xs text-slate-300 border border-slate-700 rounded px-2 py-1 outline-none"
                   >
                      <option value={1}>1x Jahr</option>
                      <option value={4}>4x Jahr</option>
                      <option value={12}>12x Jahr</option>
                   </select>
                </div>
                
                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-800/50">
                   <div>
                     <span className="text-[10px] text-slate-500 block">Div-Wachstum</span>
                     <div className="flex items-center gap-1">
                        <input 
                          type="number" 
                          value={item.dividendGrowth} 
                          onChange={(e) => updateItem(item.id, 'dividendGrowth', parseFloat(e.target.value))}
                          className="w-full bg-transparent text-sm text-purple-300 font-medium outline-none border-b border-slate-800 focus:border-purple-500"
                        />
                        <span className="text-xs text-slate-600">%</span>
                     </div>
                   </div>
                   <div>
                     <span className="text-[10px] text-slate-500 block">Kurs-Wachstum</span>
                     <div className="flex items-center gap-1">
                        <input 
                          type="number" 
                          value={item.priceGrowth} 
                          onChange={(e) => updateItem(item.id, 'priceGrowth', parseFloat(e.target.value))}
                          className="w-full bg-transparent text-sm text-indigo-300 font-medium outline-none border-b border-slate-800 focus:border-indigo-500"
                        />
                        <span className="text-xs text-slate-600">%</span>
                     </div>
                   </div>
                </div>
             </div>

          </div>
        ))}
      </div>
    </div>
  );
};
