import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import numpy as np
from datetime import datetime, timedelta

# --- KONFIGURATION ---
st.set_page_config(
    page_title="Dividend Master DE",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-card {
        background-color: #262730;
        border: 1px solid #4b5563;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        height: 100%;
        display: flex; flex-direction: column; justify-content: center;
    }
    .metric-label { color: #9ca3af; font-size: 0.85rem; text-transform: uppercase; font-weight: 700; margin-bottom: 5px; }
    .metric-value { color: #f3f4f6; font-size: 1.8rem; font-weight: 800; }
    .metric-sub { color: #6b7280; font-size: 0.8rem; margin-top: 5px; }
    .highlight-teal { color: #2dd4bf; }
    .highlight-blue { color: #60a5fa; }
    .highlight-purple { color: #c084fc; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=[
        'Ticker', 'Name', 'Anteile', 'Kaufkurs', 'Aktueller Kurs', 
        'Div Rendite %', 'Div Wachs. %', 'Kurs Wachs. %', 
        'Sparrate €', 'Intervall', 'Reinvest'
    ])

# --- PROFESSIONAL YFINANCE FETCHING (v2.0 optimized) ---

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(ticker_symbol):
    """
    Holt Daten via yfinance 'fast_info' und berechnet Yield manuell über Historie (TTM).
    Viel robuster als .info Scraping.
    """
    clean_ticker = ticker_symbol.upper().strip()
    
    try:
        # 1. Custom Session (immer gut gegen Blocks)
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        stock = yf.Ticker(clean_ticker, session=session)
        
        # --- A. PREIS (Nutze fast_info, das ist sehr zuverlässig) ---
        price = None
        try:
            # fast_info triggert keinen Web-Scrape, sondern nutzt API-Metadaten
            price = stock.fast_info.last_price
        except:
            pass
            
        # Fallback auf History, falls fast_info leer (z.B. bei manchen ETFs)
        if price is None:
            hist = stock.history(period="5d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
        
        if price is None:
            raise ValueError(f"Kein Preis für {clean_ticker} ermittelbar.")

        # --- B. DIVIDENDE (Berechne TTM - Trailing Twelve Months) ---
        # Das ist genauer als .info['dividendYield'], welches oft fehlt
        yield_percent = 0.0
        freq = 1
        
        try:
            # Hole Dividenden-Historie
            divs = stock.dividends
            if not divs.empty:
                # Zeitzone normalisieren für Vergleich
                now = pd.Timestamp.now().tz_localize(divs.index.tz)
                one_year_ago = now - pd.Timedelta(days=365)
                
                # Summiere alles im letzten Jahr
                last_12m_divs = divs[divs.index >= one_year_ago]
                
                ttm_div_sum = last_12m_divs.sum()
                count = len(last_12m_divs)
                
                if price > 0:
                    yield_percent = (ttm_div_sum / price) * 100
                
                # Frequenz ableiten
                if count >= 10: freq = 12   # Monthly
                elif count >= 3: freq = 4   # Quarterly
                elif count >= 2: freq = 2   # Semi-Annual
                elif count >= 1: freq = 1   # Annual
        except Exception as e:
            # Wenn Berechnung fehlschlägt, versuche .info als allerletzten Strohhalm
            try:
                info = stock.info
                yield_percent = (info.get('dividendYield') or 0) * 100
            except:
                pass

        # --- C. NAME ---
        name = clean_ticker
        try:
            # Versuche Name zu holen, aber lass es nicht crashen wenn es fehlschlägt
            # Wir nutzen fast_info headers oder fallback info
            # Leider hat fast_info keinen Namen, daher vorsichtiger .info call
            # Wir nutzen einen Trick: Wenn der User .DE eingibt, ist es oft klar
            info = stock.info
            name = info.get('shortName') or info.get('longName') or clean_ticker
        except:
            pass

        return {
            'Ticker': clean_ticker,
            'Name': name,
            'Aktueller Kurs': float(price),
            'Kaufkurs': float(price),
            'Div Rendite %': round(float(yield_percent), 2),
            'Intervall': freq,
            'Div Wachs. %': 5.0, 
            'Kurs Wachs. %': 6.0, 
            'Sparrate €': 0.0,
            'Reinvest': True
        }

    except Exception as e:
        print(f"ERROR bei {clean_ticker}: {e}")
        return None

def calculate_projection(df, years, pauschbetrag):
    months = years * 12
    projections = []
    
    sim = df.copy()
    
    # Initiale Basiswerte
    sim['Jahresdiv_Pro_Aktie'] = sim['Aktueller Kurs'] * (sim['Div Rendite %'] / 100)
    current_shares = sim['Anteile'].astype(float).to_dict()
    
    invested_capital = (sim['Anteile'] * sim['Kaufkurs']).sum()
    current_pausch = pauschbetrag
    
    year_net = 0
    year_tax = 0
    
    # Simulation Loop
    for m in range(1, months + 1):
        # Jahresabschluss & Reporting
        if (m - 1) % 12 == 0 and m > 1:
            curr_port_val = sum(current_shares[t] * sim.loc[sim['Ticker']==t, 'Aktueller Kurs'].values[0] for t in current_shares)
            
            projections.append({
                'Jahr': (m-1)//12,
                'Investiertes Kapital': invested_capital,
                'Portfolio Wert': curr_port_val,
                'Netto Dividende': year_net,
                'Steuern': year_tax,
                'Yield on Cost %': (year_net / invested_capital * 100) if invested_capital > 0 else 0
            })
            
            # Reset für neues Jahr
            year_net = 0
            year_tax = 0
            current_pausch = pauschbetrag
            
            # Wachstum anwenden (Step-Up am Jahresanfang)
            sim['Aktueller Kurs'] *= (1 + sim['Kurs Wachs. %'] / 100)
            sim['Jahresdiv_Pro_Aktie'] *= (1 + sim['Div Wachs. %'] / 100)

        month_idx = ((m - 1) % 12) + 1
        monthly_invest = 0
        
        for idx, row in sim.iterrows():
            ticker = row['Ticker']
            freq = int(row['Intervall'])
            
            # 1. Sparplan
            spar = row['Sparrate €']
            if spar > 0:
                shares_new = spar / row['Aktueller Kurs']
                current_shares[ticker] += shares_new
                monthly_invest += spar
            
            # 2. Dividende
            pays = False
            if freq == 12: pays = True
            elif freq == 4 and month_idx % 3 == 0: pays = True
            elif freq == 1 and month_idx == 5: pays = True
            elif freq == 2 and month_idx % 6 == 0: pays = True
            
            if pays:
                gross = current_shares[ticker] * (row['Jahresdiv_Pro_Aktie'] / freq)
                if gross > 0:
                    # Steuer DE Logik
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
                    
                    # Reinvestition
                    if row['Reinvest']:
                        drip_shares = net / row['Aktueller Kurs']
                        current_shares[ticker] += drip_shares
        
        invested_capital += monthly_invest

    # Finaler Eintrag
    curr_port_val = sum(current_shares[t] * sim.loc[sim['Ticker']==t, 'Aktueller Kurs'].values[0] for t in current_shares)
    projections.append({
        'Jahr': years,
        'Investiertes Kapital': invested_capital,
        'Portfolio Wert': curr_port_val,
        'Netto Dividende': year_net,
        'Steuern': year_tax,
        'Yield on Cost %': (year_net / invested_capital * 100) if invested_capital > 0 else 0
    })
    
    return pd.DataFrame(projections)

# --- UI LAYOUT ---

with st.sidebar:
    st.header("⚙️ Einstellungen")
    pausch = st.number_input("Sparerpauschbetrag (€)", 0, 10000, 1000, step=100)
    
    if not st.session_state.portfolio.empty:
        st.divider()
        csv = st.session_state.portfolio.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Portfolio CSV Export", csv, "portfolio.csv", "text/csv")
        
    uploaded_file = st.file_uploader("📂 Portfolio CSV Import", type=["csv"])
    if uploaded_file:
        try:
            df_up = pd.read_csv(uploaded_file)
            st.session_state.portfolio = df_up
            st.success("Geladen!")
        except:
            st.error("Fehler beim Laden.")

st.title("Dividend Master DE 🇩🇪")
st.markdown("##### 🚀 100% Live-Daten via yfinance API")

# Input Section
c1, c2 = st.columns([3,1])
with c1:
    new_ticker = st.text_input("Ticker Symbol", placeholder="z.B. O, MSFT, ALV.DE", label_visibility="collapsed")
with c2:
    if st.button("Daten abrufen 🔎", type="primary", use_container_width=True):
        if new_ticker:
            with st.spinner(f"Verbinde mit Börse für {new_ticker}..."):
                data = get_stock_data(new_ticker)
                
                if data:
                    st.session_state.portfolio = pd.concat([
                        st.session_state.portfolio, 
                        pd.DataFrame([data])
                    ], ignore_index=True)
                    st.success(f"{data['Name']} hinzugefügt! Kurs: {data['Aktueller Kurs']}€")
                    st.rerun()
                else:
                    st.error(f"Konnte keine Daten für '{new_ticker}' finden. Bitte Ticker prüfen (z.B. .DE für Deutschland).")

# Portfolio Table
if not st.session_state.portfolio.empty:
    st.markdown("### Dein Portfolio")
    
    edited = st.data_editor(
        st.session_state.portfolio,
        column_config={
            "Ticker": st.column_config.TextColumn(disabled=True),
            "Name": st.column_config.TextColumn(disabled=True),
            "Kaufkurs": st.column_config.NumberColumn("Ø Kauf €", format="%.2f €"),
            "Aktueller Kurs": st.column_config.NumberColumn("Kurs €", format="%.2f €", disabled=True),
            "Anteile": st.column_config.NumberColumn(format="%.2f"),
            "Div Rendite %": st.column_config.NumberColumn("Div %", format="%.2f %%"),
            "Sparrate €": st.column_config.NumberColumn("Sparrate", format="%.0f €"),
            "Intervall": st.column_config.SelectboxColumn("Zyklus", options=[1,2,4,12]),
            "Reinvest": st.column_config.CheckboxColumn("Auto-Reinvest", default=True)
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic"
    )
    st.session_state.portfolio = edited
    
    # Calculation
    years = st.slider("Prognose (Jahre)", 5, 40, 15)
    results = calculate_projection(edited, years, pausch)
    
    # KPI Metrics
    curr_inv = (edited['Anteile'] * edited['Kaufkurs']).sum()
    curr_val = (edited['Anteile'] * edited['Aktueller Kurs']).sum()
    
    st.divider()
    k1, k2, k3 = st.columns(3)
    k1.metric("Investiertes Kapital", f"{curr_inv:,.0f} €")
    k2.metric("Aktueller Wert", f"{curr_val:,.0f} €")
    k3.metric("Performance", f"{curr_val - curr_inv:,.0f} €", delta=f"{(curr_val-curr_inv)/curr_inv*100:.1f}%" if curr_inv>0 else "0%")
    
    # Visualization Tabs
    tab1, tab2 = st.tabs(["📊 Charts", "📋 Tabelle"])
    
    with tab1:
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("**Vermögensentwicklung**")
            chart_data = results[['Jahr', 'Investiertes Kapital', 'Portfolio Wert']].set_index('Jahr')
            st.area_chart(chart_data, color=["#6b7280", "#2dd4bf"])
        with c_right:
            st.markdown("**Netto-Dividende (nach Steuern)**")
            st.bar_chart(results.set_index('Jahr')['Netto Dividende'], color="#60a5fa")
            
    with tab2:
        st.dataframe(results.style.format("{:,.0f}"), use_container_width=True)

else:
    st.info("👆 Gib einen Ticker ein, um echte Live-Daten zu laden.")
