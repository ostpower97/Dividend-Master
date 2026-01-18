import streamlit as st
import pandas as pd
import yfinance as yf
import os
import time

# --- 1. CONFIG & CSS (FORCE LIGHT THEME & MOBILE OPTIMIZATION) ---
st.set_page_config(
    page_title="Dividend Master",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Force Light Mode Background & Text */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    /* Input Fields White */
    input, select, textarea, [data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
    }
    
    /* Cards / Containers White */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }

    /* DataFrame / Editor White */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
    }

    /* Buttons */
    button[kind="primary"] {
        background-color: #0f172a !important;
        color: white !important;
        border: none !important;
        transition: opacity 0.2s;
    }
    button[kind="primary"]:hover {
        opacity: 0.9;
    }
    
    /* Hide default header/footer for app-feel */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Mobile Padding Fixes */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA PERSISTENCE (LOCAL STORAGE) ---
CSV_FILE = "my_portfolio.csv"

def get_empty_portfolio():
    return pd.DataFrame(columns=[
        'Ticker', 'Name', 'Anteile', 'Kaufkurs', 'Aktueller Kurs', 
        'Div Rendite %', 'Div Wachs. %', 'Kurs Wachs. %', 
        'Sparrate €', 'Intervall', 'Reinvest'
    ])

def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # Ensure all columns exist (migration safe)
            defaults = get_empty_portfolio()
            for col in defaults.columns:
                if col not in df.columns:
                    df[col] = defaults[col]
            return df
        except:
            pass
    return get_empty_portfolio()

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Init Session State
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = load_data()

