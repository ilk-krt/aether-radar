import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time

# ==========================================
# 1. AYARLAR & CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER NEXUS", page_icon="🌌")

st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    h1, h2, h3, h4, span, p { color: #e0e0e0 !important; }
    .stat-box { background: linear-gradient(145deg, #111 0%, #0a0a0a 100%); padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; margin-bottom: 10px; }
    .stat-val { font-size: 1.5rem; font-weight: bold; color: #00ff88; }
    .news-box { border-left: 4px solid #00ff88; background-color: #111; padding: 10px; margin-bottom: 10px; border-radius: 4px; }
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
    "Robotik & AI": ["PATH", "SYM", "SOUN", "PLTR", "AI"]
}

# ==========================================
# 3. YARDIMCI MATEMATİK FONKSİYONLARI (PINE TO PYTHON)
# ==========================================
def rma(s, period): return s.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

def calculate_rsi(s, period=14):
    delta = s.diff()
    ma_up = rma(delta.clip(lower=0), period)
    ma_down = rma(-1 * delta.clip(upper=0), period)
    rs = ma_up / ma_down.replace(0, 0.001)
    return 100 - (100 / (1 + rs))

def calculate_apex_signals(df):
    """
    V665, V695 ve V700 PineScript kodlarındaki ana momentum, 
    sinerji, füzyon ve whale (renkli nokta) algoritmalarının Python karşılığı.
    """
    c, h, l, o, v = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
    
    # 1. Hacim ve Sıkışma
    v_avg = v.rolling(20).mean()
    rvol = (v / v_avg.clip(lower=1)).clip(upper=2.5)
    
    # 2. FUSION & SYNERGY Motoru (MACD tabanlı Hız Algılayıcıları)
    f_macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    f_h, f_l = f_macd.rolling(60).max(), f_macd.rolling(60).min()
    f_speed = ((f_macd - f_l) / (f_h - f_l).clip(lower=0.001) * 100) - 50
    f_sig = f_speed.ewm(span=9, adjust=False).mean()
    
    hlc3 = (h + l + c) / 3
    s_macd = hlc3.ewm(span=12, adjust=False).mean() - hlc3.ewm(span=26, adjust=False).mean()
    s_speed = s_macd.diff() # İvme
    
    # 3. WHALE POWER
    r14 = calculate_rsi(c, 14)
    c_range = (h - l).clip(lower=0.001)
    delta_vol = (((c - l) - (h - c)) / c_range * v).rolling(20).mean() / v_avg.clip(lower=0.001)
    base_pwr = ((r14 - 50) + (delta_vol * 40)) * rvol * 1.5
    w_pwr = np.clip(np.log1p(np.maximum(base_pwr, 0)) * 20, 0, 100)
    
    # 4. TRAPS (Bull / Bear Traps) - EMA Breakout
    ema_focus = c.ewm(span=9, adjust=False).mean()
    bear_trap = (l < ema_focus) & (c > ema_focus) & (v > v_avg * 1.5)
    bull_trap = (h > ema_focus) & (c < ema_focus) & (v > v_avg * 1.5)
    
    # 5. VOLATILITY HOLE (Squeeze)
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    b_low = sma20 - 2 * std20
    b_up = sma20 + 2 * std20
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    k_mid = sma20
    k_up = k_mid + 1.5 * tr.rolling(20).mean()
    k_low = k_mid - 1.5 * tr.rolling(20).mean()
    sqz_on = (b_low > k_low) & (b_up < k_up)
    
    # 6. SİNYAL NOKTALARI (RENK TANIMLAMALARI)
    # Fusion Noktaları
    df['Fus_Koyu_Mavi'] = (f_speed > f_sig) & (f_speed.shift(1) <= f_sig.shift(1))
    df['Fus_Acik_Mavi'] = (f_speed > f_sig) & (f_speed > f_speed.shift(1)) & ~df['Fus_Koyu_Mavi']
    df['Fus_Kirmizi'] = (f_speed < f_sig) & (f_speed.shift(1) >= f_sig.shift(1))
    df['Fus_Sari'] = (f_speed < f_sig) & (f_speed < f_speed.shift(1)) & ~df['Fus_Kirmizi']
    
    # Synergy Noktaları
    df['Syn_Koyu_Mavi'] = (s_speed > 0) & (s_speed.shift(1) <= 0)
    df['Syn_Sari'] = (s_speed > 0) & (s_speed < s_speed.shift(1))
    
    # Whale Noktaları
    pct_pro = w_pwr.ewm(span=3, adjust=False).mean()
    df['Whale_Reentry'] = (w_pwr > pct_pro) & (w_pwr.shift(1) <= pct_pro.shift(1))
    df['Whale_Out'] = (w_pwr < pct_pro) & (w_pwr.shift(1) >= pct_pro.shift(1))
    df['Whale_Full_Red'] = w_pwr > 75
    
    # Özel Formasyonlar
    df['Bear_Trap_✅'] = bear_trap
    df['Bull_Trap_⛔'] = bull_trap
    df['Vol_Hole'] = sqz_on
    df['Ignition'] = (c > o) & (v > v_avg * 2) & df['Fus_Koyu_Mavi']
    df['Stall'] = (c < o) & (v < v_avg * 0.5) & (f_speed < f_speed.shift(1))
    
    return df

# ==========================================
# 4. ARAYÜZ (TABS)
# ==========================================
tab1, tab2, tab3 = st.tabs(["🏛️ MAKRO & OPEX", "⚖️ THEMATIC VALUATION GAP", "📊 RALLİ İSTATİSTİĞİ (THE BEAST)"])

# ------------------------------------------
# TAB 1: MAKRO & OPEX
# ------------------------------------------
with tab1:
    st.header("🏛️ Gelişmiş Makro İstihbarat & Likidite Paneli")
    
    # --- TAHVİL FAİZLERİ ANOMALİ MOTORU ---
    st.subheader("🇺🇸 Amerikan Tahvil Faizleri (Haftalık Cuma-Cuma Hareketi)")
    col1, col2, col3 = st.columns(3)
    
    @st.cache_data(ttl=3600)
    def fetch_bonds():
        try:
            bond_data = yf.download(["^IRX", "^FVX", "^TNX"], period="10d", progress=False)
            if isinstance(bond_data.columns, pd.MultiIndex):
                # Handle MultiIndex
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
        
        if diff_10 > 0.15:
            st.error("🚨 ANOMALİ: 10 Yıllık Tahvillerde sert yükseliş! Büyüme (Tech/Çip) hisselerinde baskı yaratabilir. Nakit akışı enerji ve finansa dönebilir.")
        elif diff_10 < -0.15:
            st.success("🟢 LİKİDİTE RAHATLIYOR: Tahvil faizleri düşüyor. Yüksek çarpanlı teknoloji, uzay ve kripto hisseleri için pozitif (Risk-On) rüzgarı.")
        else:
            st.info("⚖️ Nötr Seyir: Tahvil piyasasında stabilizasyon var. Sektörel rotasyonlar kendi iç dinamikleriyle (Bilanço/Haber) ilerleyebilir.")
            
    st.divider()
    
    # --- HABER & OPEX SIMULATOR ---
    st.subheader("📰 Makro Gelişmeler & Varlık Sınıfı Etkileri")
    news_cat = st.selectbox("İstihbarat Modülü", [
        "1. Önümüzdeki Hafta Finansal Takvimi (Örn: İstihdam)",
        "2. Likidite & Fed Kararları",
        "3. Global Aktörler (Çin, Japonya, AB)",
        "4. ABD Hükümeti (Trump Kararları)",
        "5. Jeopolitik (Petrol & Doğalgaz)"
    ])
    
    if st.button("🔄 Verileri Güncelle"):
        with st.spinner("Kurumsal veri ağları taranıyor..."):
            time.sleep(1) # Simüle edilmiş API Gecikmesi
            
            if "Takvimi" in news_cat:
                st.markdown("""
                <div class='news-box'>
                <h4>📅 Önümüzdeki Hafta Beklentisi: Tarım Dışı İstihdam (NFP)</h4>
                <ul>
                    <li><b>Beklenti:</b> 180K </li>
                    <li><b>Eğer Düşük Gelirse (< 150K):</b> Fed faiz indirim umudu artar. <i>Etki:</i> Tech & Kripto (🚀), Tahvil (🔻), Dolar (🔻).</li>
                    <li><b>Eğer Yüksek Gelirse (> 220K):</b> Enflasyon korkusu hortlar. <i>Etki:</i> Teknoloji (🩸), Enerji (🟢), Dolar (🚀).</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)
            elif "Trump" in news_cat:
                st.markdown("""
                <div class='news-box'>
                <h4>🦅 Hükümet Politikaları (Executive Orders)</h4>
                <ul>
                    <li><b>Gelişme:</b> Deregülasyon ve vergi teşvikleri gündemde. Uzay ve savunma altyapısı ihaleleri konuşuluyor.</li>
                    <li><b>Etkilenecek ETF'ler:</b> $SPACE_RACE ve $CYBER temaları (🚀), Geleneksel ESG & Temiz Enerji (🩸).</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)
            elif "Likidite" in news_cat:
                st.markdown("""
                <div class='news-box'>
                <h4>🏦 FED Bilanço & Ters Repo (RRP) Analizi</h4>
                <ul>
                    <li><b>Gelişme:</b> Piyasadan likidite çekilme hızı yavaşlıyor.</li>
                    <li><b>Etki:</b> Varlık balonlarına izin verilecek. $WGMI (Bitcoin Miner) ve $PHOTON (Çip) ETF'lerine kurumsal nakit akışı güçlenir.</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.success("Veriler güncellendi. (Bu alana ileride API bağlantısı eklenebilir).")

# ------------------------------------------
# TAB 2: THEMATIC VALUATION GAP
# ------------------------------------------
with tab2:
    st.header("⚖️ Thematic Valuation Gap (Çarpan Uçurumu)")
    theme_choice = st.selectbox("Analiz Edilecek Temayı Seçin", list(THEMES.keys()))
    
    col_news, col_val = st.columns([1, 2])
    
    with col_news:
        st.subheader(f"📰 {theme_choice} Haberleri")
        if st.button("🔄 Son 1 Haftalık Haberleri Çek"):
            with st.spinner("AI Haber Ajansı Taranıyor..."):
                time.sleep(1)
                st.markdown(f"*(Simüle Edilmiş)* Son dakika: **{THEMES[theme_choice][0]}**, analist beklentilerini aşan bir rehberlik yayınladı. Kurumsal sermaye bu temaya yöneliyor.")
    
    with col_val:
        st.subheader("📊 Değerleme Uçurumu Radarı")
        if st.button("⚛️ Gap Hesapla", type="primary"):
            tickers = THEMES[theme_choice]
            with st.spinner(f"Finansal veriler {len(tickers)} hisse için Yahoo Finance üzerinden çekiliyor..."):
                funds = []
                for t in tickers:
                    try:
                        tk = yf.Ticker(t)
                        # API limitini aşmamak için fast_info kullanıyoruz
                        mc = tk.fast_info.get('marketCap', 0)
                        
                        try: pe = tk.info.get('trailingPE', 0)
                        except: pe = 0
                            
                        if mc > 0:
                            funds.append({"Ticker": t, "MarketCap": mc, "PE": pe})
                    except: pass
                
                df_val = pd.DataFrame(funds)
                if not df_val.empty:
                    df_val = df_val.sort_values(by='MarketCap', ascending=False).reset_index(drop=True)
                    leader = df_val.iloc[0]
                    
                    st.markdown(f"### 👑 Lider Hisse: **{leader['Ticker']}**")
                    st.markdown(f"Market Cap: **${leader['MarketCap']/1e9:.1f} Milyar** | F/K: **{leader['PE'] if leader['PE']>0 else 'N/A'}**")
                    st.divider()
                    
                    for i in range(1, len(df_val)):
                        row = df_val.iloc[i]
                        gap = leader['MarketCap'] / row['MarketCap']
                        st.markdown(f"**{row['Ticker']}** ➔ Liderden **{gap:.1f} kat** daha küçük. (Market Cap: ${row['MarketCap']/1e9:.1f}B, F/K: {row['PE'] if row['PE']>0 else 'N/A'})")
                else:
                    st.error("Veri çekilemedi. API limitlenmiş olabilir.")

# ------------------------------------------
# TAB 3: RALLİ İSTATİSTİĞİ (THE BEAST)
# ------------------------------------------
with tab3:
    st.header("📈 Ralli Öncesi İstatistik Motoru (V665, V695, V700 Sinerjisi)")
    st.markdown("Büyük fiyat hareketlerinden (Örn: 10 günde %15 artış/azalış) önceki 4 periyotta (Gün veya 4H) göstergelerin nasıl konumlandığını analiz eder.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st_ticker = st.selectbox("İncelenecek Hisse", [t for sublist in THEMES.values() for t in sublist])
    with c2:
        st_tf = st.selectbox("Periyot", ["1d (Günlük)", "4h (4 Saatlik)"])
    with c3:
        st_thr = st.number_input("Hareket Eşiği (%)", min_value=5, max_value=50, value=15)
        
    if st.button("🧠 İstatistikleri Üret (Ağır İşlem)", use_container_width=True):
        with st.spinner(f"{st_ticker} geçmişi simüle ediliyor ve V665/V700 sinyalleri işleniyor... (Bu işlem saniyeler sürebilir)"):
            yf_tf = "1d" if "1d" in st_tf else "1h"
            
            try:
                # Geniş bir tarihçe çekelim
                df_raw = yf.download(st_ticker, period="2y", interval=yf_tf, progress=False)
                if isinstance(df_raw.columns, pd.MultiIndex):
                    df = df_raw.xs(st_ticker, level=1, axis=1).copy()
                else:
                    df = df_raw.copy()
                df.dropna(inplace=True)
                
                if "4h" in st_tf:
                    df.index = pd.to_datetime(df.index)
                    df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
                
                # Tüm Şahane Sinyallerini Hesapla
                df = calculate_apex_signals(df)
                
                # Ralli Arama Motoru (10 barda %15 artış)
                rallies = []
                bar_len = len(df)
                for i in range(10, bar_len - 10):
                    past_close = df['Close'].iloc[i]
                    future_close = df['Close'].iloc[i+10]
                    pct_change = ((future_close / past_close) - 1) * 100
                    
                    if pct_change >= st_thr:
                        # Ralli bulundu! Önceki 4 bara bakalım
                        if i >= 4:
                            rallies.append(df.iloc[i-4:i])
                
                st.success(f"Geçmiş 2 yılda, 10 periyotta +%{st_thr} yükselen tam **{len(rallies)} adet** majör ralli bulundu!")
                st.divider()
                
                if len(rallies) > 0:
                    # İstatistikleri Topla
                    stats = {
                        "Fus_Koyu_Mavi": 0, "Syn_Koyu_Mavi": 0, "Whale_Reentry": 0, 
                        "Whale_Full_Red": 0, "Bear_Trap_✅": 0, "Vol_Hole": 0, "Ignition": 0
                    }
                    
                    for r_df in rallies:
                        # Ralli öncesi 4 periyotta bu sinyallerden en az 1 kez yananları say
                        for key in stats.keys():
                            if r_df[key].sum() > 0:
                                stats[key] += 1
                                
                    # Ekrana Bas
                    st.subheader("🔥 İstatistiksel Sinyal Olasılıkları (Ralli Öncesi 4 Bar)")
                    sc1, sc2, sc3, sc4 = st.columns(4)
                    
                    def prob(val): return (val / len(rallies)) * 100
                    
                    sc1.markdown(f"<div class='stat-box'>Fusion Koyu Mavi<br><span class='stat-val'>%{prob(stats['Fus_Koyu_Mavi']):.1f}</span></div>", unsafe_allow_html=True)
                    sc2.markdown(f"<div class='stat-box'>Synergy Koyu Mavi<br><span class='stat-val'>%{prob(stats['Syn_Koyu_Mavi']):.1f}</span></div>", unsafe_allow_html=True)
                    sc3.markdown(f"<div class='stat-box'>Whale Re-Entry<br><span class='stat-val'>%{prob(stats['Whale_Reentry']):.1f}</span></div>", unsafe_allow_html=True)
                    sc4.markdown(f"<div class='stat-box'>Whale %75+ Güç<br><span class='stat-val'>%{prob(stats['Whale_Full_Red']):.1f}</span></div>", unsafe_allow_html=True)
                    
                    sc1.markdown(f"<div class='stat-box'>Bear Trap (✅)<br><span class='stat-val'>%{prob(stats['Bear_Trap_✅']):.1f}</span></div>", unsafe_allow_html=True)
                    sc2.markdown(f"<div class='stat-box'>Volatility Hole<br><span class='stat-val'>%{prob(stats['Vol_Hole']):.1f}</span></div>", unsafe_allow_html=True)
                    sc3.markdown(f"<div class='stat-box'>Ignition<br><span class='stat-val'>%{prob(stats['Ignition']):.1f}</span></div>", unsafe_allow_html=True)
                    
                    st.info("💡 **Yorum:** Örneğin 'Whale Re-Entry %80' diyorsa, gerçekleşen tüm büyük rallilerin %80'inde, ralli başlamadan önceki 4 bar içinde mutlaka Whale Re-Entry sinyali yanmış demektir.")
                else:
                    st.warning("Bu hissede belirtilen şartlarda dev bir ralli/hareket geçmişi bulunamadı. Eşiği düşürmeyi deneyin.")
            
            except Exception as e:
                st.error(f"Veri çekme veya hesaplama hatası: {e}")
