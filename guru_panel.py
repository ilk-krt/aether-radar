import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# ==========================================
# 1. AYARLAR VE VERİ HARİTASI
# ==========================================
st.set_page_config(page_title="Aether V695 - Quantum Radar", layout="wide")

GLOBAL_MAP = {
    "Teknoloji (XLK)": ["SMH", "CIBR", "IGV", "BOTZ", "ARKF"],
    "Sanayi (XLI)": ["ITA", "IYT", "PAVE", "JETS"],
    "Enerji (XLE)": ["XOP", "OIH", "URA", "ICLN"],
    "Sağlık (XLV)": ["XBI", "IHI", "ARKG"],
    "Finans (XLF)": ["KRE", "KIE", "IAI"],
    "Tüketim (XLY)": ["XRT", "XHB", "IBUY", "BETZ"],
    "Materyal (XLB)": ["XME", "GDX", "LIT", "REMX"],
    "İletişim (XLC)": ["SOCL", "HERO"],
    "Gayrimenkul (XLRE)": ["SRVR", "REZ"],
    "Temel Tüketim (XLP)": ["MOO", "PBJ"],
    "Kamu (XLU)": ["PHO", "TAN"]
}

# Fon Bileşenleri (En Önemli Balinalar)
ETF_HOLDINGS = {
    "SMH": ["NVDA (Nvidia)", "TSM (Taiwan Semi)", "AVGO (Broadcom)", "ASML", "AMD"],
    "OIH": ["SLB (Schlumberger)", "HAL (Halliburton)", "BKR (Baker Hughes)", "FTI"],
    "TAN": ["FSLR (First Solar)", "ENPH (Enphase)", "NXT (Nextracker)", "SEDG"],
    "LIT": ["ALB (Albemarle)", "SQM", "BYD", "TSLA (Tesla)", "CATL"],
    "ICLN": ["BE (Bloom Energy)", "FSLR", "ENPH", "VWS (Vestas)", "PLUG"],
    "BOTZ": ["ISRG (Intuitive)", "NVDA", "ABB", "KEYENCE", "FANUC"],
    "BETZ": ["DKNG (DraftKings)", "FLUT (Flutter)", "EVO (Evolution)", "RSI"],
    "URA": ["CCJ (Cameco)", "KAP (Kazatomprom)", "UUUU", "NLR"],
    "XOP": ["XOM (Exxon)", "CVX (Chevron)", "COP (Conoco)", "EOG"]
}

SUB_TICKERS = [item for sublist in GLOBAL_MAP.values() for item in sublist]

# ==========================================
# 2. QUANTUM ENGINE (MATEMATİKSEL MOTOR)
# ==========================================
def scan_market(tickers, benchmark="SPY"):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    raw_data = yf.download(tickers + [benchmark], start=start_date, end=end_date, progress=False, group_by='ticker')
    
    results = []
    benchmark_close = raw_data[benchmark]['Close']
    
    for t in tickers:
        if t not in raw_data.columns.levels[0]: continue
        df = raw_data[t].copy().dropna()
        if len(df) < 25: continue
        
        # --- WHALE POWER (V695) ---
        vol_avg = df['Volume'].rolling(window=20).mean()
        vol_std = df['Volume'].rolling(window=20).std()
        is_whale_vol = df['Volume'].iloc[-1] > (vol_avg.iloc[-1] + (vol_std.iloc[-1] * 1.5))
        
        spread = (df['High'] - df['Low']).replace(0, 0.001)
        w_pwr = (df['Volume'] / vol_avg) * ((df['Close'] - df['Low']) / spread)
        current_w_pwr = round(w_pwr.iloc[-1] * 100, 1)

        # --- OMNI FUSION (V650) ---
        fusion_score = 0
        ema12 = df['Close'].ewm(span=12, adjust=False).mean().iloc[-1]
        if df['Close'].iloc[-1] > ema12: fusion_score += 1
        
        slope_up = (df['Close'].iloc[-1] > df['Close'].iloc[-2]) and (df['Close'].iloc[-2] > df['Close'].iloc[-3])
        if slope_up: fusion_score += 1
        if current_w_pwr > 50: fusion_score += 2
        if is_whale_vol: fusion_score += 1

        # --- TRAP & SIGNAL ---
        is_bull_trap = slope_up and (w_pwr.iloc[-1] < w_pwr.iloc[-2])
        rs = (df['Close'] / benchmark_close) * 100
        mom = ((rs.iloc[-1] / rs.iloc[-11]) - 1) * 100
        jump_score = ((rs.iloc[-1] / rs.iloc[-4]) - 1) * 100
        
        if is_bull_trap: signal = "⛔ TRAP"
        elif fusion_score >= 4: signal = "💎 ANY BUY"
        elif is_whale_vol and current_w_pwr > 70: signal = "🐋 WHALE"
        elif fusion_score >= 2: signal = "✅ BUY"
        else: signal = "⏳"

        results.append({
            "Ticker": t,
            "Sinyal": signal,
            "Fusion Skor": fusion_score,
            "Whale Power": current_w_pwr,
            "3G Sıçrama %": round(jump_score, 2),
            "RS Gücü": round(rs.iloc[-1], 2),
            "Momentum": round(mom, 2)
        })
        
    return pd.DataFrame(results).sort_values(by="Fusion Skor", ascending=False)