# --- 3. MARKET DATA ENGINE (yfinance - ON DEMAND) ---
def update_market_data(df):
    """Holt frische Daten von yfinance und aktualisiert das DataFrame."""
    if df.empty:
        return df
    
    updated_df = df.copy()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(df)
    
    for i, row in df.iterrows():
        ticker = row['Ticker']
        status_text.caption(f"Lade Daten für {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            
            # 1. Price
            price = None
            try:
                price = stock.fast_info.last_price
            except:
                try:
                    price = stock.history(period="1d")['Close'].iloc[-1]
                except:
                    pass
            
            if price:
                updated_df.at[i, 'Aktueller Kurs'] = float(price)
            
            # 2. Dividend Yield
            try:
                info = stock.info
                if 'dividendYield' in info and info['dividendYield']:
                    updated_df.at[i, 'Div Rendite %'] = round(info['dividendYield'] * 100, 2)
            except:
                pass
                
            # 3. Name fallback
            if pd.isna(row['Name']) or row['Name'] == ticker:
                try:
                    name = stock.info.get('shortName') or stock.info.get('longName')
                    if name:
                        updated_df.at[i, 'Name'] = name
                except:
                    pass

        except Exception as e:
            print(f"Error updating {ticker}: {e}")
            
        progress_bar.progress((i + 1) / total)
        
    status_text.empty()
    progress_bar.empty()
    return updated_df

def add_new_stock(ticker_input):
    clean = ticker_input.upper().strip()
    if clean in st.session_state.portfolio['Ticker'].values:
        st.warning("Aktie bereits im Portfolio.")
        return

    try:
        with st.spinner(f"Suche {clean}..."):
            stock = yf.Ticker(clean)
            # Check if valid by fetching minimal history
            hist = stock.history(period="1d")
            if hist.empty:
                st.error(f"Konnte {clean} nicht finden.")
                return

            price = hist['Close'].iloc[-1]
            
            # Metadata
            info = stock.info
            name = info.get('shortName', clean)
            div_yield = (info.get('dividendYield', 0) or 0) * 100
            
            new_row = {
                'Ticker': clean,
                'Name': name,
                'Anteile': 0.0,
                'Kaufkurs': float(price),
                'Aktueller Kurs': float(price),
                'Div Rendite %': round(div_yield, 2),
                'Div Wachs. %': 5.0, # Default estimate
                'Kurs Wachs. %': 7.0, # Default estimate
                'Sparrate €': 0.0,
                'Intervall': 1, # Annual default
                'Reinvest': True
            }
            
            st.session_state.portfolio = pd.concat([st.session_state.portfolio, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.portfolio)
            st.success(f"{clean} hinzugefügt!")
            time.sleep(0.5)
            st.rerun()
            
    except Exception as e:
        st.error(f"Fehler: {str(e)}")

# --- 4. UI COMPONENTS ---

def render_mobile_card(index, row):
    """Renders a single stock as a nice card (Mobile Optimized)"""
    with st.container(border=True):
        # Header: Symbol + Name + Delete Button
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"**{row['Ticker']}** <span style='color:gray; font-size:0.8em'>{row['Name']}</span>", unsafe_allow_html=True)
        with c2:
            if st.button("🗑️", key=f"del_{index}", help="Löschen"):
                st.session_state.portfolio = st.session_state.portfolio.drop(index).reset_index(drop=True)
                save_data(st.session_state.portfolio)
                st.rerun()

        st.divider()
        
        # Main Data Grid
        c_left, c_right = st.columns(2)
        
        with c_left:
            new_shares = st.number_input("Anteile", value=float(row['Anteile']), key=f"shares_{index}", step=1.0)
            new_spar = st.number_input("Sparrate (€)", value=float(row['Sparrate €']), key=f"spar_{index}", step=25.0)
            
        with c_right:
            # Display only (updated via refresh button)
            st.markdown(f"""
            <div style='text-align:right'>
                <div style='font-size:0.8em; color:gray'>Kurs</div>
                <div style='font-weight:bold'>{row['Aktueller Kurs']:.2f} €</div>
                <div style='font-size:0.8em; color:gray; margin-top:8px'>Div. Rendite</div>
                <div style='font-weight:bold; color:#059669'>{row['Div Rendite %']:.2f} %</div>
            </div>
            """, unsafe_allow_html=True)

        # Update State if inputs changed
        if new_shares != row['Anteile'] or new_spar != row['Sparrate €']:
            st.session_state.portfolio.at[index, 'Anteile'] = new_shares
            st.session_state.portfolio.at[index, 'Sparrate €'] = new_spar
            save_data(st.session_state.portfolio)
            # No rerun needed immediately, feels smoother

        with st.expander("⚙️ Details & Prognose-Werte"):
            col_a, col_b = st.columns(2)
            with col_a:
                new_div_growth = st.number_input("Div. Wachstum %", value=float(row['Div Wachs. %']), key=f"dg_{index}")
                new_reinvest = st.checkbox("Reinvestieren?", value=bool(row['Reinvest']), key=f"ri_{index}")
            with col_b:
                new_price_growth = st.number_input("Kurs Wachstum %", value=float(row['Kurs Wachs. %']), key=f"pg_{index}")
                new_freq = st.selectbox("Ausschüttung", options=[1, 4, 12], index={1:0, 4:1, 12:2}.get(row['Intervall'], 0), key=f"fq_{index}")

            # Save expanded changes
            if (new_div_growth != row['Div Wachs. %'] or new_price_growth != row['Kurs Wachs. %'] or 
                new_reinvest != row['Reinvest'] or new_freq != row['Intervall']):
                st.session_state.portfolio.at[index, 'Div Wachs. %'] = new_div_growth
                st.session_state.portfolio.at[index, 'Kurs Wachs. %'] = new_price_growth
                st.session_state.portfolio.at[index, 'Reinvest'] = new_reinvest
                st.session_state.portfolio.at[index, 'Intervall'] = new_freq
                save_data(st.session_state.portfolio)


# --- 5. MAIN APP LAYOUT ---

# Top Bar
col_logo, col_refresh = st.columns([3, 1])
with col_logo:
    st.title("Dividend Master")
with col_refresh:
    st.write("") # Spacer
    if st.button("🔄 Preise Update"):
        with st.spinner("Aktualisiere Markt..."):
            st.session_state.portfolio = update_market_data(st.session_state.portfolio)
            save_data(st.session_state.portfolio)
        st.rerun()

# Add Stock Expander
with st.expander("➕ Neue Aktie hinzufügen", expanded=st.session_state.portfolio.empty):
    with st.form("add_stock_form"):
        c1, c2 = st.columns([3, 1])
        ticker_in = c1.text_input("Ticker (z.B. O, MSFT)", placeholder="US-Ticker oder .DE")
        submitted = st.form_submit_button("Hinzufügen", type="primary")
        if submitted and ticker_in:
            add_new_stock(ticker_in)

# Calculations
df = st.session_state.portfolio
total_invest = (df['Anteile'] * df['Kaufkurs']).sum()
current_value = (df['Anteile'] * df['Aktueller Kurs']).sum()
annual_div_gross = (df['Anteile'] * df['Aktueller Kurs'] * (df['Div Rendite %']/100)).sum()
monthly_savings = df['Sparrate €'].sum()

# Dashboard Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Portfolio Wert", f"{current_value:,.2f} €", delta=f"{current_value-total_invest:,.2f} €")
m2.metric("Jahresdividende (Brutto)", f"{annual_div_gross:,.2f} €", delta=f"{(annual_div_gross/current_value*100) if current_value>0 else 0:.2f} % Rendite")
m3.metric("Sparrate / Monat", f"{monthly_savings:,.0f} €")

st.divider()

# VIEW TABS
tab_cards, tab_table, tab_sim = st.tabs(["📱 Portfolio", "📝 Editor (Tabelle)", "📊 Prognose"])

# TAB 1: MOBILE CARDS
with tab_cards:
    if df.empty:
        st.info("Dein Portfolio ist leer.")
    else:
        for idx, row in df.iterrows():
            render_mobile_card(idx, row)

# TAB 2: DESKTOP TABLE
with tab_table:
    st.caption("Excel-ähnlicher Editor für schnelle Änderungen an vielen Werten.")
    edited_df = st.data_editor(
        df,
        key="data_editor",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Ticker": st.column_config.TextColumn(disabled=True),
            "Aktueller Kurs": st.column_config.NumberColumn(format="%.2f €", disabled=True),
            "Anteile": st.column_config.NumberColumn(format="%.4f"),
            "Div Rendite %": st.column_config.NumberColumn(format="%.2f %%"),
            "Sparrate €": st.column_config.NumberColumn(format="%.2f €"),
        }
    )
    if not edited_df.equals(df):
        st.session_state.portfolio = edited_df
        save_data(edited_df)
        st.rerun()

