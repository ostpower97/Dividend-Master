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
    initial_sidebar_state="expanded"
)

# --- CSS STYLING (OPTIMIZED LIGHT MODE & MOBILE FIXES) ---
st.markdown("""
<style>
    /* Force Light Theme Colors Global */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
        color: #0f172a;
    }
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.95);
    }
    
    /* Typography Overrides (Excluding Buttons) */
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #0f172a;
    }
    
    /* BUTTON FIXES */
    /* Primary Buttons (Red/Blue) need white text */
    button[kind="primary"] p, button[kind="primary"] div {
        color: #ffffff !important;
    }
    /* Secondary Buttons need dark text */
    button[kind="secondary"] p, button[kind="secondary"] div {
        color: #0f172a !important;
    }
    
    /* TABLE FIXES (MOBILE & DARK MODE OVERRIDE) */
    [data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0;
    }
    [data-testid="stDataFrame"] div[role="columnheader"] {
        background-color: #f1f5f9 !important;
        color: #334155 !important;
        font-weight: bold;
    }
    [data-testid="stDataFrame"] div[role="gridcell"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    
    /* Custom Metric Cards */
    div.css-1r6slb0 {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
    }
    
    /* Hide Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- LOCAL PERSISTENCE ---
CSV_FILE = "my_portfolio.csv"

def load_portfolio():
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
    try:
        df.to_csv(CSV_FILE, index=False)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")

# --- SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = load_portfolio()

# --- PROFESSIONAL YFINANCE FETCHING ---

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(ticker_symbol):
    """
    Holt Daten via yfinance, konvertiert Währung und BERECHNET WACHSTUMSRATEN.
    """
    clean_ticker = ticker_symbol.upper().strip()
    
    try:
        stock = yf.Ticker(clean_ticker)
        
        # --- A. PREIS & WÄHRUNG ---
        current_price = None
        currency = "EUR" 
        
        try:
            current_price = stock.fast_info.last_price
            currency = stock.fast_info.currency
        except:
            pass
            
        if current_price is None or pd.isna(current_price):
            try:
                hist = stock.history(period="5d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    if not currency or currency == "EUR":
                        meta = stock.info
                        currency = meta.get('currency', 'EUR')
            except:
                pass

        if current_price is None or pd.isna(current_price):
            # Try finding via search if direct ticker fails? (Simple Fallback)
            return None

        # --- B. WÄHRUNGSUMRECHNUNG (FX -> EUR) ---
        if currency and currency.upper() != 'EUR':
            try:
                rate = 1.0
                if currency.upper() == 'USD':
                    fx = yf.Ticker("EUR=X")
                    rate = fx.fast_info.last_price
                elif currency.upper() == 'GBP':
                    fx = yf.Ticker("GBPEUR=X")
                    rate = fx.fast_info.last_price
                elif currency.upper() == 'CHF':
                    fx = yf.Ticker("CHFEUR=X")
                    rate = fx.fast_info.last_price
                
                if rate and rate > 0:
                    current_price = current_price * rate
            except Exception as e:
                pass

        # --- C. DIVIDENDEN & RENDITE ---
        yield_percent = 0.0
        freq = 1
        
        try:
            divs = stock.dividends
            if not divs.empty:
                # Letztes Jahr Dividenden für Yield (TTM)
                tz = divs.index.tz
                now = pd.Timestamp.now(tz=tz) if tz else pd.Timestamp.now()
                cutoff = now - pd.Timedelta(days=365)
                recent_divs = divs[divs.index > cutoff]
                
                if not recent_divs.empty:
                    ttm_sum = recent_divs.sum()
                    # Yield basierend auf Originalpreis (da Div auch in Originalwährung)
                    price_original = stock.fast_info.last_price or current_price
                    if price_original > 0:
                        yield_percent = (ttm_sum / price_original) * 100
                    
                    c = len(recent_divs)
                    if c >= 10: freq = 12
                    elif c >= 3: freq = 4
                    elif c >= 2: freq = 2
            else:
                info = stock.info
                if 'dividendYield' in info and info['dividendYield']:
                    yield_percent = info['dividendYield'] * 100
        except Exception:
            pass

        # --- D. WACHSTUMS-BERECHNUNG (REAL) ---
        div_cagr = 2.0 # Konservativer Fallback
        price_cagr = 4.0 # Konservativer Fallback
        
        # 1. Price Growth (5Y CAGR)
        try:
            hist_5y = stock.history(period="5y")
            if not hist_5y.empty:
                start_p = hist_5y['Close'].iloc[0]
                end_p = hist_5y['Close'].iloc[-1]
                years_passed = (hist_5y.index[-1] - hist_5y.index[0]).days / 365.25
                
                if years_passed >= 3 and start_p > 0:
                    cagr = (end_p / start_p) ** (1 / years_passed) - 1
                    price_cagr = round(cagr * 100, 2)
        except:
            pass

        # 2. Dividend Growth (5Y CAGR)
        try:
            divs = stock.dividends
            if not divs.empty:
                # Gruppieren nach Jahr
                divs_per_year = divs.groupby(divs.index.year).sum()
                current_year = pd.Timestamp.now().year
                # Nur volle Jahre betrachten (ohne aktuelles Jahr)
                full_years = divs_per_year[divs_per_year.index < current_year]
                
                if len(full_years) >= 5:
                    end_div = full_years.iloc[-1]
                    start_div = full_years.iloc[-5]
                    if start_div > 0:
                        div_cagr = round(((end_div / start_div) ** (1/4) - 1) * 100, 2)
                elif len(full_years) >= 3:
                    end_div = full_years.iloc[-1]
                    start_div = full_years.iloc[0]
                    diff = len(full_years) - 1
                    if start_div > 0:
                        div_cagr = round(((end_div / start_div) ** (1/diff) - 1) * 100, 2)
        except:
            pass

        # --- E. NAME ---
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

    except Exception as e:
        print(f"Fatal error fetching {clean_ticker}: {e}")
        return None

def calculate_projection(df, years, pauschbetrag):
    months = years * 12
    projections = []
    
    sim = df.copy()
    
    # 1. Initiale Werte
    sim['Jahresdiv_Pro_Aktie'] = sim['Aktueller Kurs'] * (sim['Div Rendite %'] / 100)
    current_shares = dict(zip(sim['Ticker'], sim['Anteile'].astype(float)))
    invested_capital_cash = (sim['Anteile'] * sim['Kaufkurs']).sum()
    current_pausch = pauschbetrag
    
    # JAHR 0
    curr_port_val = 0
    for t_symbol, t_shares in current_shares.items():
        price = sim.loc[sim['Ticker'] == t_symbol, 'Aktueller Kurs'].values[0]
        curr_port_val += t_shares * price
        
    projections.append({
        'Jahr': 0,
        'Investiertes Kapital': invested_capital_cash,
        'Portfolio Wert': curr_port_val,
        'Netto Dividende': 0,
        'Steuern': 0,
        'Yield on Cost %': 0
    })

    year_net = 0
    year_tax = 0
    
    # --- SIMULATION ---
    for m in range(1, months + 1):
        month_idx = ((m - 1) % 12) + 1
        monthly_savings_cash = 0
        
        for idx, row in sim.iterrows():
            ticker = row['Ticker']
            freq = int(row['Intervall'])
            curr_price = row['Aktueller Kurs']
            
            # A. Sparplan
            spar = row['Sparrate €']
            if spar > 0:
                shares_bought = spar / curr_price
                current_shares[ticker] += shares_bought
                monthly_savings_cash += spar
            
            # B. Dividende
            pays = False
            if freq == 12: pays = True
            elif freq == 4 and month_idx % 3 == 0: pays = True
            elif freq == 1 and month_idx == 6: pays = True 
            elif freq == 2 and month_idx % 6 == 0: pays = True
            
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
                        tax = 0
                    
                    net = gross - tax
                    year_net += net
                    year_tax += tax
                    
                    if row['Reinvest']:
                        drip_shares = net / curr_price
                        current_shares[ticker] += drip_shares
        
        invested_capital_cash += monthly_savings_cash
        
        if m % 12 == 0:
            curr_port_val = 0
            for t_symbol, t_shares in current_shares.items():
                price = sim.loc[sim['Ticker'] == t_symbol, 'Aktueller Kurs'].values[0]
                curr_port_val += t_shares * price
            
            yoc = (year_net / invested_capital_cash * 100) if invested_capital_cash > 0 else 0
            
            projections.append({
                'Jahr': m // 12,
                'Investiertes Kapital': invested_capital_cash,
                'Portfolio Wert': curr_port_val,
                'Netto Dividende': year_net,
                'Steuern': year_tax,
                'Yield on Cost %': yoc
            })
            
            year_net = 0
            year_tax = 0
            current_pausch = pauschbetrag
            
            # Jährliches Wachstum anwenden
            sim['Aktueller Kurs'] *= (1 + sim['Kurs Wachs. %'] / 100)
            sim['Jahresdiv_Pro_Aktie'] *= (1 + sim['Div Wachs. %'] / 100)
    
    return pd.DataFrame(projections)

# --- UI LAYOUT ---

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3310/3310653.png", width=50)
    st.markdown("### Einstellungen")
    pausch = st.number_input("Sparerpauschbetrag (€)", 0, 10000, 1000, step=100)
    st.caption("Änderungen werden automatisch gespeichert.")
    
    if not st.session_state.portfolio.empty:
        st.divider()
        csv = st.session_state.portfolio.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Backup (CSV)", csv, "portfolio_backup.csv", "text/csv", use_container_width=True)
        
    uploaded_file = st.file_uploader("📂 Import (CSV)", type=["csv"])
    if uploaded_file:
        try:
            df_up = pd.read_csv(uploaded_file)
            st.session_state.portfolio = df_up
            save_portfolio(df_up) # Direkt speichern
            st.success("Erfolgreich geladen!")
            st.rerun()
        except:
            st.error("Fehler beim Laden.")

st.title("Dividend Master DE 🇩🇪")
st.markdown("##### 🚀 Live-Daten & Zinseszins-Optimierer")

# Input Section
c1, c2 = st.columns([3,1])
with c1:
    new_ticker = st.text_input("Aktie hinzufügen", placeholder="z.B. O, MSFT, ALV.DE", label_visibility="collapsed", key="ticker_input")
with c2:
    if st.button("Hinzufügen 🔎", type="primary", use_container_width=True):
        if new_ticker:
            with st.spinner(f"Analysiere {new_ticker} (5Y History)..."):
                data = get_stock_data(new_ticker)
                if data:
                    st.session_state.portfolio = pd.concat([
                        st.session_state.portfolio, 
                        pd.DataFrame([data])
                    ], ignore_index=True)
                    save_portfolio(st.session_state.portfolio) # Speichern
                    st.rerun()
                else:
                    st.error("Ticker nicht gefunden.")

# Portfolio Table
if not st.session_state.portfolio.empty:
    st.markdown("### 📋 Dein Portfolio")
    
    # Nutzung eines Keys für data_editor ist CRITICAL für State Sync bei Re-Runs
    edited = st.data_editor(
        st.session_state.portfolio,
        key="portfolio_editor",
        column_config={
            "Ticker": st.column_config.TextColumn(disabled=True),
            "Name": st.column_config.TextColumn(disabled=True),
            "Kaufkurs": st.column_config.NumberColumn("Ø Kauf €", format="%.2f €"),
            "Aktueller Kurs": st.column_config.NumberColumn("Kurs €", format="%.2f €", disabled=True),
            "Anteile": st.column_config.NumberColumn(format="%.2f"),
            "Div Rendite %": st.column_config.NumberColumn("Div %", format="%.2f %%"),
            "Div Wachs. %": st.column_config.NumberColumn("D-CAGR %", format="%.2f %%", help="Dividendenwachstum p.a. (5J Durchschnitt)"),
            "Kurs Wachs. %": st.column_config.NumberColumn("K-CAGR %", format="%.2f %%", help="Kurswachstum p.a. (5J Durchschnitt)"),
            "Sparrate €": st.column_config.NumberColumn("Sparrate", format="%.0f €"),
            "Intervall": st.column_config.SelectboxColumn("Zyklus", options=[1,2,4,12]),
            "Reinvest": st.column_config.CheckboxColumn("Auto-Reinvest", default=True)
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic"
    )
    
    # Check for changes and autosave
    if not edited.equals(st.session_state.portfolio):
        st.session_state.portfolio = edited
        save_portfolio(edited)
    
    st.divider()
    
    # Simulation
    st.subheader("📊 Simulation & Analyse")
    
    sim_years = st.slider("Simulations-Dauer (Total)", 5, 40, 20)
    results = calculate_projection(edited, sim_years, pausch)
    
    st.markdown("#### 🔍 Detail-Check: Wie viel bekomme ich im Jahr X?")
    
    col_slider, col_space = st.columns([2, 1])
    with col_slider:
        inspect_year = st.select_slider(
            "Zeitreise: Wähle ein Jahr aus", 
            options=results['Jahr'].unique(),
            value=sim_years // 2
        )
    
    row = results[results['Jahr'] == inspect_year].iloc[0]
    monthly_net = row['Netto Dividende'] / 12
    total_net = row['Netto Dividende']
    port_val = row['Portfolio Wert']
    total_invest = row['Investiertes Kapital']
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ø Monatlich (Netto)", f"{monthly_net:,.2f} €", help="Verfügbarer Cashflow pro Monat nach Steuern")
    k2.metric("Jahressumme (Netto)", f"{total_net:,.0f} €", delta=f"{row['Yield on Cost %']:.1f}% YoC")
    k3.metric("Portfolio Wert", f"{port_val:,.0f} €")
    k4.metric("Gewinn/Verlust", f"{port_val - total_invest:,.0f} €", delta=f"{(port_val - total_invest)/total_invest*100:.0f}%" if total_invest > 0 else "0%")
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Charts Visualisierung", "Detaillierte Tabelle"])
    
    with tab1:
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("**Vermögensaufbau (Zinseszins)**")
            chart_data = results[['Jahr', 'Investiertes Kapital', 'Portfolio Wert']].set_index('Jahr')
            st.area_chart(chart_data, color=["#94a3b8", "#0d9488"]) 
        with c_right:
            st.markdown("**Netto-Dividenden-Entwicklung**")
            st.bar_chart(results.set_index('Jahr')['Netto Dividende'], color="#3b82f6") 
            
    with tab2:
        st.dataframe(
            results.style.format({
                "Investiertes Kapital": "{:,.0f} €",
                "Portfolio Wert": "{:,.0f} €",
                "Netto Dividende": "{:,.0f} €",
                "Steuern": "{:,.0f} €",
                "Yield on Cost %": "{:.2f} %"
            }), 
            use_container_width=True
        )

else:
    st.info("👆 Gib oben einen Ticker ein (z.B. 'AAPL' oder 'VNA.DE'), um zu starten.")
