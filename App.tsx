import React, { useState, useEffect } from 'react';
import { PortfolioItem, UserSettings, YearProjection } from './types';
import { PortfolioTable } from './components/PortfolioTable';
import { Dashboard } from './components/Dashboard';
import { calculateProjections } from './services/financialEngine';
import { fetchStockDataFromAI } from './services/aiFinancialData'; // Use AI instead of static file

const DEFAULT_SETTINGS: UserSettings = {
  pauschbetrag: 1000,
  initialLumpSum: 0
};

const App: React.FC = () => {
  // Load initial state from LocalStorage
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>(() => {
    try {
      const saved = localStorage.getItem('dividend_portfolio');
      return saved ? JSON.parse(saved) : [];
    } catch (e) { return []; }
  });
  
  const [settings, setSettings] = useState<UserSettings>(() => {
    try {
      const saved = localStorage.getItem('dividend_settings');
      return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
    } catch (e) { return DEFAULT_SETTINGS; }
  });

  const [projections, setProjections] = useState<YearProjection[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [tickerInput, setTickerInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Persistence
  useEffect(() => {
    localStorage.setItem('dividend_portfolio', JSON.stringify(portfolio));
  }, [portfolio]);

  useEffect(() => {
    localStorage.setItem('dividend_settings', JSON.stringify(settings));
  }, [settings]);

  // Recalculate whenever data changes
  useEffect(() => {
    // Calculate even if portfolio is empty (returns empty projections)
    const data = calculateProjections(portfolio, settings);
    setProjections(data);
  }, [portfolio, settings]);

  const handleAddStock = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!tickerInput.trim()) return;

    setIsLoading(true);

    try {
      // 1. Try to fetch real data via AI (simulating yfinance quality)
      const aiData = await fetchStockDataFromAI(tickerInput);
      
      // 2. Create the new item with AI data or Fallbacks
      const newItem: PortfolioItem = {
        id: Date.now().toString(),
        symbol: aiData?.symbol || tickerInput.toUpperCase(),
        name: aiData?.name || tickerInput.toUpperCase(),
        shares: 0, // User must enter shares manually
        buyPrice: aiData?.price || 0,
        currentPrice: aiData?.price || 0,
        dividendYield: aiData?.dividendYield || 0,
        dividendGrowth: aiData?.dividendGrowth || 3.0, // Conservative Fallback
        priceGrowth: aiData?.priceGrowth || 5.0,
        payoutFrequency: aiData?.payoutFrequency || 1,
        reinvest: true,
        monthlyContribution: 0
      };

      setPortfolio(prev => [...prev, newItem]);
      setTickerInput("");
    } catch (error) {
      alert("Fehler beim Laden der Daten. Bitte manuell eingeben.");
    } finally {
      setIsLoading(false);
    }
  };

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
        alert('Format-Fehler beim Import.');
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans pb-32">
      
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-teal-500/10 p-2 rounded-lg">
              <span className="text-2xl">📈</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white leading-tight">Dividend Master</h1>
              <p className="text-xs text-slate-400">Compound Tracker</p>
            </div>
          </div>
          <button 
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors text-slate-400 hover:text-white border border-slate-700"
          >
            ⚙️
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto p-4 space-y-8">
        
        {/* ADD STOCK BAR */}
        <section className="bg-slate-900 rounded-2xl p-1 shadow-lg border border-slate-800 sticky top-[80px] z-20">
          <form onSubmit={handleAddStock} className="flex relative">
            <input 
              type="text" 
              value={tickerInput}
              onChange={(e) => setTickerInput(e.target.value)}
              disabled={isLoading}
              placeholder="Ticker eingeben (z.B. MSFT, ALV.DE)..." 
              className="w-full bg-transparent text-white px-5 py-4 outline-none placeholder-slate-500 font-medium disabled:opacity-50"
            />
            <button 
              type="submit"
              disabled={isLoading || !tickerInput}
              className="absolute right-1 top-1 bottom-1 bg-teal-600 hover:bg-teal-500 disabled:bg-slate-700 text-white font-semibold px-6 rounded-xl transition-all active:scale-95 shadow-lg flex items-center gap-2"
            >
              {isLoading ? (
                <span className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full block"></span>
              ) : (
                <>
                  <span>+</span> 
                  <span className="hidden sm:inline">Hinzufügen</span>
                </>
              )}
            </button>
          </form>
        </section>

        {/* PORTFOLIO LIST */}
        <section>
          <PortfolioTable portfolio={portfolio} setPortfolio={setPortfolio} />
        </section>

        {/* VISUALIZATION */}
        {portfolio.length > 0 && projections.length > 0 && (
          <section className="animate-fade-in space-y-4 pt-4">
             <div className="flex items-center gap-2 px-2">
                <h2 className="text-xl font-bold text-white">Langzeit-Prognose</h2>
                <span className="px-2 py-0.5 bg-teal-500/20 text-teal-300 text-xs rounded-full font-medium">30 Jahre</span>
             </div>
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
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="bg-slate-900 rounded-t-2xl sm:rounded-2xl border border-slate-800 w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-900">
              <h2 className="text-lg font-bold text-white">Einstellungen</h2>
              <button onClick={() => setIsSettingsOpen(false)} className="bg-slate-800 p-1 rounded-full text-slate-400 hover:text-white">✕</button>
            </div>
            
            <div className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">Sparerpauschbetrag (€)</label>
                <input 
                  type="number"
                  value={settings.pauschbetrag}
                  onChange={(e) => setSettings({...settings, pauschbetrag: parseFloat(e.target.value) || 0})}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-teal-500 outline-none text-lg"
                />
              </div>

              <div className="pt-4 border-t border-slate-800">
                <div className="grid grid-cols-2 gap-3">
                  <button onClick={handleExport} className="flex justify-center items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white py-3 rounded-lg text-sm font-medium transition-colors">
                    💾 Backup speichern
                  </button>
                  <label className="flex justify-center items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white py-3 rounded-lg text-sm font-medium cursor-pointer transition-colors">
                    📂 Backup laden
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