# TAB 3: PROGNOSE
with tab_sim:
    st.header("Zinseszins Simulation")
    years = st.slider("Jahre", 5, 40, 15)
    pausch = st.number_input("Freibetrag", 0, 10000, 1000)
    
    if not df.empty:
        # Simple Simulation Logic inside view for performance
        sim_data = []
        
        # Local copies
        sim_shares = df['Anteile'].values.copy()
        sim_prices = df['Aktueller Kurs'].values.copy()
        sim_div_yields = df['Div Rendite %'].values.copy() / 100
        sim_div_growths = df['Div Wachs. %'].values.copy() / 100
        sim_price_growths = df['Kurs Wachs. %'].values.copy() / 100
        sim_savings = df['Sparrate €'].values.copy()
        sim_reinvest = df['Reinvest'].values.copy()
        sim_freqs = df['Intervall'].values.copy()
        
        sim_div_per_share = sim_prices * sim_div_yields
        
        accumulated_net = 0
        
        for y in range(1, years + 1):
            year_gross = 0
            year_net = 0
            
            # 1. Sparpläne (vereinfacht am Jahresanfang für Performance)
            shares_bought = (sim_savings * 12) / sim_prices
            sim_shares += shares_bought
            
            # 2. Dividenden
            gross_payouts = sim_shares * sim_div_per_share
            total_gross = gross_payouts.sum()
            
            # Steuer
            taxable = max(0, total_gross - pausch)
            tax = taxable * 0.26375
            net_income = total_gross - tax
            
            # 3. Reinvest
            # Distribute net income proportionally to stocks marked as Reinvest
            reinvest_indices = np.where(sim_reinvest)[0]
            if len(reinvest_indices) > 0 and net_income > 0:
                # Naive distribution: Reinvest into the stock that paid it? 
                # Or distribute total net back into portfolio?
                # Prompt said: "Wenn Reinvest aktiv ist, wird Netto genutz um neue Anteile DIESES Titels zu kaufen"
                
                # We need to calculate tax per stock essentially, but tax is global.
                # Simplification: Effective Tax Rate applied to each stock
                eff_tax_rate = tax / total_gross if total_gross > 0 else 0
                
                for idx in reinvest_indices:
                    gross_stock = gross_payouts[idx]
                    net_stock = gross_stock * (1 - eff_tax_rate)
                    new_shares_drip = net_stock / sim_prices[idx]
                    sim_shares[idx] += new_shares_drip
            
            # Update Metrics for next year
            sim_prices *= (1 + sim_price_growths)
            sim_div_per_share *= (1 + sim_div_growths)
            
            portfolio_value = (sim_shares * sim_prices).sum()
            
            sim_data.append({
                "Jahr": y,
                "Dividende (Netto)": net_income,
                "Portfolio Wert": portfolio_value
            })
            
        sim_df = pd.DataFrame(sim_data)
        
        st.bar_chart(sim_df.set_index("Jahr")["Dividende (Netto)"], color="#0f172a")
        st.area_chart(sim_df.set_index("Jahr")["Portfolio Wert"], color="#2563eb")
        st.dataframe(sim_df.style.format("{:.0f}"), use_container_width=True)

