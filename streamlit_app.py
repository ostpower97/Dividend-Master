import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time

# --- KONFIGURATION ---
st.set_page_config(
    page_title="Dividend Master DE",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für "Fintech"-Look
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #262730;
        border: 1px solid #4b5563;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-label {
        color: #9ca3af;
        font-size: 0.85rem;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }
    .metric-value {
        color: #f3f4f6;
        font-size: 1.8rem;
        font-weight: 800;
    }
    .metric-sub {
        color: #6b7280;
        font-size: 0.8rem;
        margin-top: 5px;
    }
    .highlight-teal { color: #2dd4bf; }
    .highlight-blue { color: #60a5fa; }
    .highlight-purple { color: #c084fc; }
    
    /* Hide Streamlit branding elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- STATIC FALLBACK DATA (Wenn Yahoo blockiert) ---
STATIC_FALLBACK_DATA = {
    'O': {'Name': 'Realty Income', 'Price': 53.50, 'Yield': 5.8, 'Freq': 12},
    'MAIN': {'Name': 'Main Street Capital', 'Price': 50.20, 'Yield': 6.0, 'Freq': 12},
    'MSFT': {'Name': 'Microsoft Corp.', 'Price': 405.00, 'Yield': 0.7, 'Freq': 4},
    'AAPL': {'Name': 'Apple Inc.', 'Price': 175.00, 'Yield': 0.5, 'Freq': 4},
    'ALV.DE': {'Name': 'Allianz SE', 'Price': 290.00, 'Yield': 5.2, 'Freq': 1},
    'MUV2.DE': {'Name': 'Münchener Rück', 'Price': 475.00, 'Yield': 3.3, 'Freq': 1},
    'BAS.DE': {'Name': 'BASF SE', 'Price': 46.00, 'Yield': 7.2, 'Freq': 1},
    'DTE.DE': {'Name': 'Deutsche Telekom', 'Price': 23.00, 'Yield': 3.5, 'Freq': 1},
    'JNJ': {'Name': 'Johnson & Johnson', 'Price': 148.00, 'Yield': 3.0, 'Freq': 4},
    'PG': {'Name': 'Procter & Gamble', 'Price': 162.00, 'Yield': 2.4, 'Freq': 4},
    'KO': {'Name': 'Coca-Cola', 'Price': 60.00, 'Yield': 3.1, 'Freq': 4},
    'PEP': {'Name': 'PepsiCo', 'Price': 165.00, 'Yield': 3.0, 'Freq': 4},
    'MCD': {'Name': 'McDonald\'s', 'Price': 270.00, 'Yield': 2.3, 'Freq': 4},
    'NESN.SW': {'Name': 'Nestlé', 'Price': 94.00, 'Yield': 3.0, 'Freq': 1},
    'ROG.SW': {'Name': 'Roche', 'Price': 225.00, 'Yield': 4.0, 'Freq': 1},
    'NOVN.SW': {'Name': 'Novartis', 'Price': 88.00, 'Yield': 3.8, 'Freq': 1},
    'SHEL': {'Name': 'Shell', 'Price': 32.00, 'Yield': 3.9, 'Freq': 4},
    'BMW.DE': {'Name': 'BMW AG', 'Price': 102.00, 'Yield': 5.5, 'Freq': 1},
    'VNA.DE': {'Name': 'Vonovia SE', 'Price': 28.00, 'Yield': 3.1, 'Freq': 1},
    'ADC': {'Name': 'Agree Realty', 'Price': 62.00, 'Yield': 4.7, 'Freq': 12},
    'STAG': {'Name': 'STAG Industrial', 'Price': 37.00, 'Yield': 4.0, 'Freq': 12},
}

# --- SESSION STATE INITIALISIERUNG ---
if 'portfolio' not in st.session_state:
    # Default Portfolio Structure
    st.session_state.portfolio = pd.DataFrame(columns=[
        'Ticker', 'Name', 'Anteile', 'Kaufkurs', 'Aktueller Kurs', 
        'Div Rendite %', 'Div Wachs. %', 'Kurs Wachs. %', 
        'Sparrate €', 'Intervall', 'Reinvest'
    ])

# --- HELPER FUNCTIONS ---

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(ticker_symbol):
    """
    Zieht Daten mit Caching (1 Stunde) und Fallback-Mechanismus.
    Vermeidet 'Too Many Requests' Abstürze.
    """
    clean_ticker = ticker_symbol.upper().strip()
    
    # 1. Versuch: yfinance (Live Daten)
    try:
        stock = yf.Ticker(clean_ticker)
        # Fast access to info (minimizes request load)
        info = stock.info 
        
        # Validierung: Hat die Antwort Daten?
        price = info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
        if price == 0 or price is None:
            raise ValueError("Kein Preis gefunden")

        name = info.get('shortName', clean_ticker)
        yield_val = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
        
        # Frequenz schätzen (braucht History, oft Fehlerquelle bei Rate Limit)
        # Wir machen das defensiv
        freq = 1
        try:
            hist = stock.dividends
            if not hist.empty:
                last_year = hist.last('12mo')
                count = len(last_year)
                if count >= 10: freq = 12
                elif count >= 3: freq = 4
                elif count >= 1: freq = 1
        except:
            pass # Behalte default 1 bei Fehler

        return {
            'Ticker': clean_ticker,
            'Name': name,
            'Aktueller Kurs': price,
            'Kaufkurs': price,
            'Div Rendite %': round(yield_val, 2),
            'Intervall': freq,
            'Div Wachs. %': 5.0,
            'Kurs Wachs. %': 5.0,
            'Reinvest': True,
            'Source': 'Live'
        }

    except Exception as e:
        # 2. Versuch: Fallback Datenbank
        if clean_ticker in STATIC_FALLBACK_DATA:
            data = STATIC_FALLBACK_DATA[clean_ticker]
            return {
                'Ticker': clean_ticker,
                'Name': data['Name'],
                'Aktueller Kurs': data['Price'],
                'Kaufkurs': data['Price'],
                'Div Rendite %': data['Yield'],
                'Intervall': data['Freq'],
                'Div Wachs. %': 5.0,
                'Kurs Wachs. %': 5.0,
                'Reinvest': True,
                'Source': 'Fallback'
            }
        
        # 3. Versuch: Manuelles Template zurückgeben (statt Fehler)
        return {
            'Ticker': clean_ticker,
            'Name': 'Bitte Daten eingeben',
            'Aktueller Kurs': 0.0,
            'Kaufkurs': 0.0,
            'Div Rendite %': 0.0,
            'Intervall': 1,
            'Div Wachs. %': 5.0,
            'Kurs Wachs. %': 5.0,
            'Reinvest': True,
            'Source': 'Manual'
        }

def calculate_projection(df, years, pauschbetrag):
    """
    Simuliert die Portfolio-Entwicklung monatlich.
    """
    months = years * 12
    projections = []
    
    # Init Simulation State
    sim_data = df.copy()
    
    # Initiale Werte berechnen
    sim_data['Aktuelle Div/Aktie (Jahr)'] = sim_data['Aktueller Kurs'] * (sim_data['Div Rendite %'] / 100)
    current_shares = sim_data['Anteile'].astype(float).to_dict()
    
    # Investiertes Kapital (Initial)
    invested_capital = (sim_data['Anteile'] * sim_data['Kaufkurs']).sum()
    
    current_pauschbetrag = pauschbetrag
    
    # Aggregatoren für das laufende Jahr
    year_gross = 0
    year_net = 0
    year_tax = 0
    portfolio_value = 0

    for m in range(1, months + 1):
        month_index = m % 12
        if month_index == 0: month_index = 12
        
        # --- JAHRESWECHSEL ---
        if (m - 1) % 12 == 0 and m > 1:
            # Snapshot speichern
            projections.append({
                'Jahr': (m-1)//12,
                'Investiertes Kapital': invested_capital,
                'Portfolio Wert': portfolio_value,
                'Brutto Dividende': year_gross,
                'Netto Dividende': year_net,
                'Steuern': year_tax,
                'Yield on Cost %': (year_gross / invested_capital * 100) if invested_capital > 0 else 0
            })
            # Reset Aggregatoren
            year_gross = 0
            year_net = 0
            year_tax = 0
            current_pauschbetrag = pauschbetrag
            
            # WACHSTUM ANWENDEN (Step-Up am Jahresanfang)
            for idx, row in sim_data.iterrows():
                # Kurssteigerung
                sim_data.at[idx, 'Aktueller Kurs'] *= (1 + row['Kurs Wachs. %'] / 100)
                # Dividendensteigerung
                sim_data.at[idx, 'Aktuelle Div/Aktie (Jahr)'] *= (1 + row['Div Wachs. %'] / 100)

        # --- MONATLICHE LOGIK ---
        current_portfolio_val_temp = 0
        monthly_savings_total = 0
        
        for idx, row in sim_data.iterrows():
            ticker = row['Ticker']
            freq = int(row['Intervall'])
            
            # 1. Sparplan (erhöht investiertes Kapital)
            monthly_contrib = row['Sparrate €']
            if monthly_contrib > 0:
                new_shares = monthly_contrib / sim_data.at[idx, 'Aktueller Kurs']
                current_shares[ticker] += new_shares
                monthly_savings_total += monthly_contrib

            # 2. Dividenden & Reinvest
            pays_this_month = False
            if freq == 12: pays_this_month = True
            elif freq == 4 and month_index % 3 == 0: pays_this_month = True 
            elif freq == 2 and month_index % 6 == 0: pays_this_month = True
            elif freq == 1 and month_index == 5: pays_this_month = True 

            if pays_this_month:
                div_per_share_payment = sim_data.at[idx, 'Aktuelle Div/Aktie (Jahr)'] / freq
                gross_payout = current_shares[ticker] * div_per_share_payment
                
                if gross_payout > 0:
                    # Steuer
                    tax = 0
                    if gross_payout > current_pauschbetrag:
                        taxable = gross_payout - current_pauschbetrag
                        tax = taxable * 0.26375
                        current_pauschbetrag = 0
                    else:
                        current_pauschbetrag -= gross_payout
                        tax = 0
                    
                    net_payout = gross_payout - tax
                    
                    # Tracking
                    year_gross += gross_payout
                    year_net += net_payout
                    year_tax += tax
                    
                    # Reinvest (DRIP)
                    if row['Reinvest']:
                        drip_shares = net_payout / sim_data.at[idx, 'Aktueller Kurs']
                        current_shares[ticker] += drip_shares

            # Portfolio Wert für Ticker berechnen
            current_portfolio_val_temp += current_shares[ticker] * sim_data.at[idx, 'Aktueller Kurs']
        
        # Monatssummen updaten
        portfolio_value = current_portfolio_val_temp
        invested_capital += monthly_savings_total

    # Letztes Jahr hinzufügen
    projections.append({
        'Jahr': years,
        'Investiertes Kapital': invested_capital,
        'Portfolio Wert': portfolio_value,
        'Brutto Dividende': year_gross,
        'Netto Dividende': year_net,
        'Steuern': year_tax,
        'Yield on Cost %': (year_gross / invested_capital * 100) if invested_capital > 0 else 0
    })
    
    return pd.DataFrame(projections)

# --- UI LAYOUT ---

# Sidebar
with st.sidebar:
    st.title("Einstellungen ⚙️")
    pauschbetrag = st.number_input("Sparerpauschbetrag (€)", value=1000, step=100)
    
    st.markdown("---")
    st.subheader("Daten")
    
    # CSV Export
    if not st.session_state.portfolio.empty:
        csv = st.session_state.portfolio.to_csv(index=False).encode('utf-8')
        st.download_button(
            "💾 Portfolio speichern (CSV)",
            csv,
            "portfolio.csv",
            "text/csv",
            key='download-csv'
        )
    
    # CSV Import
    uploaded_file = st.file_uploader("📂 Portfolio laden", type=["csv"])
    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            required_cols = ['Ticker', 'Anteile', 'Kaufkurs']
            if all(col in df_uploaded.columns for col in required_cols):
                st.session_state.portfolio = df_uploaded
                st.success("Erfolgreich geladen!")
                st.rerun()
            else:
                st.error("CSV Format falsch.")
        except:
            st.error("Datei konnte nicht gelesen werden.")

# Main Content
st.title("💰 Dividend Master DE")
st.caption("Realtime-Kurse via yfinance (Cached) | Deutsche Steuerlogik | Zinseszins-Prognose")

# 1. ADD TICKER
col1, col2 = st.columns([3, 1])
with col1:
    new_ticker = st.text_input("Ticker Symbol (z.B. O, MSFT, ALV.DE)", placeholder="Symbol eingeben...")
with col2:
    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
    if st.button("Hinzufügen 🚀", use_container_width=True):
        if new_ticker:
            with st.spinner(f"Lade Daten für {new_ticker}..."):
                stock_data = get_stock_data(new_ticker)
                
                # Feedback an User
                if stock_data['Source'] == 'Fallback':
                    st.toast(f"⚠️ Yahoo überlastet. Nutze gespeicherte Daten für {stock_data['Ticker']}.", icon="ℹ️")
                elif stock_data['Source'] == 'Manual':
                    st.warning("Keine Daten gefunden (API Limit). Bitte trage Kurs/Dividende manuell ein.")

                # Append to portfolio
                st.session_state.portfolio = pd.concat([
                    st.session_state.portfolio, 
                    pd.DataFrame([stock_data])
                ], ignore_index=True)
                
                st.rerun()

# 2. PORTFOLIO TABLE
st.subheader("Dein Portfolio")
if not st.session_state.portfolio.empty:
    
    edited_df = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        column_config={
            "Ticker": st.column_config.TextColumn(disabled=True),
            "Name": st.column_config.TextColumn(disabled=True),
            "Kaufkurs": st.column_config.NumberColumn("Ø Kaufkurs €", format="%.2f €", help="Dein durchschnittlicher Einkaufspreis"),
            "Aktueller Kurs": st.column_config.NumberColumn("Aktuell €", format="%.2f €"),
            "Anteile": st.column_config.NumberColumn(format="%.2f"),
            "Div Rendite %": st.column_config.NumberColumn("Div %", format="%.2f %%"),
            "Div Wachs. %": st.column_config.NumberColumn("Div CAGR %", format="%.1f %%"),
            "Kurs Wachs. %": st.column_config.NumberColumn("Kurs CAGR %", format="%.1f %%"),
            "Sparrate €": st.column_config.NumberColumn(format="%.0f €"),
            "Intervall": st.column_config.SelectboxColumn("Intervall", options=[1, 2, 4, 12]),
            "Reinvest": st.column_config.CheckboxColumn("Auto-Reinvest", default=True),
            "Source": st.column_config.TextColumn("Quelle", disabled=True, width="small")
        },
        use_container_width=True,
        hide_index=True,
        key="editor"
    )
    
    st.session_state.portfolio = edited_df

    # 3. PROGNOSEN & DASHBOARD
    st.markdown("---")
    
    years_to_project = st.slider("Prognose-Zeitraum (Jahre)", 1, 30, 15)
    
    if not edited_df.empty:
        df_proj = calculate_projection(edited_df, years_to_project, pauschbetrag)
        
        # --- TOP LEVEL METRICS (Current) ---
        current_invested = (edited_df['Anteile'] * edited_df['Kaufkurs']).sum()
        current_value = (edited_df['Anteile'] * edited_df['Aktueller Kurs']).sum()
        current_gain = current_value - current_invested
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Investiertes Kapital", f"{current_invested:,.0f} €")
        c2.metric("Aktueller Wert", f"{current_value:,.0f} €")
        c3.metric("Gewinn/Verlust", f"{current_gain:,.0f} €", delta=f"{(current_gain/current_invested*100) if current_invested>0 else 0:.1f} %")
        c4.metric("Brutto Dividende (Forward)", f"{(current_value * (edited_df['Div Rendite %'].mean()/100)):,.0f} €" if not edited_df.empty else "0 €")

        st.markdown("---")
        
        # --- PROJECTION TABS ---
        tab1, tab2 = st.tabs(["📊 Dashboard & KPIs", "📈 Detaillierte Tabelle"])
        
        with tab1:
            view_year = st.slider("Jahr im Detail ansehen:", 1, years_to_project, years_to_project)
            row = df_proj[df_proj['Jahr'] == view_year].iloc[0]
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Ø Monatlich (Netto)</div><div class="metric-value highlight-teal">{row['Netto Dividende']/12:,.0f} €</div><div class="metric-sub">Verfügbar</div></div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Jahres-Dividende (Netto)</div><div class="metric-value highlight-blue">{row['Netto Dividende']:,.0f} €</div><div class="metric-sub">Nach Steuern</div></div>""", unsafe_allow_html=True)
            with m3:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Portfolio Wert</div><div class="metric-value">{row['Portfolio Wert']:,.0f} €</div><div class="metric-sub">Gesamtvermögen</div></div>""", unsafe_allow_html=True)
            with m4:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Persönliche Rendite</div><div class="metric-value highlight-purple">{row['Yield on Cost %']:.1f} %</div><div class="metric-sub">Yield on Cost</div></div>""", unsafe_allow_html=True)

            st.markdown("### 📈 Vermögensentwicklung")
            chart_data = df_proj[['Jahr', 'Investiertes Kapital', 'Portfolio Wert']].set_index('Jahr')
            st.area_chart(chart_data, color=["#4b5563", "#2dd4bf"])
            
            st.markdown("### 💸 Dividenden-Strom")
            div_data = df_proj[['Jahr', 'Netto Dividende', 'Steuern']].set_index('Jahr')
            st.bar_chart(div_data, color=["#2dd4bf", "#ef4444"])

        with tab2:
            st.dataframe(df_proj.style.format({
                "Investiertes Kapital": "{:,.0f} €",
                "Portfolio Wert": "{:,.0f} €",
                "Brutto Dividende": "{:,.0f} €",
                "Netto Dividende": "{:,.0f} €",
                "Steuern": "{:,.0f} €",
                "Yield on Cost %": "{:.2f} %"
            }), use_container_width=True)

else:
    st.info("Bitte füge oben Aktien hinzu (z.B. 'O' für Realty Income oder 'ALV.DE' für Allianz), um zu starten.")
