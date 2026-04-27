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

# Genişletilmiş ETF Bilgi Kütüphanesi (Alan Tanımı + Genişletilmiş Hisseler)
ETF_INFO = {
    # --- TEKNOLOJİ, YARI İLETKEN & YAPAY ZEKA ---
    "SMH": {"area": "Yarı İletken Devleri & Çip Üretimi", "stocks": ["NVDA (Nvidia)", "TSM (Taiwan Semi)", "AVGO (Broadcom)", "ASML", "AMD", "MU (Micron)", "INTC (Intel)", "KLAC", "LRCX", "ADI"]},
    "SOXX": {"area": "Global Çip Ekosistemi & Tasarım", "stocks": ["NVDA", "AVGO", "AMD", "TXN (Texas Inst)", "MU", "INTC", "AMAT (Applied Mat)", "QCOM (Qualcomm)", "ADI", "MCHP"]},
    "BOTZ": {"area": "Robotik Sistemler & Endüstriyel AI", "stocks": ["ISRG (Intuitive)", "NVDA", "ABB", "KEYENCE", "FANUC", "TER (Teradyne)", "YASKAWA", "PATH (UiPath)", "OMRON"]},
    "CIBR": {"area": "Siber Güvenlik & Veri Koruma Ağları", "stocks": ["PANW (Palo Alto)", "CRWD (Crowdstrike)", "FTNT (Fortinet)", "NET (Cloudflare)", "ZS (Zscaler)", "OKTA", "CHKP (Check Point)", "AKAM (Akamai)"]},
    "IGV": {"area": "Bulut Yazılım & Kurumsal SaaS", "stocks": ["ADBE (Adobe)", "CRM (Salesforce)", "INTU (Intuit)", "ORCL (Oracle)", "MSFT (Microsoft)", "NOW (ServiceNow)", "SNOW (Snowflake)", "MDB (MongoDB)"]},
    "ARKF": {"area": "Finansal Teknoloji & Dijital Ödemeler", "stocks": ["COIN (Coinbase)", "SHOP (Shopify)", "SQ (Block)", "MELI (MercadoLibre)", "HOOD (Robinhood)", "DKNG (DraftKings)", "TOAST", "PYPL (PayPal)"]},
    
    # --- SAVUNMA, HAVACILIK & UZAY ---
    "ITA": {"area": "Havacılık, Savunma & Ulusal Güvenlik", "stocks": ["RTX (Raytheon)", "LMT (Lockheed)", "BA (Boeing)", "GD (General Dynamics)", "NOC (Northrop)", "TDG (TransDigm)", "HWM (Howmet)", "LHX (L3Harris)", "TXT (Textron)"]},
    "XAR": {"area": "Gelişmiş Uzay Teknolojileri & Donanım", "stocks": ["GE (General Electric)", "TDG", "HWM", "LMT", "RTX", "AXON", "NOC", "RKLB (Rocket Lab)", "BKS (Barnes)"]},
    "IYT": {"area": "Ulaşım, Lojistik & Kargo Taşımacılığı", "stocks": ["UNP (Union Pacific)", "UPS", "UBER", "FDX (FedEx)", "CSX", "NSC", "ODFL (Old Dominion)", "DAL (Delta)", "EXPD"]},
    "PAVE": {"area": "Altyapı, İnşaat & Endüstriyel Üretim", "stocks": ["TRNE (Trane)", "ETN (Eaton)", "URI (United Rentals)", "DE (Deere)", "CAT (Caterpillar)", "VMC (Vulcan)", "MLM (Martin Marietta)", "EMR (Emerson)"]},
    "JETS": {"area": "Hava Yolu Taşımacılığı & Global Operatörler", "stocks": ["DAL (Delta)", "UAL (United)", "AAL (American)", "LUV (Southwest)", "ALGT", "ALK (Alaska Air)", "JBLU (JetBlue)", "SAVE (Spirit)"]},
    
    # --- ENERJİ, URANYUM & YEŞİL DÖNÜŞÜM ---
    "XOP": {"area": "Petrol & Doğalgaz Arama/Çıkarma", "stocks": ["XOM (Exxon)", "CVX (Chevron)", "COP (Conoco)", "EOG", "PXD (Pioneer)", "HES (Hess)", "DVN (Devon)", "OXY (Occidental)", "MRO"]},
    "OIH": {"area": "Petrol Servisleri & Sondaj Ekipmanları", "stocks": ["SLB (Schlumberger)", "HAL (Halliburton)", "BKR (Baker Hughes)", "FTI (TechnipFMC)", "VLO (Valero)", "MPC (Marathon)", "PSX (Phillips 66)", "HP"]},
    "URA": {"area": "Nükleer Enerji & Uranyum Madenciliği", "stocks": ["CCJ (Cameco)", "KAP (Kazatomprom)", "UUUU (Energy Fuels)", "NLR", "BWXT", "DNN (Denison Mines)", "NXE (NexGen)", "UEC (Uranium Energy)"]},
    "ICLN": {"area": "Temiz Enerji & Karbonsuz Dönüşüm", "stocks": ["BE (Bloom Energy)", "FSLR (First Solar)", "ENPH (Enphase)", "VWS (Vestas)", "ORSTED", "NEE (NextEra)", "EDPR", "PLUG (Plug Power)", "DQ"]},
    "TAN": {"area": "Güneş Enerjisi & Panel Üretimi", "stocks": ["FSLR", "ENPH", "NXT (Nextracker)", "SEDG (SolarEdge)", "RUN (Sunrun)", "TPW", "SHLS (Shoals)", "SPWR (SunPower)"]},
    
    # --- MATERYALLER & LİTYUM ---
    "LIT": {"area": "Lityum Döngüsü & Batarya Teknolojileri", "stocks": ["ALB (Albemarle)", "SQM", "BYD", "TSLA (Tesla)", "CATL", "ALTM (Arcadium)", "LAC (Lithium Americas)", "PIL (Pilbara Minerals)", "PMG"]},
    "XME": {"area": "Metaller, Madencilik & Çelik Sanayi", "stocks": ["FCX (Freeport)", "NUE (Nucor)", "STLD (Steel Dynamics)", "AA (Alcoa)", "CLF (Cleveland-Cliffs)", "RS (Reliance)", "MP (MP Materials)"]},
    "GDX": {"area": "Altın Madencileri & Değerli Metaller", "stocks": ["NEM (Newmont)", "GOLD (Barrick)", "AEM (Agnico Eagle)", "WPM (Wheaton)", "KGC (Kinross)", "PAAS (Pan American)"]},
    "REMX": {"area": "Nadir Toprak Elementleri & Stratejik Metaller", "stocks": ["ALB", "MP (MP Materials)", "Lynas Rare Earths", "Ganfeng Lithium", "Tianqi Lithium"]},
    
    # --- SAĞLIK & BİYOTEKNOLOJİ ---
    "XBI": {"area": "Biyoteknoloji & Genetik Araştırmalar", "stocks": ["MRNA (Moderna)", "VRTX (Vertex)", "AMGN (Amgen)", "GILD (Gilead)", "BIIB (Biogen)", "REGN (Regeneron)", "SGEN", "BNTX (BioNTech)"]},
    "IHI": {"area": "Tıbbi Cihazlar & Cerrahi Teknolojiler", "stocks": ["ABT (Abbott)", "MDT (Medtronic)", "ISRG (Intuitive)", "SYK (Stryker)", "BSX (Boston Sci)", "EW (Edwards)", "DXCM (Dexcom)", "ZBH"]},
    "ARKG": {"area": "Genomik Devrim & Yaşam Bilimleri", "stocks": ["EXAS (Exact Sciences)", "CRSP (CRISPR)", "PACB (Pacific Bio)", "NTLA (Intellia)", "EDIT (Editas)", "NVTA", "BEAM"]},
    
    # --- TÜKETİM, BAHİS & EĞLENCE ---
    "BETZ": {"area": "Online Bahis & iGaming Teknolojileri", "stocks": ["DKNG (DraftKings)", "FLUT (Flutter)", "EVO (Evolution)", "PENN", "MGM (Resorts)", "CZR (Caesars)", "WYNN", "GENI (Genius Sports)"]},
    "XRT": {"area": "Perakende Ticaret & Tüketici Harcamaları", "stocks": ["CVNA (Carvana)", "ANF (Abercrombie)", "AMZN (Amazon)", "COST (Costco)", "WMT (Walmart)", "TGT (Target)", "TJX", "DLTR"]},
    "XHB": {"area": "Konut İnşaatı & Ev Geliştirme", "stocks": ["LEN (Lennar)", "DHI (DR Horton)", "PHM (PulteGroup)", "LOW (Lowe's)", "HD (Home Depot)", "NVR", "TOL (Toll Brothers)"]},
    "IBUY": {"area": "E-Ticaret & Dijital Pazaryerleri", "stocks": ["AMZN", "EBAY", "ETSY", "CHWY (Chewy)", "MELI", "QRTEA", "JD (JD.com)"]},
    
    # --- FİNANS & BANKACILIK ---
    "KRE": {"area": "ABD Bölgesel Bankacılık Sistemi", "stocks": ["NYCB", "WAL (Western Alliance)", "ZION (Zions)", "CMA (Comerica)", "TFC (Truist)", "HBAN (Huntington)", "RF (Regions)", "FITB"]},
    "KIE": {"area": "Sigortacılık & Risk Yönetimi", "stocks": ["CB (Chubb)", "PGR (Progressive)", "ALL (Allstate)", "TRV (Travelers)", "MET (MetLife)", "PRU (Prudential)", "AFL (Aflac)"]},
    "IAI": {"area": "Yatırım Bankacılığı & Aracı Kurumlar", "stocks": ["MS (Morgan Stanley)", "GS (Goldman Sachs)", "IBKR (Interactive Brokers)", "SCHW (Charles Schwab)", "RJF (Raymond James)", "LPLA"]},
    
    # --- DİĞERLERİ & KÜRESEL ---
    "SOCL": {"area": "Sosyal Medya & İletişim Ağları", "stocks": ["META", "GOOGL (Alphabet)", "Tencent", "SNAP", "PINS (Pinterest)", "GRVY", "BIDU", "SPOT (Spotify)"]},
    "HERO": {"area": "Video Oyunları & Dijital Eğlence", "stocks": ["NVDA", "NTDOY (Nintendo)", "SE (Sea)", "EA (Electronic Arts)", "TTWO (Take-Two)", "RBLX (Roblox)", "U (Unity)", "UBSFY (Ubisoft)"]},
    "SRVR": {"area": "Veri Merkezleri & Altyapı GYO", "stocks": ["EQIX (Equinix)", "AMT (American Tower)", "DLR (Digital Realty)", "CCI (Crown Castle)", "SBAC", "UNIT"]},
    "PHO": {"area": "Su Teknolojileri & Arıtma Sistemleri", "stocks": ["AWK (American Water)", "XYL (Xylem)", "WTS (Watts)", "AWR", "SBS (Sabesp)", "TTEK"]},
    "MOO": {"area": "Tarım Teknolojileri & Gıda Üretimi", "stocks": ["DE (Deere)", "ZTS (Zoetis)", "TSCO (Tractor Supply)", "CTVA (Corteva)", "ADM (Archer Daniels)", "NTR (Nutrien)", "FMC"]},
    "PBJ": {"area": "Temel Tüketim & Hazır Gıda", "stocks": ["MDLZ (Mondelez)", "PEP (Pepsi)", "KO (Coca-Cola)", "KHC (Kraft)", "GIS (General Mills)", "HSY (Hershey)", "TSN (Tyson)"]}
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

# Ana Tablo (Seçim mekanizması düzeltildi)
    selection_event = st.dataframe(
        res.style.map(color_signal, subset=['Sinyal']),
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row", # BURASI DÜZELTİLDİ: "single-row"
        key="main_table"
    )

# --- DETAY PANELİ (GÜNCELLENMİŞ VERSİYON) ---
    if selection_event.selection.rows:
        selected_idx = selection_event.selection.rows[0]
        ticker = res.iloc[selected_idx]['Ticker']
        
        # HATA BURADAYDI: ETF_HOLDINGS yerine ETF_INFO kullanıyoruz
        # Eğer ETF_INFO sözlüğünde bu ticker yoksa varsayılan değerleri getirir
        info = ETF_INFO.get(ticker, {"area": "Sektörel Veri", "stocks": ["Veri Mevcut Değil"]})
        
        st.success(f"🔍 **{ticker} Analiz Paneli**")
        
        # Yeni eklenen Odak Alanı bilgisi
        st.info(f"🌐 **Odak Alanı:** {info['area']}")
        
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Fusion Skoru:** {res.iloc[selected_idx]['Fusion Skor']}/5")
            st.write(f"**Whale Power:** %{res.iloc[selected_idx]['Whale Power']}")
        with c2:
            st.write("**Bileşen Balinalar (Top Holdings):**")
            # info içindeki 'stocks' listesini döner
            for h in info['stocks']:
                st.write(f"• {h}")
        st.divider()

    # Grafik
    fig = px.scatter(res, x="RS Gücü", y="Whale Power", text="Ticker", 
                     color="Sinyal", size="Fusion Skor", title="Piyasa Matrisi")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Lütfen 'Deep Scan' butonuna basarak taramayı başlatın.")
