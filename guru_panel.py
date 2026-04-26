import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ==========================================
# 1. TÜM SEKTÖR VE ALT SEKTÖR HARİTASI
# ==========================================
st.set_page_config(page_title="Aether V131.0 - Quantum Radar", layout="wide")

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
# 2. MANUEL HESAPLAMA MOTORU (NO PANDAS_TA)
# ==========================================
def scan_market(tickers, benchmark="SPY"):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=200)
    data = yf.download(tickers + [benchmark], start=start_date, end=end_date, progress=False)['Close']
    
    results = []
    for t in tickers:
        if t not in data.columns: continue
        
        # RS ve Momentum Hesaplama (Manuel)
        rs = (data[t] / data[benchmark]) * 100
        # ROC (Momentum) = ((Bugün / 10 Gün Önce) - 1) * 100
        mom = ((rs.iloc[-1] / rs.iloc[-11]) - 1) * 100
        jump_score = ((rs.iloc[-1] / rs.iloc[-4]) - 1) * 100
        
        # Aether Logic (Sophisticated 3)
        prices = data[t].dropna()
        # EMA Hesaplama: pandas ewm
        ema1 = prices.iloc[-1] # 1 periyotluk EMA fiyattır
        ema12 = prices.ewm(span=12, adjust=False).mean().iloc[-1]
        
        # 3-Bar Slope Rule
        slope = (prices.iloc[-1] > prices.iloc[-2]) and (prices.iloc[-2] > prices.iloc[-3])
        
        signal = "✅ BUY" if (ema1 > ema12) and slope else "⏳"
        
        status = "NORMAL"
        if jump_score > 2: status = "🚨 SIÇRAMA (JUMP)"
        elif mom > 1: status = "🔥 SICAK PARA"
        elif mom < -1: status = "❄️ ÇIKIŞ"

        results.append({
            "Ticker": t,
            "RS Gücü": round(rs.iloc[-1], 2),
            "Momentum": round(mom, 2),
            "3G Sıçrama %": round(jump_score, 2),
            "Durum": status,
            "Aether Sinyal": signal
        })
    return pd.DataFrame(results).sort_values(by="3G Sıçrama %", ascending=False)

# ==========================================
# 3. KOKPİT EKRANI
# ==========================================
st.title("📟 Quantum Radar - Smart Money Tracker")
st.write(f"**Mod:** Python 3.14 Manual Override | **Tarih:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if st.button("Tüm Pazarı Tara (Deep Scan)"):
    with st.spinner("Sistemler Kontrol Ediliyor..."):
        scan_results = scan_market(SUB_TICKERS)
        
        st.subheader("🚀 Anlık Sıçrama Yapan Alt Sektörler")
        jumps = scan_results[scan_results['3G Sıçrama %'] > 1.5].head(5)
        if not jumps.empty:
            cols = st.columns(len(jumps))
            for i, (_, row) in enumerate(jumps.iterrows()):
                with cols[i]:
                    st.metric(label=row['Ticker'], value=f"{row['3G Sıçrama %']}%", delta="SIÇRAMA")
        
        st.divider()
        st.subheader("📊 Global Sektör Rütbelendirme")
        st.dataframe(scan_results, use_container_width=True)

        fig = px.scatter(scan_results, x="RS Gücü", y="Momentum", text="Ticker", color="Durum",
                         size=[10]*len(scan_results), title="Para Akış Matrisi")
        st.plotly_chart(fig, use_container_width=True)