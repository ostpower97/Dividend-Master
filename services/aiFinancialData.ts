import { GoogleGenAI, Type } from "@google/genai";
import { StockData } from "../types";

// Initialize Gemini
// Note: In a deployed Netlify app, ensure 'API_KEY' is set in your environment variables.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const fetchStockDataFromAI = async (ticker: string): Promise<Partial<StockData> | null> => {
  if (!ticker) return null;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash-latest",
      contents: `Du bist ein Finanz-Daten-Assistent. Ermittle die aktuellsten Finanzdaten für das Unternehmen mit dem Ticker Symbol '${ticker}'.
      
      Anforderungen:
      1. Name: Offizieller Unternehmensname.
      2. Price: Aktueller Aktienkurs in EURO (€). Wenn möglich Realtime, sonst letzter Schlusskurs.
      3. DividendYield: Aktuelle Dividendenrendite in Prozent (z.B. 5.5 für 5,5%).
      4. DividendGrowth: Durchschnittliches jährliches Dividendenwachstum (CAGR) der letzten 5 Jahre in Prozent.
      5. PriceGrowth: Durchschnittliche jährliche Kursentwicklung (CAGR) der letzten 10 Jahre in Prozent.
      6. PayoutFrequency: Wie oft schüttet das Unternehmen pro Jahr aus? (1 = Jährlich, 2 = Halbjährlich, 4 = Quartalsweise, 12 = Monatlich).

      Beispiele für Frequency: 
      - Realty Income (O) = 12
      - Allianz (ALV) = 1
      - Microsoft (MSFT) = 4

      Gib Preise immer in EUR an.`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            name: { type: Type.STRING },
            price: { type: Type.NUMBER, description: "Current Stock Price in EUR" },
            dividendYield: { type: Type.NUMBER, description: "Dividend Yield % (e.g. 4.5)" },
            dividendGrowth: { type: Type.NUMBER, description: "5y Dividend CAGR %" },
            priceGrowth: { type: Type.NUMBER, description: "10y Price CAGR %" },
            payoutFrequency: { type: Type.NUMBER, description: "Payouts per year: 1, 2, 4, or 12" }
          },
          required: ["name", "price", "dividendYield", "dividendGrowth", "priceGrowth", "payoutFrequency"]
        }
      }
    });

    const text = response.text;
    if (!text) return null;

    const data = JSON.parse(text);
    
    return {
      symbol: ticker.toUpperCase(),
      name: data.name,
      price: data.price,
      dividendYield: data.dividendYield,
      dividendGrowth: data.dividendGrowth,
      priceGrowth: data.priceGrowth,
      payoutFrequency: data.payoutFrequency
    } as StockData; 

  } catch (error) {
    console.error("Error fetching stock data via AI:", error);
    return null;
  }
};