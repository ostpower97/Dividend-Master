import React, { useState, useEffect } from 'react';
import { PortfolioItem, UserSettings, YearProjection } from './types';
import { PortfolioTable } from './components/PortfolioTable';
import { Dashboard } from './components/Dashboard';
import { calculateProjections } from './services/financialEngine';
import { getMarketData } from './services/marketData';

const DEFAULT_SETTINGS: UserSettings = {
  pauschbetrag: 1000,
  initialLumpSum: 0
};

const App: React.FC = () => {
  // Load initial state from LocalStorage if available
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>(() => {
    const saved = localStorage.getItem('dividend_portfolio');
    return saved ? JSON.parse(saved) : [];
  });
  
  const [settings, setSettings] = useState<UserSettings>(() => {
    const saved = localStorage.getItem('dividend_settings');
    return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
  });

  const [projections, setProjections] = useState<YearProjection[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [tickerInput, setTickerInput] = useState("");

  // Persistence Effects
  useEffect(() => {
    localStorage.setItem('dividend_portfolio', JSON.stringify(portfolio));
  }, [portfolio]);

  useEffect(() => {
    localStorage.setItem('dividend_settings', JSON.stringify(settings));
  }, [settings]);

  // Calculation Effect
  useEffect(() => {
    if (portfolio.length > 0) {
      const data = calculateProjections(portfolio, settings);
      setProjections(data);
    } else {
      setProjections([]);
    }
  }, [portfolio, settings]);

  const handleAddStock = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!tickerInput.trim()) return;

    const marketData = getMarketData(tickerInput);
    
    const newItem: PortfolioItem = {
      id: Date.now().toString(),
      symbol: marketData?.symbol || tickerInput.toUpperCase(),
      name: marketData?.name || 'Manuelle Position',
      shares: 0,
      buyPrice: marketData?.price || 0,
      currentPrice: marketData?.price || 0,
      dividendYield: marketData?.dividendYield || 0,
      dividendGrowth: marketData?.dividendGrowth || 2.5,
      priceGrowth: marketData?.priceGrowth || 5.0,
      payoutFrequency: marketData?.payoutFrequency || 1,
      reinvest: true,
      monthlyContribution: 0
    };

    setPortfolio([...portfolio, newItem]);
    setTickerInput("");
  };

  // File Import/Export
  const handleExport = () => {
    const dataStr = JSON.stringify({ portfolio, settings }, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `dividend_master_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        if (json.portfolio) setPortfolio(json.portfolio);
        if (json.settings) setSettings(json.settings);
      } catch (err) {
        alert('Fehler beim Laden der Datei. Falsches Format?');
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans pb-20">
      
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-20 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="text-2xl">📈</span>
            <h1 className="text-xl md:text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-blue-500">
              Dividend Master
            </h1>
          </div>
          <button 
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-slate-300"
            aria-label="Einstellungen"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
        
        {/* ADD STOCK BAR */}
        <section className="bg-slate-800 rounded-xl p-4 shadow-lg border border-slate-700">
          <label className="block text-sm font-medium text-slate-400 mb-2">Aktie hinzufügen</label>
          <form onSubmit={handleAddStock} className="flex gap-2">
            <div className="relative flex-1">
              <input 
                type="text" 
                value={tickerInput}
                onChange={(e) => setTickerInput(e.target.value)}
                placeholder="z.B. MSFT, Allianz, O" 
                className="w-full bg-slate-900 border border-slate-600 rounded-lg py-3 pl-4 pr-10 text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-all shadow-inner"
              />
              <div className="absolute right-3 top-3 text-slate-500">
                🔍
              </div>
            </div>
            <button 
              type="submit"
              className="bg-teal-600 hover:bg-teal-500 text-white font-semibold py-3 px-6 rounded-lg transition-colors shadow-lg active:scale-95"
            >
              Hinzufügen
            </button>
          </form>
        </section>

        {/* DATA TABLE / LIST */}
        <section>
          <PortfolioTable portfolio={portfolio} setPortfolio={setPortfolio} />
        </section>

        {/* DASHBOARD */}
        {projections.length > 0 && (
          <section className="animate-fade-in pt-4">
             <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                📊 Langzeit-Prognose
             </h2>
             <Dashboard 
              projections={projections} 
              portfolio={portfolio} 
              pauschbetrag={settings.pauschbetrag} 
            />
          </section>
        )}
      </main>

      {/* Settings Modal */}
      {isSettingsOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-slate-800 rounded-xl border border-slate-600 shadow-2xl w-full max-w-md overflow-hidden">
            <div className="p-5 border-b border-slate-700 flex justify-between items-center bg-slate-900">
              <h2 className="text-xl font-bold text-white">Einstellungen</h2>
              <button onClick={() => setIsSettingsOpen(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              
              {/* Pauschbetrag */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Sparerpauschbetrag (€)</label>
                <div className="relative">
                   <input 
                    type="number"
                    value={settings.pauschbetrag}
                    onChange={(e) => setSettings({...settings, pauschbetrag: parseFloat(e.target.value) || 0})}
                    className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                  />
                </div>
              </div>

              {/* Data Management */}
              <div className="pt-4 border-t border-slate-700">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">Backup</h3>
                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={handleExport}
                    className="flex justify-center items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white py-2 rounded-lg text-sm border border-slate-600"
                  >
                    💾 Speichern
                  </button>
                  <label className="flex justify-center items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white py-2 rounded-lg text-sm border border-slate-600 cursor-pointer">
                    📂 Laden
                    <input type="file" onChange={handleImport} className="hidden" accept=".json" />
                  </label>
                </div>
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default App;