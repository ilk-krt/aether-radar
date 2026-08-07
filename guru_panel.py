import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# ==========================================
# 1. AYARLAR & SİBERPUNK CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER NEXUS | PRO", page_icon="🌌")

st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    h1, h2, h3, h4, span, p { color: #e0e0e0 !important; }
    
    /* Fütüristik Metrik Kartları */
    .metric-card { 
        background: linear-gradient(145deg, #111 0%, #0a0a0a 100%); 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #333; 
        border-left: 4px solid #00f3ff;
        text-align: center; 
        margin-bottom: 15px; 
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.1);
        transition: transform 0.3s;
    }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 0 25px rgba(0, 243, 255, 0.3); }
    .metric-title { font-size: 1rem; color: #888; text-transform: uppercase; letter-spacing: 2px; }
    .metric-val { font-size: 2.2rem; font-weight: bold; color: #00f3ff; text-shadow: 0 0 10px rgba(0,243,255,0.5); }
    .metric-sub { font-size: 1rem; margin-top: 5px; }
    .pos-change { color: #00ff88; text-shadow: 0 0 8px rgba(0,255,136,0.5); }
    .neg-change { color: #ff0055; text-shadow: 0 0 8px rgba(255,0,85,0.5); }
    .stat-box { background: linear-gradient(145deg, #111 0%, #0a0a0a 100%); padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; margin-bottom: 10px; }
    .stat-val { font-size: 1.5rem; font-weight: bold; color: #00ff88; }
    .news-box { border-left: 4px solid #00ff88; background-color: #111; padding: 10px; margin-bottom: 10px; border-radius: 4px; }
    
    /* Güncelle Butonu */
    .stButton>button {
        background: transparent;
        color: #00f3ff;
        border: 2px solid #00f3ff;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background: #00f3ff;
        color: #000;
        box-shadow: 0 0 20px #00f3ff;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. VERİ SETLERİ & TEMALAR
# ==========================================
THEMES = {
    "Yarı İletken (Çip Mimarisi)": ["NVDA", "AMD", "TSM", "ASML", "AVGO", "AMAT", "LRCX", "KLAC"],
    "Fotonik ve Optik Ekosistemi": ["COHR", "LITE", "POET", "AAOI", "IQE", "AXTI"],
    "Global Siber Güvenlik": ["CRWD", "PANW", "ZS", "FTNT", "NET", "OKTA", "S"],
    "SpaceX & Uzay": ["RKLB", "ASTS", "LUNR", "SATS", "PL", "SPIR", "BKSY", "SIDU"],
    "Kripto Madencilik (Neocloud)": ["MSTR", "MARA", "RIOT", "CLSK", "IREN", "WULF", "CIFR", "CORZ"],
    "Enerji & Altyapı": ["XLU", "CEG", "VST", "NNE", "CCJ"],
    "Robotik & AI": ["PATH", "SYM", "SOUN", "PLTR", "AI"]
}

# ==========================================
# 3. YARDIMCI VERİ FONKSİYONLARI
# ==========================================
@st.cache_data(ttl=600)
def get_usd_try():
    try: return float(yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1])
    except: return 34.50

@st.cache_data(ttl=600)
def get_yf_price(symbol):
    try: return float(yf.Ticker(symbol).history(period="1d")['Close'].iloc[-1])
    except: return 0.0

@st.cache_data(ttl=3600)
def get_tefas_price(fund_code):
    try:
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        price_str = soup.find('span', string='Son Fiyat').find_next_sibling('span').text
        return float(price_str.replace('.', '').replace(',', '.'))
    except: return 0.0

# ==========================================
# 4. PORTFÖY SESSION STATE (İLK YÜKLEME)
# ==========================================
if "portfolio_df" not in st.session_state:
    initial_data = {
        "Sembol": ["NVDA", "XLU", "ALK.IS", "MAC", "BTC-USD", "GOLD"],
        "Tür": ["US_STOCK", "ETF", "TR_STOCK", "TEFAS", "CRYPTO", "GOLD"],
        "Ana Sınıf": ["ABD Hisse", "ABD ETF", "BIST", "Fon", "Kripto", "Emtia"],
        "Sektör": ["Yarı İletken", "Altyapı", "Kimya", "Hisse Yoğun", "L1 Zincir", "Kıymetli Maden"],
        "Adet": [10.0, 20.0, 500.0, 10000.0, 0.25, 50.0],
        "Maliyet": [95.0, 60.0, 25.0, 0.05, 42000.0, 2000.0],
        "Güncel Fiyat": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # 0 olanlar otomatik çekilecek
        "Para Birimi": ["USD", "USD", "TRY", "TRY", "USD", "TRY"]
    }
    st.session_state.portfolio_df = pd.DataFrame(initial_data)

# ==========================================
# 5. ARAYÜZ (TABS)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🌌 PORTFÖY & SANKEY", "🏛️ MAKRO & OPEX", "⚖️ THEMATIC VALUATION", "📊 THE BEAST (RALLİ)"])

# ------------------------------------------
# TAB 1: PORTFÖY & SANKEY
# ------------------------------------------
with tab1:
    col_hdr1, col_hdr2 = st.columns([4, 1])
    with col_hdr1:
        st.markdown("<h1>🌌 AETHER NEXUS <span style='color:#00f3ff;'>PORTFOLIO</span></h1>", unsafe_allow_html=True)
    
    # 🔄 GÜNCELLEME MOTORU
    if col_hdr2.button("🔄 FİYATLARI SENKRONİZE ET"):
        usd_try = get_usd_try()
        gold_oz = get_yf_price("GC=F") or 2500.0
        silver_oz = get_yf_price("SI=F") or 30.0
        
        gold_gram_try = (gold_oz / 31.1035) * usd_try
        silver_gram_try = (silver_oz / 31.1035) * usd_try
        
        updated_df = st.session_state.portfolio_df.copy()
        
        for idx, row in updated_df.iterrows():
            if pd.isna(row['Güncel Fiyat']) or row['Güncel Fiyat'] == 0.0:
                ptype = row['Tür']
                sym = row['Sembol']
                curr = row['Para Birimi']
                
                if ptype in ["US_STOCK", "TR_STOCK", "ETF", "CRYPTO"]:
                    price = get_yf_price(sym)
                    if price > 0: updated_df.at[idx, 'Güncel Fiyat'] = price
                elif ptype == "TEFAS":
                    price = get_tefas_price(sym)
                    if price > 0: updated_df.at[idx, 'Güncel Fiyat'] = price
                elif ptype == "GOLD":
                    updated_df.at[idx, 'Güncel Fiyat'] = gold_gram_try if curr == "TRY" else gold_oz
                elif ptype == "SILVER":
                    updated_df.at[idx, 'Güncel Fiyat'] = silver_gram_try if curr == "TRY" else silver_oz
                elif ptype == "CASH":
                    updated_df.at[idx, 'Güncel Fiyat'] = 1.0
                    
        st.session_state.portfolio_df = updated_df
        st.rerun()

    st.markdown("### 📝 Manuel Portföy Editörü")
    st.write("Fiyatını `0` bıraktığın varlıklar (Hisse, Kripto, TEFAS), 'Senkronize Et' butonuna bastığında API üzerinden anlık güncellenir.")
    
    # Data Editor
    edited_df = st.data_editor(
        st.session_state.portfolio_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Adet": st.column_config.NumberColumn(format="%.4f"),
            "Maliyet": st.column_config.NumberColumn(format="%.2f"),
            "Güncel Fiyat": st.column_config.NumberColumn(format="%.2f"),
            "Para Birimi": st.column_config.SelectboxColumn(options=["TRY", "USD"]),
            "Tür": st.column_config.SelectboxColumn(options=["US_STOCK", "TR_STOCK", "ETF", "TEFAS", "CRYPTO", "GOLD", "SILVER", "CASH", "MANUAL"])
        }
    )
    st.session_state.portfolio_df = edited_df

    # HESAPLAMALAR
    usd_try = get_usd_try()
    calc_df = edited_df.copy()
    
    calc_df['Maliyet (TRY)'] = np.where(calc_df['Para Birimi'] == 'TRY', calc_df['Adet'] * calc_df['Maliyet'], (calc_df['Adet'] * calc_df['Maliyet']) * usd_try)
    calc_df['Maliyet (USD)'] = np.where(calc_df['Para Birimi'] == 'USD', calc_df['Adet'] * calc_df['Maliyet'], (calc_df['Adet'] * calc_df['Maliyet']) / usd_try)
    
    calc_df['Güncel Değer (TRY)'] = np.where(calc_df['Para Birimi'] == 'TRY', calc_df['Adet'] * calc_df['Güncel Fiyat'], (calc_df['Adet'] * calc_df['Güncel Fiyat']) * usd_try)
    calc_df['Güncel Değer (USD)'] = np.where(calc_df['Para Birimi'] == 'USD', calc_df['Adet'] * calc_df['Güncel Fiyat'], (calc_df['Adet'] * calc_df['Güncel Fiyat']) / usd_try)
    
    calc_df['Kâr/Zarar (%)'] = np.where(calc_df['Maliyet'] > 0, ((calc_df['Güncel Fiyat'] - calc_df['Maliyet']) / calc_df['Maliyet']) * 100, 0)

    tot_try = calc_df['Güncel Değer (TRY)'].sum()
    tot_usd = calc_df['Güncel Değer (USD)'].sum()
    tot_cost_try = calc_df['Maliyet (TRY)'].sum()
    total_profit_try = tot_try - tot_cost_try
    total_profit_pct = (total_profit_try / tot_cost_try * 100) if tot_cost_try > 0 else 0

    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>NET DEĞER (TRY)</div><div class='metric-val'>₺ {tot_try:,.0f}</div><div class='metric-sub'>USD/TRY: {usd_try:.2f}</div></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>NET DEĞER (USD)</div><div class='metric-val' style='color:#b829ff;'>$ {tot_usd:,.0f}</div><div class='metric-sub'>Global Satın Alma Gücü</div></div>", unsafe_allow_html=True)
    
    p_col = "pos-change" if total_profit_pct >= 0 else "neg-change"
    p_sig = "+" if total_profit_pct >= 0 else ""
    with m3:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>TÜM ZAMANLAR K/Z</div><div class='metric-val {p_col}'>{p_sig}₺ {total_profit_try:,.0f}</div><div class='metric-sub {p_col}'>{p_sig}%{total_profit_pct:.2f} Büyüme</div></div>", unsafe_allow_html=True)
    with m4:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>AKTİF VARLIK SAYISI</div><div class='metric-val'>{len(calc_df)}</div><div class='metric-sub'>Takip Edilen Enstrüman</div></div>", unsafe_allow_html=True)

    # 📊 SANKEY DİYAGRAMI
    st.markdown("### 🧬 Portföy Diversifikasyon Akışı (Sankey Matrix)")
    if not calc_df.empty and calc_df['Güncel Değer (TRY)'].sum() > 0:
        labels = ["Tüm Portföy"] + list(calc_df["Ana Sınıf"].unique()) + list(calc_df["Sektör"].unique()) + list(calc_df["Sembol"].unique())
        label_dict = {label: i for i, label in enumerate(labels)}

        source, target, value, colors = [], [], [], []
        
        # Renk Paleti (Siberpunk Mavi/Cyan)
        link_color = "rgba(0, 243, 255, 0.35)"

        for sinif, group in calc_df.groupby("Ana Sınıf"):
            if group["Güncel Değer (TRY)"].sum() > 0:
                source.append(label_dict["Tüm Portföy"])
                target.append(label_dict[sinif])
                value.append(group["Güncel Değer (TRY)"].sum())
                colors.append(link_color)

        for (sinif, sektor), group in calc_df.groupby(["Ana Sınıf", "Sektör"]):
            if group["Güncel Değer (TRY)"].sum() > 0:
                source.append(label_dict[sinif])
                target.append(label_dict[sektor])
                value.append(group["Güncel Değer (TRY)"].sum())
                colors.append(link_color)

        for (sektor, varlik), group in calc_df.groupby(["Sektör", "Sembol"]):
            if group["Güncel Değer (TRY)"].sum() > 0:
                source.append(label_dict[sektor])
                target.append(label_dict[varlik])
                value.append(group["Güncel Değer (TRY)"].sum())
                colors.append(link_color)

        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=25, thickness=20,
                line=dict(color="#00f3ff", width=1),
                label=labels,
                color="#111"
            ),
            link=dict(source=source, target=target, value=value, color=colors)
        )])

        fig_sankey.update_layout(
            font_size=12, height=600,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0e0e0'),
            margin=dict(t=30, l=10, r=10, b=10)
        )
        st.plotly_chart(fig_sankey, use_container_width=True)

# ------------------------------------------
# TAB 2: MAKRO & OPEX
# ------------------------------------------
with tab2:
    st.header("🏛️ Gelişmiş Makro İstihbarat & Likidite Paneli")
    st.subheader("🇺🇸 Amerikan Tahvil Faizleri (Haftalık Cuma-Cuma Hareketi)")
    col1, col2, col3 = st.columns(3)
    
    @st.cache_data(ttl=3600)
    def fetch_bonds():
        try:
            bond_data = yf.download(["^IRX", "^FVX", "^TNX"], period="10d", progress=False)
            if isinstance(bond_data.columns, pd.MultiIndex):
                return {
                    "13W": bond_data.xs('^IRX', level=1, axis=1)['Close'] if '^IRX' in bond_data.columns.levels[1] else pd.Series(),
                    "5Y": bond_data.xs('^FVX', level=1, axis=1)['Close'] if '^FVX' in bond_data.columns.levels[1] else pd.Series(),
                    "10Y": bond_data.xs('^TNX', level=1, axis=1)['Close'] if '^TNX' in bond_data.columns.levels[1] else pd.Series()
                }
            else:
                return {"13W": bond_data['^IRX'], "5Y": bond_data['^FVX'], "10Y": bond_data['^TNX']}
        except: return None
        
    bonds = fetch_bonds()
    if bonds and not bonds["10Y"].empty:
        def calc_bond_chg(s):
            if len(s) < 5: return 0.0, s.iloc[-1]
            return (s.iloc[-1] - s.iloc[-5]), s.iloc[-1]
            
        diff_1, val_1 = calc_bond_chg(bonds["13W"])
        diff_5, val_5 = calc_bond_chg(bonds["5Y"])
        diff_10, val_10 = calc_bond_chg(bonds["10Y"])
        
        col1.metric("3 Aylık Bono (^IRX)", f"%{val_1:.2f}", f"{diff_1:.2f} bps")
        col2.metric("5 Yıllık Tahvil (^FVX)", f"%{val_5:.2f}", f"{diff_5:.2f} bps")
        col3.metric("10 Yıllık Tahvil (^TNX)", f"%{val_10:.2f}", f"{diff_10:.2f} bps")

# ------------------------------------------
# TAB 3: THEMATIC VALUATION GAP
# ------------------------------------------
with tab3:
    st.header("⚖️ Thematic Valuation Gap (Çarpan Uçurumu)")
    theme_choice = st.selectbox("Analiz Edilecek Temayı Seçin", list(THEMES.keys()))
    
    col_news, col_val = st.columns([1, 2])
    with col_news:
        st.subheader(f"📰 {theme_choice} Haberleri")
        if st.button("🔄 Son Haberleri Çek"):
            st.markdown(f"*(Simüle Edilmiş)* Son dakika: **{THEMES[theme_choice][0]}**, beklentileri aşan bir rehberlik yayınladı. Kurumsal sermaye akışı hızlanıyor.")
    
    with col_val:
        st.subheader("📊 Değerleme Uçurumu Radarı")
        if st.button("⚛️ Gap Hesapla", type="primary"):
            tickers = THEMES[theme_choice]
            with st.spinner(f"Veriler {len(tickers)} hisse için çekiliyor..."):
                funds = []
                for t in tickers:
                    try:
                        tk = yf.Ticker(t)
                        mc = tk.fast_info.get('marketCap', 0)
                        pe = tk.info.get('trailingPE', 0) if 'trailingPE' in tk.info else 0
                        if mc > 0: funds.append({"Ticker": t, "MarketCap": mc, "PE": pe})
                    except: pass
                
                df_val = pd.DataFrame(funds)
                if not df_val.empty:
                    df_val = df_val.sort_values(by='MarketCap', ascending=False).reset_index(drop=True)
                    leader = df_val.iloc[0]
                    st.markdown(f"### 👑 Lider Hisse: **{leader['Ticker']}** (Market Cap: ${leader['MarketCap']/1e9:.1f}B)")
                    for i in range(1, len(df_val)):
                        row = df_val.iloc[i]
                        gap = leader['MarketCap'] / row['MarketCap']
                        st.markdown(f"**{row['Ticker']}** ➔ Liderden **{gap:.1f} kat** daha küçük. (F/K: {row['PE'] if row['PE']>0 else 'N/A'})")

# ------------------------------------------
# TAB 4: RALLİ İSTATİSTİĞİ (THE BEAST)
# ------------------------------------------
with tab4:
    def rma(s, p): return s.ewm(alpha=1/p, min_periods=p, adjust=False).mean()
    def calc_rsi(s, p=14):
        d = s.diff()
        rs = rma(d.clip(lower=0), p) / rma(-1 * d.clip(upper=0), p).replace(0, 0.001)
        return 100 - (100 / (1 + rs))

    def calc_signals(df):
        c, h, l, o, v = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
        v_avg = v.rolling(20).mean()
        rvol = (v / v_avg.clip(lower=1)).clip(upper=2.5)
        
        f_macd = c.ewm(span=12).mean() - c.ewm(span=26).mean()
        f_h, f_l = f_macd.rolling(60).max(), f_macd.rolling(60).min()
        f_speed = ((f_macd - f_l) / (f_h - f_l).clip(lower=0.001) * 100) - 50
        f_sig = f_speed.ewm(span=9).mean()
        
        df['Fus_Koyu_Mavi'] = (f_speed > f_sig) & (f_speed.shift(1) <= f_sig.shift(1))
        df['Whale_Full_Red'] = (((calc_rsi(c, 14) - 50) + ((((c-l)-(h-c))/(h-l).clip(lower=0.001)*v).rolling(20).mean() / v_avg.clip(lower=0.001)) * 40) * rvol * 1.5) > 75
        df['Bear_Trap'] = (l < c.ewm(span=9).mean()) & (c > c.ewm(span=9).mean()) & (v > v_avg * 1.5)
        return df

    st.header("📈 Ralli Öncesi İstatistik Motoru (V665/V700)")
    c1, c2, c3 = st.columns(3)
    with c1: st_ticker = st.selectbox("Hisse Seç", [t for sublist in THEMES.values() for t in sublist])
    with c2: st_tf = st.selectbox("Periyot", ["1d (Günlük)", "4h (4 Saatlik)"])
    with c3: st_thr = st.number_input("Eşik (%)", min_value=5, max_value=50, value=15)
    
    if st.button("🧠 İstatistikleri Üret", use_container_width=True):
        with st.spinner("Sinyaller işleniyor..."):
            try:
                df_raw = yf.download(st_ticker, period="2y", interval="1d" if "1d" in st_tf else "1h", progress=False)
                df = df_raw.xs(st_ticker, level=1, axis=1) if isinstance(df_raw.columns, pd.MultiIndex) else df_raw
                df.dropna(inplace=True)
                if "4h" in st_tf: df = df.resample('4h').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                
                df = calc_signals(df)
                rallies = [df.iloc[i-4:i] for i in range(10, len(df)-10) if ((df['Close'].iloc[i+10] / df['Close'].iloc[i]) - 1)*100 >= st_thr and i >= 4]
                
                st.success(f"{len(rallies)} adet ralli bulundu!")
                if rallies:
                    stats = {"Fus_Koyu_Mavi": 0, "Whale_Full_Red": 0, "Bear_Trap": 0}
                    for r in rallies:
                        for k in stats:
                            if r[k].sum() > 0: stats[k] += 1
                    
                    sc1, sc2, sc3 = st.columns(3)
                    sc1.markdown(f"<div class='stat-box'>Fusion Koyu Mavi<br><span class='stat-val'>%{(stats['Fus_Koyu_Mavi']/len(rallies))*100:.1f}</span></div>", unsafe_allow_html=True)
                    sc2.markdown(f"<div class='stat-box'>Whale Kırmızı<br><span class='stat-val'>%{(stats['Whale_Full_Red']/len(rallies))*100:.1f}</span></div>", unsafe_allow_html=True)
                    sc3.markdown(f"<div class='stat-box'>Bear Trap<br><span class='stat-val'>%{(stats['Bear_Trap']/len(rallies))*100:.1f}</span></div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Hata: {e}")
