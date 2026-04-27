import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# ==========================================
# 1. TÜM SEKTÖR VE ALT SEKTÖR HARİTASI
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

SUB_TICKERS = [item for sublist in GLOBAL_MAP.values() for item in sublist]

# ==========================================
# 2. QUANTUM FUSION ENGINE (V695 & V650)
# ==========================================
def scan_market(tickers, benchmark="SPY"):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60) # Analiz için yeterli derinlik
    
    # Tüm verileri (OHLCV) indir
    raw_data = yf.download(tickers + [benchmark], start=start_date, end=end_date, progress=False, group_by='ticker')
    
    results = []
    benchmark_close = raw_data[benchmark]['Close']
    
    for t in tickers:
        if t not in raw_data.columns.levels[0]: continue
        
        df = raw_data[t].copy().dropna()
        if len(df) < 25: continue
        
        # --- A. WHALE POWER HESAPLAMA (V695) ---
        # Hacim Analizi
        vol_avg = df['Volume'].rolling(window=20).mean()
        vol_std = df['Volume'].rolling(window=20).std()
        is_whale_vol = df['Volume'].iloc[-1] > (vol_avg.iloc[-1] + (vol_std.iloc[-1] * 1.5))
        
        # Mum Yapısı & Whale Power (w_pwr)
        # Formül: (Hacim / Ort. Hacim) * ((Close - Low) / (High - Low))
        spread = (df['High'] - df['Low']).replace(0, 0.001)
        w_pwr = (df['Volume'] / vol_avg) * ((df['Close'] - df['Low']) / spread)
        current_w_pwr = round(w_pwr.iloc[-1] * 100, 1)

        # --- B. OMNI FUSION SKORLAMA (V650) ---
        fusion_score = 0
        
        # 1. EMA Onayı (Fiyat > 12 EMA)
        ema12 = df['Close'].ewm(span=12, adjust=False).mean().iloc[-1]
        if df['Close'].iloc[-1] > ema12: fusion_score += 1
        
        # 2. 3-Bar Slope (Süreklilik)
        slope_up = (df['Close'].iloc[-1] > df['Close'].iloc[-2]) and (df['Close'].iloc[-2] > df['Close'].iloc[-3])
        if slope_up: fusion_score += 1
        
        # 3. Whale Power Onayı
        if current_w_pwr > 50: fusion_score += 2
        
        # 4. Hacim Patlaması
        if is_whale_vol: fusion_score += 1

        # --- C. TUZAK & SİNYAL MANTIĞI (✅/⛔) ---
        # Bull Trap: Fiyat artıyor ama Whale Power düşüyorsa
        is_bull_trap = slope_up and (w_pwr.iloc[-1] < w_pwr.iloc[-2])
        
        # RS ve Momentum
        rs = (df['Close'] / benchmark_close) * 100
        mom = ((rs.iloc[-1] / rs.iloc[-11]) - 1) * 100
        jump_score = ((rs.iloc[-1] / rs.iloc[-4]) - 1) * 100
        
        # Final Sinyal Belirleme
        if is_bull_trap:
            signal = "⛔ TRAP"
        elif fusion_score >= 4:
            signal = "💎 ANY BUY"
        elif is_whale_vol and current_w_pwr > 70:
            signal = "🐋 WHALE"
        elif fusion_score >= 2:
            signal = "✅ BUY"
        else:
            signal = "⏳"

        results.append({
            "Ticker": t,
            "Sinyal": signal,
            "Fusion Skor": fusion_score,
            "Whale Power": f"{current_w_pwr}%",
            "3G Sıçrama %": round(jump_score, 2),
            "RS Gücü": round(rs.iloc[-1], 2),
            "Momentum": round(mom, 2)
        })
        
    return pd.DataFrame(results).sort_values(by="Fusion Skor", ascending=False)

# ==========================================
# 3. KOKPİT EKRANI (MOBİL UYUMLU)
# ==========================================
st.title("📟 Quantum Radar V695")
st.write(f"**Engine:** Whale Power + Omni-Fusion | {datetime.now().strftime('%H:%M:%S')}")

if st.button("HEDEF KİLİTLE (Deep Scan)"):
    with st.spinner("Balinalar İzleniyor..."):
        scan_results = scan_market(SUB_TICKERS)
        
        # Üst Panel: Kritik Sinyaller
        st.subheader("🎯 Taktik Sinyaller")
        hits = scan_results[scan_results['Sinyal'].isin(["💎 ANY BUY", "🐋 WHALE"])]
        if not hits.empty:
            cols = st.columns(len(hits[:5]))
            for i, (_, row) in enumerate(hits[:5].iterrows()):
                with cols[i]:
                    st.metric(label=row['Ticker'], value=row['Sinyal'], delta=row['Whale Power'])
        
        st.divider()
        
        # Ana Tablo
        st.subheader("📊 Omni-Fusion Tarayıcı")
        
        # Renklendirme Fonksiyonu
        def color_signal(val):
            if val == "💎 ANY BUY": return 'background-color: #004d40; color: white'
            if val == "⛔ TRAP": return 'background-color: #4a148c; color: white'
            if val == "🐋 WHALE": return 'background-color: #01579b; color: white'
            return ''

        styled_df = scan_results.style.applymap(color_signal, subset=['Sinyal'])
        st.dataframe(styled_df, use_container_width=True)

        # Görsel Matris
        fig = px.scatter(scan_results, x="RS Gücü", y="Whale Power", text="Ticker", 
                         color="Sinyal", size="Fusion Skor",
                         title="Whale Power vs Relative Strength Matrix")
        st.plotly_chart(fig, use_container_width=True)