# ==========================================
# 3. KOKPİT EKRANI (MOBİL ODAKLI)
# ==========================================
st.title("📟 Quantum Radar V695")
st.write(f"**Engine:** Whale + Fusion | {datetime.now().strftime('%H:%M')}")

# Telefon hafızası: Tarama verilerini session_state içinde tut
if st.button("HEDEF KİLİTLE (Deep Scan)"):
    with st.spinner("Balinalar İzleniyor..."):
        st.session_state.scan_results = scan_market(SUB_TICKERS)

if "scan_results" in st.session_state:
    res = st.session_state.scan_results

    # Üst Panel: Kritik Sinyaller (Metrics)
    hits = res[res['Sinyal'].isin(["💎 ANY BUY", "🐋 WHALE"])].head(3)
    if not hits.empty:
        m_cols = st.columns(len(hits))
        for idx, (_, row) in enumerate(hits.iterrows()):
            with m_cols[idx]:
                st.metric(label=row['Ticker'], value=row['Sinyal'], delta=f"{row['Whale Power']}%")

    st.divider()

    # Ana Tablo (Tıklama Özellikli)
    st.subheader("📊 Omni-Fusion Tarayıcı")
    st.caption("💡 Detay ve hisseler için satıra tıkla.")

    def color_signal(val):
        if val == "💎 ANY BUY": return 'background-color: #004d40; color: white'
        if val == "⛔ TRAP": return 'background-color: #4a148c; color: white'
        if val == "🐋 WHALE": return 'background-color: #01579b; color: white'
        return ''

    # Seçim mekanizması
    selection_event = st.dataframe(
        res.style.map(color_signal, subset=['Sinyal']),
        use_container_width=True,
        on_select="rerun",
        selection_mode="single_row",
        key="main_table"
    )

    # Detay Paneli (Sadece seçim varsa görünür)
    if selection_event.selection.rows:
        selected_idx = selection_event.selection.rows[0]
        ticker = res.iloc[selected_idx]['Ticker']
        
        st.success(f"🔍 **{ticker} Analiz Paneli**")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Fusion Skoru:** {res.iloc[selected_idx]['Fusion Skor']}/5")
            st.write(f"**Whale Power:** %{res.iloc[selected_idx]['Whale Power']}")
        with c2:
            st.write("**Bileşen Balinalar (Top Holdings):**")
            holdings = ETF_HOLDINGS.get(ticker, ["Veri mevcut değil."])
            for h in holdings:
                st.write(f"• {h}")
        st.divider()

    # Grafik
    fig = px.scatter(res, x="RS Gücü", y="Whale Power", text="Ticker", 
                     color="Sinyal", size="Fusion Skor", title="Piyasa Matrisi")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Lütfen 'Deep Scan' butonuna basarak taramayı başlatın.")
