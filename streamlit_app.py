import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import numpy as np
import os
from datetime import datetime, timedelta

# --- KONFIGURATION ---
st.set_page_config(
    page_title="Dividend Master DE",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS STYLING (HARDCORE LIGHT MODE) ---
st.markdown("""
<style>
    /* Global Background */
    [data-testid="stAppViewContainer"] {
        background-color: #f8fafc !important; /* Sehr helles Grau/Weiß */
        color: #0f172a !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, p, label, span, div, li {
        color: #0f172a !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* EXTREME TABLE FIXES (MOBILE & DARK MODE) */
    [data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }
    [data-testid="stDataFrame"] * {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    /* Header Cells specific */
    div[data-testid="stDataFrame"] div[role="columnheader"] {
        background-color: #f1f5f9 !important; /* Light Gray Header */
        color: #334155 !important;
        font-weight: 800 !important;
        border-bottom: 2px solid #e2e8f0 !important;
    }
    /* Data Cells specific */
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        color: #0f172a !important;
        border-bottom: 1px solid #f1f5f9 !important;
    }

    /* Buttons */
    button[kind="primary"] {
        background-color: #2563eb !important;
        border: none !important;
        transition: all 0.2s ease;
    }
    button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
    }
    button[kind="primary"] * {
        color: #ffffff !important;
    }
    
    /* Inputs */
    input, select, textarea {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
    }

    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important; 
    }
    
    /* Hide Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- LOCAL PERSISTENCE ---
CSV_FILE = "my_portfolio.csv"

def load_portfolio():
    # Versuche lokal zu laden
    if os.path.exists(CSV_FILE):
        try:
            return pd.read_csv(CSV_FILE)
        except:
            pass
    return pd.DataFrame(columns=[
        'Ticker', 'Name', 'Anteile', 'Kaufkurs', 'Aktueller Kurs', 
        'Div Rendite %', 'Div Wachs. %', 'Kurs Wachs. %', 
        'Sparrate €', 'Intervall', 'Reinvest'
    ])

def save_portfolio(df):
    # Speichert lokal in CSV (funktioniert gut lokal, im Web ephemeral)
    try:
        df.to_csv(CSV_FILE, index=False)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")

# --- SESSION STATE INITIALIZATION ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = load_portfolio()

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(ticker_symbol):
    clean_ticker = ticker_symbol.upper().strip()
    try:
        stock = yf.Ticker(clean_ticker)
        
        # 1. Price & Currency
        current_price = None
        try:
            current_price = stock.fast_info.last_price
        except:
            pass
            
        if current_price is None or pd.isna(current_price):
            try:
                hist = stock.history(period="5d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            except:
                pass

        if current_price is None or pd.isna(current_price):
            return None

        # 2. Dividend Yield
        yield_percent = 0.0
        freq = 1
        try:
            info = stock.info
            if 'dividendYield' in info and info['dividendYield']:
                yield_percent = info['dividendYield'] * 100
            
            # Estimate Frequency via history
            divs = stock.dividends
            if not divs.empty:
                recent = divs[divs.index > (pd.Timestamp.now(tz=divs.index.tz) - pd.Timedelta(days=365))]
                count = len(recent)
                if count >= 10: freq = 12
                elif count >= 3: freq = 4
                elif count >= 2: freq = 2
        except:
            pass

        # 3. Growth Rates (Fallback or Calc)
        div_cagr = 3.0
        price_cagr = 5.0
        
        # 4. Name
        name = clean_ticker
        try:
            meta = stock.info
            name = meta.get('shortName') or meta.get('longName') or clean_ticker
        except:
            pass

        return {
            'Ticker': clean_ticker,
            'Name': name,
            'Aktueller Kurs': float(current_price), 
            'Kaufkurs': float(current_price),     
            'Div Rendite %': round(float(yield_percent), 2),
            'Intervall': freq,
            'Div Wachs. %': div_cagr, 
            'Kurs Wachs. %': price_cagr, 
            'Sparrate €': 0.0,
            'Reinvest': True
        }
    except:
        return None

def calculate_projection(df, years, pauschbetrag):
    months = years * 12
    projections = []
    
    sim = df.copy()
    
    # Init
    sim['Jahresdiv_Pro_Aktie'] = sim['Aktueller Kurs'] * (sim['Div Rendite %'] / 100)
    current_shares = dict(zip(sim['Ticker'], sim['Anteile'].astype(float)))
    invested_capital_cash = (sim['Anteile'] * sim['Kaufkurs']).sum()
    current_pausch = pauschbetrag
    
    # Year 0
    curr_port_val = sum([current_shares[t] * sim.loc[sim['Ticker']==t, 'Aktueller Kurs'].values[0] for t in current_shares])
    projections.append({
        'Jahr': 0, 'Investiertes Kapital': invested_capital_cash, 
        'Portfolio Wert': curr_port_val, 'Netto Dividende': 0, 
        'Steuern': 0, 'Yield on Cost %': 0
    })

    year_net = 0
    year_tax = 0
    
    for m in range(1, months + 1):
        month_idx = ((m - 1) % 12) + 1
        monthly_savings_cash = 0
        
        for idx, row in sim.iterrows():
            ticker = row['Ticker']
            freq = int(row['Intervall'])
            curr_price = row['Aktueller Kurs']
            
            # Savings Plan
            spar = row['Sparrate €']
            if spar > 0:
                shares_bought = spar / curr_price
                current_shares[ticker] += shares_bought
                monthly_savings_cash += spar
            
            # Dividend Payout
            pays = (freq == 12) or \
                   (freq == 4 and month_idx % 3 == 0) or \
                   (freq == 2 and month_idx % 6 == 0) or \
                   (freq == 1 and month_idx == 6)
            
            if pays:
                gross = current_shares[ticker] * (row['Jahresdiv_Pro_Aktie'] / freq)
                if gross > 0:
                    tax = 0
                    if gross > current_pausch:
                        taxable = gross - current_pausch
                        tax = taxable * 0.26375
                        current_pausch = 0
                    else:
                        current_pausch -= gross
                    
                    net = gross - tax
                    year_net += net
                    year_tax += tax
                    
                    if row['Reinvest']:
                        current_shares[ticker] += (net / curr_price)
        
        invested_capital_cash += monthly_savings_cash
        
        # Year End
        if m % 12 == 0:
            curr_port_val = 0
            for t, shares in current_shares.items():
                p = sim.loc[sim['Ticker'] == t, 'Aktueller Kurs'].values[0]
                curr_port_val += shares * p
            
            yoc = (year_net / invested_capital_cash * 100) if invested_capital_cash > 0 else 0
            projections.append({
                'Jahr': m // 12,
                'Investiertes Kapital': invested_capital_cash,
                'Portfolio Wert': curr_port_val,
                'Netto Dividende': year_net,
                'Steuern': year_tax,
                'Yield on Cost %': yoc
            })
            
            year_net = 0; year_tax = 0; current_pausch = pauschbetrag
            sim['Aktueller Kurs'] *= (1 + sim['Kurs Wachs. %'] / 100)
            sim['Jahresdiv_Pro_Aktie'] *= (1 + sim['Div Wachs. %'] / 100)
            
    return pd.DataFrame(projections)


# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Konfiguration")
    pausch = st.number_input("Sparerpauschbetrag (€)", 0, 10000, 1000, step=100)
    
    st.divider()
    st.markdown("### 💾 Datenverwaltung")
    st.info("""
    **Hinweis zur Speicherung:**
    Lokal: Automatisch in `my_portfolio.csv`.
    Web: Daten sind temporär. Bitte Export nutzen!
    """)
    
    if not st.session_state.portfolio.empty:
        csv = st.session_state.portfolio.to_csv(index=False).encode('utf-8')
        st.download_button("📥 CSV Exportieren", csv, "mein_portfolio.csv", "text/csv", use_container_width=True)
        
    up_file = st.file_uploader("📤 CSV Importieren", type=["csv"])
    if up_file:
        try:
            df = pd.read_csv(up_file)
            st.session_state.portfolio = df
            save_portfolio(df)
            st.success("Geladen!")
            st.rerun()
        except:
            st.error("Fehler.")

# --- MAIN PAGE ---
st.title("Dividend Master DE 🇩🇪")

# 1. ADD TICKER SECTION (Cleaner UI)
with st.container():
    st.markdown("#### ➕ Aktie hinzufügen")
    c1, c2 = st.columns([4, 1])
    with c1:
        new_ticker = st.text_input("Ticker Symbol", placeholder="z.B. O, MSFT, ALV.DE", label_visibility="collapsed", key="ticker_in")
    with c2:
        if st.button("Suchen & Hinzufügen", type="primary", use_container_width=True):
            if new_ticker:
                with st.spinner("Lade Daten..."):
                    d = get_stock_data(new_ticker)
                    if d:
                        st.session_state.portfolio = pd.concat([st.session_state.portfolio, pd.DataFrame([d])], ignore_index=True)
                        save_portfolio(st.session_state.portfolio)
                        st.rerun()
                    else:
                        st.error("Nicht gefunden.")

st.divider()

# 2. PORTFOLIO TABLE
if not st.session_state.portfolio.empty:
    st.markdown("#### 📋 Dein Portfolio")
    
    # Data Editor
    edited = st.data_editor(
        st.session_state.portfolio,
        key="portfolio_editor",
        column_config={
            "Ticker": st.column_config.TextColumn(disabled=True, width="small"),
            "Name": st.column_config.TextColumn(disabled=True, width="medium"),
            "Kaufkurs": st.column_config.NumberColumn("Ø Kauf €", format="%.2f €"),
            "Aktueller Kurs": st.column_config.NumberColumn("Kurs €", format="%.2f €", disabled=True),
            "Anteile": st.column_config.NumberColumn(format="%.2f"),
            "Div Rendite %": st.column_config.NumberColumn("Div %", format="%.2f %%"),
            "Div Wachs. %": st.column_config.NumberColumn("D-Wachs%", format="%.1f %%"),
            "Kurs Wachs. %": st.column_config.NumberColumn("K-Wachs%", format="%.1f %%"),
            "Sparrate €": st.column_config.NumberColumn("Sparrate", format="%.0f €"),
            "Intervall": st.column_config.SelectboxColumn("Zyklus", options=[1,2,4,12], width="small"),
            "Reinvest": st.column_config.CheckboxColumn("Auto-Reinvest", default=True)
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic" # This actually allows deletion, but we add explicit button below
    )

    # Sync Changes
    if not edited.equals(st.session_state.portfolio):
        st.session_state.portfolio = edited
        save_portfolio(edited)
        st.rerun()

    # 3. EXPLICIT DELETE FUNCTION (Cleaner than native UI on mobile)
    with st.expander("🗑️ Positionen verwalten / löschen"):
        st.caption("Falls das Löschen in der Tabelle oben nicht klappt:")
        to_delete = st.multiselect("Aktien zum Entfernen auswählen:", st.session_state.portfolio['Ticker'].unique())
        if st.button("Ausgewählte Aktien unwiderruflich löschen", type="secondary"):
            if to_delete:
                st.session_state.portfolio = st.session_state.portfolio[~st.session_state.portfolio['Ticker'].isin(to_delete)]
                save_portfolio(st.session_state.portfolio)
                st.rerun()

    st.divider()

    # 4. SIMULATION DASHBOARD
    st.subheader("📊 Prognose Dashboard")
    
    sim_years = st.slider("Zeithorizont (Jahre)", 5, 40, 15)
    results = calculate_projection(edited, sim_years, pausch)
    
    # Year Selector
    year_sel = st.select_slider("Zeitreise zu Jahr:", options=results['Jahr'].unique(), value=sim_years//2)
    
    # Metrics
    row = results[results['Jahr'] == year_sel].iloc[0]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ø Monatlich (Netto)", f"{row['Netto Dividende']/12:,.2f} €")
    m2.metric("Jahres-Netto", f"{row['Netto Dividende']:,.0f} €", delta=f"{row['Yield on Cost %']:.1f}% YoC")
    m3.metric("Portfolio Wert", f"{row['Portfolio Wert']:,.0f} €")
    inv = row['Investiertes Kapital']
    gain = row['Portfolio Wert'] - inv
    m4.metric("Gesamtgewinn", f"{gain:,.0f} €", delta=f"{gain/inv*100:.0f}%" if inv>0 else "0%")

    # Charts
    tab1, tab2 = st.tabs(["📈 Chart-Ansicht", "🔢 Tabellen-Ansicht"])
    with tab1:
        st.area_chart(results.set_index('Jahr')[['Investiertes Kapital', 'Portfolio Wert']], color=["#cbd5e1", "#2563eb"])
        st.bar_chart(results.set_index('Jahr')['Netto Dividende'], color="#0d9488")
    with tab2:
        st.dataframe(results.style.format("{:.0f}"), use_container_width=True)

else:
    st.info("👆 Dein Portfolio ist leer. Füge oben Aktien hinzu!")
