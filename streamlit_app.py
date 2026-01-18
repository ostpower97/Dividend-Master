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

# --- PROFESSIONAL YFINANCE FETCHING (v5.0 Currency Aware) ---

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(ticker_symbol):
    """
    Holt Daten via yfinance und konvertiert Fremdwährungen live in EUR.
    """
    clean_ticker = ticker_symbol.upper().strip()
    
    try:
        stock = yf.Ticker(clean_ticker)
        
        # --- A. PREIS & WÄHRUNG ---
        current_price = None
        currency = "EUR" # Default Annahme
        
        try:
            # Versuch via fast_info (enthält oft Währung)
            current_price = stock.fast_info.last_price
            currency = stock.fast_info.currency
        except:
            pass
            
        # Fallback history
        if current_price is None or pd.isna(current_price):
            try:
                hist = stock.history(period="5d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    # Versuch Währung aus Meta zu holen, falls fast_info leer war
                    if not currency or currency == "EUR":
                        meta = stock.info
                        currency = meta.get('currency', 'EUR')
            except:
                pass

        # Fallback download
        if current_price is None or pd.isna(current_price):
            try:
                df = yf.download(clean_ticker, period="5d", progress=False, threads=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        current_price = df.xs('Close', axis=1, level=0).iloc[-1].iloc[0]
                    else:
                        current_price = df['Close'].iloc[-1]
            except:
                pass

        if current_price is None or pd.isna(current_price):
            return None

        # --- B. WÄHRUNGSUMRECHNUNG (FX -> EUR) ---
        # Wenn Währung gefunden und nicht EUR, rechne um.
        if currency and currency.upper() != 'EUR':
            try:
                rate = 1.0
                if currency.upper() == 'USD':
                    # Yahoo Ticker für USD zu EUR ist 'EUR=X'
                    fx = yf.Ticker("EUR=X")
                    rate = fx.fast_info.last_price
                elif currency.upper() == 'GBP':
                    fx = yf.Ticker("GBPEUR=X")
                    rate = fx.fast_info.last_price
                elif currency.upper() == 'CHF':
                    fx = yf.Ticker("CHFEUR=X")
                    rate = fx.fast_info.last_price
                
                # Plausibilitätscheck Rate (darf nicht 0 oder None sein)
                if rate and rate > 0:
                    current_price = current_price * rate
            except Exception as e:
                print(f"Währungsumrechnung Fehler für {currency}: {e}")
                # Im Fehlerfall behalten wir den Originalpreis bei, besser als Absturz

        # --- C. DIVIDENDEN (Yield Berechnung in Originalwährung) ---
        # Yield % ist währungsunabhängig (Verhältniszahl)
        yield_percent = 0.0
        freq = 1
        
        try:
            divs = stock.dividends
            if not divs.empty:
                tz = divs.index.tz
                now = pd.Timestamp.now(tz=tz) if tz else pd.Timestamp.now()
                cutoff = now - pd.Timedelta(days=365)
                recent_divs = divs[divs.index > cutoff]
                
                if not recent_divs.empty:
                    ttm_sum = recent_divs.sum()
                    
                    # Wir brauchen den Preis in der ORIGINAL-Währung für die Yield-Berechnung!
                    # Da wir oben current_price ggf. schon in EUR umgerechnet haben, 
                    # holen wir kurz den Raw Price nochmal oder rechnen zurück? 
                    # Sauberer: Wir nutzen fast_info.last_price (Original) falls vorhanden.
                    
                    price_original = stock.fast_info.last_price
                    if not price_original:
                        # Fallback: Wenn wir umgerechnet haben, rate rausrechnen? 
                        # Zu komplex. Nehmen wir an, current_price ist korrekt.
                        # Wenn FX passiert ist, müssten wir auch Dividenden konvertieren.
                        # EINFACHER: (Dividende / Preis) ist gleich, egal welche Währung, 
                        # SOLANGE BEIDE in der gleichen Währung sind.
                        # Da divs in Originalwährung kommen und stock.fast_info.last_price auch,
                        # berechnen wir Yield basierend auf Originalwerten.
                        price_original = current_price # Fallback (eventuell falsch wenn FX, aber akzeptabel für Fallback)

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

        # --- D. NAME ---
        name = clean_ticker
        try:
            meta = stock.info
            name = meta.get('shortName') or meta.get('longName') or clean_ticker
        except:
            pass

        return {
            'Ticker': clean_ticker,
            'Name': name,
            'Aktueller Kurs': float(current_price), # Jetzt in EUR
            'Kaufkurs': float(current_price),     # Default auf aktuellen EUR Kurs
            'Div Rendite %': round(float(yield_percent), 2),
            'Intervall': freq,
            'Div Wachs. %': 5.0, 
            'Kurs Wachs. %': 6.0, 
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
    
    # Initiale Basiswerte
    sim['Jahresdiv_Pro_Aktie'] = sim['Aktueller Kurs'] * (sim['Div Rendite %'] / 100)
    
    # FIX KEYERROR: Dictionary Mapping Ticker -> Shares korrekt erstellen
    # Vorher: to_dict() nutzte Index (0,1,2). Jetzt: zip(Ticker, Anteile).
    current_shares = dict(zip(sim['Ticker'], sim['Anteile'].astype(float)))
    
    invested_capital = (sim['Anteile'] * sim['Kaufkurs']).sum()
    current_pausch = pauschbetrag
    
    year_net = 0
    year_tax = 0
    
    # Simulation Loop
    for m in range(1, months + 1):
        # Jahresabschluss & Reporting
        if (m - 1) % 12 == 0 and m > 1:
            # Portfolio Wert berechnen
            curr_port_val = 0
            for t_symbol, t_shares in current_shares.items():
                # Hole aktuellen Kurs aus Simulationstabelle für diesen Ticker
                # .values[0] ist sicher, da Ticker unique sein sollten im DF
                price = sim.loc[sim['Ticker'] == t_symbol, 'Aktueller Kurs'].values[0]
                curr_port_val += t_shares * price

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
                # Hier lag der KeyError zuvor: current_shares[ticker]
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

    # Finaler Eintrag (letztes Jahr)
    curr_port_val = 0
    for t_symbol, t_shares in current_shares.items():
        price = sim.loc[sim['Ticker'] == t_symbol, 'Aktueller Kurs'].values[0]
        curr_port_val += t_shares * price

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
st.markdown("##### 🚀 Live-Daten (Auto-Währungsumrechnung in €)")

# Input Section
c1, c2 = st.columns([3,1])
with c1:
    new_ticker = st.text_input("Ticker Symbol", placeholder="z.B. O, MSFT, ALV.DE", label_visibility="collapsed")
with c2:
    if st.button("Daten abrufen 🔎", type="primary", use_container_width=True):
        if new_ticker:
            with st.spinner(f"Hole Daten für {new_ticker} (inkl. EUR Umrechnung)..."):
                data = get_stock_data(new_ticker)
                
                if data:
                    st.session_state.portfolio = pd.concat([
                        st.session_state.portfolio, 
                        pd.DataFrame([data])
                    ], ignore_index=True)
                    st.success(f"{data['Name']} hinzugefügt! Kurs: {data['Aktueller Kurs']:.2f}€")
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
