import React, { useState, useEffect } from 'react';
import { PortfolioItem, UserSettings, YearProjection } from './types';
import { PortfolioTable } from './components/PortfolioTable';
import { Dashboard } from './components/Dashboard';
import { calculateProjections } from './services/financialEngine';

const DEFAULT_SETTINGS: UserSettings = {
  pauschbetrag: 1000,
  initialLumpSum: 0
};

const App: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [projections, setProjections] = useState<YearProjection[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Recalculate projections whenever inputs change
  useEffect(() => {
    if (portfolio.length > 0) {
      const data = calculateProjections(portfolio, settings);
      setProjections(data);
    } else {
      setProjections([]);
    }
  }, [portfolio, settings]);

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
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
      
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4 sticky top-0 z-10 shadow-md">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-blue-500">
              Dividend Master DE
            </h1>
          </div>
          <button 
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors border border-gray-600 text-sm font-medium"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-teal-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
            Einstellungen
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-4 md:p-6 space-y-8">
        
        {/* Section 1: Portfolio Input */}
        <section>
          <PortfolioTable portfolio={portfolio} setPortfolio={setPortfolio} />
        </section>

        {/* Section 2: Dashboard/Charts */}
        {projections.length > 0 && (
          <section className="animate-fade-in">
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
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-2xl w-full max-w-md overflow-hidden">
            <div className="p-5 border-b border-gray-700 flex justify-between items-center bg-gray-850">
              <h2 className="text-xl font-bold text-white">Einstellungen</h2>
              <button onClick={() => setIsSettingsOpen(false)} className="text-gray-400 hover:text-white">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              
              {/* Pauschbetrag */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Sparerpauschbetrag (€)</label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">€</span>
                   <input 
                    type="number"
                    value={settings.pauschbetrag}
                    onChange={(e) => setSettings({...settings, pauschbetrag: parseFloat(e.target.value) || 0})}
                    className="w-full bg-gray-900 border border-gray-600 rounded-lg pl-8 pr-3 py-2 text-white focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                    placeholder="1000"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Alle Dividendenerträge über diesem Betrag werden automatisch mit 26,375% (Abgeltung + Soli) versteuert.
                </p>
              </div>

              {/* Export/Import */}
              <div className="pt-4 border-t border-gray-700">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Daten-Backup</h3>
                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={handleExport}
                    className="flex justify-center items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg text-sm transition-colors border border-gray-600"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Speichern
                  </button>
                  <label className="flex justify-center items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg text-sm transition-colors border border-gray-600 cursor-pointer text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    Laden
                    <input type="file" onChange={handleImport} className="hidden" accept=".json" />
                  </label>
                </div>
              </div>

            </div>
            
            <div className="bg-gray-850 p-4 border-t border-gray-700 flex justify-end">
              <button 
                onClick={() => setIsSettingsOpen(false)}
                className="bg-teal-600 hover:bg-teal-500 text-white px-6 py-2 rounded-lg font-medium transition-colors"
              >
                Fertig
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default App;