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
st.set_page_config(layout="wide", page_title="AETHER NEXUS | PORTFOLIO", page_icon="🌌")

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
# 2. PORTFÖY TANIMLAMALARI (KULLANICI GİRİŞİ)
# ==========================================
# Kendi portföyünü buraya gir. 
# Type: US_STOCK, TR_STOCK, ETF, TEFAS, GOLD, SILVER, CASH, MANUAL
PORTFOLIO = [
    {"symbol": "NVDA", "type": "US_STOCK", "qty": 15.5, "avg_cost": 120.0, "currency": "USD"},
    {"symbol": "AAPL", "type": "US_STOCK", "qty": 20, "avg_cost": 150.0, "currency": "USD"},
    {"symbol": "THYAO.IS", "type": "TR_STOCK", "qty": 500, "avg_cost": 250.0, "currency": "TRY"},
    {"symbol": "TUPRS.IS", "type": "TR_STOCK", "qty": 200, "avg_cost": 130.0, "currency": "TRY"},
    {"symbol": "QQQ", "type": "ETF", "qty": 10, "avg_cost": 400.0, "currency": "USD"},
    {"symbol": "MAC", "type": "TEFAS", "qty": 15000, "avg_cost": 0.08, "currency": "TRY"},
    {"symbol": "IIH", "type": "TEFAS", "qty": 25000, "avg_cost": 0.05, "currency": "TRY"},
    {"symbol": "GOLD", "type": "GOLD", "qty": 50, "avg_cost": 2000.0, "currency": "TRY", "unit": "gram"},
    {"symbol": "SILVER", "type": "SILVER", "qty": 100, "avg_cost": 25.0, "currency": "TRY", "unit": "gram"},
    {"symbol": "NAKIT_TL", "type": "CASH", "qty": 50000, "avg_cost": 1, "currency": "TRY"},
    {"symbol": "NAKIT_USD", "type": "CASH", "qty": 2000, "avg_cost": 1, "currency": "USD"},
    {"symbol": "GAYRIMENKUL", "type": "MANUAL", "qty": 1, "avg_cost": 3000000, "current_price": 3500000, "currency": "TRY"}
]

# ==========================================
# 3. VERİ ÇEKME MOTORLARI (API & SCRAPING)
# ==========================================
@st.cache_data(ttl=600)
def get_usd_try():
    try:
        usd_try = yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1]
        return float(usd_try)
    except: return 34.50 # Hata durumunda varsayılan (güncelleyiniz)

@st.cache_data(ttl=3600)
def get_yfinance_history(symbol, period="1y"):
    try:
        return yf.Ticker(symbol).history(period=period)['Close']
    except:
        return pd.Series(dtype=float)

@st.cache_data(ttl=3600)
def get_tefas_price(fund_code):
    """TEFAS web sitesinden anlık fon fiyatını çeker."""
    try:
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        price_str = soup.find('span', string='Son Fiyat').find_next_sibling('span').text
        return float(price_str.replace('.', '').replace(',', '.'))
    except Exception as e:
        return None

# ==========================================
# 4. HESAPLAMA MOTORU
# ==========================================
def calculate_portfolio():
    usd_try = get_usd_try()
    
    # Altın/Gümüş Ons fiyatları
    gold_history = get_yfinance_history("GC=F")
    silver_history = get_yfinance_history("SI=F")
    
    current_gold_oz_usd = gold_history.iloc[-1] if not gold_history.empty else 2500
    current_silver_oz_usd = silver_history.iloc[-1] if not silver_history.empty else 30
    
    # 1 Ons = 31.1035 Gram
    current_gold_gram_try = (current_gold_oz_usd / 31.1035) * usd_try
    current_silver_gram_try = (current_silver_oz_usd / 31.1035) * usd_try

    results = []
    
    for item in PORTFOLIO:
        symbol = item["symbol"]
        ptype = item["type"]
        qty = item["qty"]
        avg_cost = item["avg_cost"]
        curr = item["currency"]
        
        current_price = 0
        hist_data = pd.Series(dtype=float)
        
        if ptype in ["US_STOCK", "TR_STOCK", "ETF"]:
            hist_data = get_yfinance_history(symbol)
            if not hist_data.empty:
                current_price = hist_data.iloc[-1]
                
        elif ptype == "TEFAS":
            fetched_price = get_tefas_price(symbol)
            if fetched_price: current_price = fetched_price
            else: current_price = avg_cost # Hata yedeği
            
        elif ptype == "GOLD":
            current_price = current_gold_gram_try if item.get("unit") == "gram" else current_gold_oz_usd
        elif ptype == "SILVER":
            current_price = current_silver_gram_try if item.get("unit") == "gram" else current_silver_oz_usd
            
        elif ptype == "MANUAL":
            current_price = item.get("current_price", avg_cost)
            
        elif ptype == "CASH":
            current_price = 1.0

        # Değer Hesaplamaları
        total_val_native = qty * current_price
        total_cost_native = qty * avg_cost
        profit_native = total_val_native - total_cost_native
        pct_change = (profit_native / total_cost_native * 100) if total_cost_native > 0 else 0
        
        # TRY ve USD Çevirileri
        total_val_try = total_val_native if curr == "TRY" else total_val_native * usd_try
        total_val_usd = total_val_native if curr == "USD" else total_val_native / usd_try
        
        # Geçmiş Dönem Hesaplamaları (Sadece yfinance verisi olanlar için)
        changes = {"1D": 0, "1W": 0, "1M": 0, "3M": 0, "6M": 0, "1Y": 0}
        if not hist_data.empty and len(hist_data) > 0:
            def get_past_price(days):
                try: return hist_data.iloc[-min(days, len(hist_data))]
                except: return current_price
            
            changes["1D"] = (current_price / get_past_price(2) - 1) * 100
            changes["1W"] = (current_price / get_past_price(5) - 1) * 100
            changes["1M"] = (current_price / get_past_price(21) - 1) * 100
            changes["3M"] = (current_price / get_past_price(63) - 1) * 100
            changes["6M"] = (current_price / get_past_price(126) - 1) * 100
            changes["1Y"] = (current_price / get_past_price(252) - 1) * 100

        results.append({
            "Varlık": symbol,
            "Sınıf": ptype,
            "Miktar": qty,
            "Maliyet": avg_cost,
            "Güncel Fiyat": current_price,
            "Para Birimi": curr,
            "Kâr/Zarar %": pct_change,
            "Toplam (TRY)": total_val_try,
            "Toplam (USD)": total_val_usd,
            "1G %": changes["1D"],
            "1H %": changes["1W"],
            "1A %": changes["1M"],
            "3A %": changes["3M"],
            "1Y %": changes["1Y"]
        })
        
    return pd.DataFrame(results), usd_try

# ==========================================
# 5. ARAYÜZ (DASHBOARD)
# ==========================================
col_hdr1, col_hdr2 = st.columns([4, 1])
with col_hdr1:
    st.markdown("<h1>🌌 AETHER NEXUS <span style='color:#00f3ff;'>PORTFOLIO</span></h1>", unsafe_allow_html=True)
with col_hdr2:
    if st.button("🔄 VERİLERİ SENKRONİZE ET"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Uydulara bağlanılıyor, piyasa verileri çekiliyor..."):
    df_port, usd_try = calculate_portfolio()

# ANA METRİKLER
tot_try = df_port['Toplam (TRY)'].sum()
tot_usd = df_port['Toplam (USD)'].sum()

# Toplam Maliyet Hesaplama
total_cost_try = 0
for idx, row in df_port.iterrows():
    if PORTFOLIO[idx]['currency'] == "TRY":
        total_cost_try += row['Maliyet'] * row['Miktar']
    else:
        total_cost_try += (row['Maliyet'] * row['Miktar']) * usd_try

total_profit_try = tot_try - total_cost_try
total_profit_pct = (total_profit_try / total_cost_try * 100) if total_cost_try > 0 else 0

st.markdown("<br>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>NET DEĞER (TRY)</div>
            <div class='metric-val'>₺ {tot_try:,.2f}</div>
            <div class='metric-sub'>USD/TRY: {usd_try:.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>NET DEĞER (USD)</div>
            <div class='metric-val' style='color:#b829ff;'>$ {tot_usd:,.2f}</div>
            <div class='metric-sub'>Global Satın Alma Gücü</div>
        </div>
    """, unsafe_allow_html=True)

profit_color = "pos-change" if total_profit_pct >= 0 else "neg-change"
sign = "+" if total_profit_pct >= 0 else ""
with m3:
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>TÜM ZAMANLAR K/Z</div>
            <div class='metric-val {profit_color}'>{sign}₺ {total_profit_try:,.0f}</div>
            <div class='metric-sub {profit_color}'>{sign}%{total_profit_pct:.2f} Toplam Büyüme</div>
        </div>
    """, unsafe_allow_html=True)

# 1 Günlük Değişim Yaklaşımı (Sadece Hisse/ETF)
daily_profit = (df_port['Toplam (TRY)'] * (df_port['1G %'] / 100)).sum()
daily_color = "pos-change" if daily_profit >= 0 else "neg-change"
dsign = "+" if daily_profit >= 0 else ""
with m4:
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>24S DEĞİŞİM P&L</div>
            <div class='metric-val {daily_color}'>{dsign}₺ {daily_profit:,.0f}</div>
            <div class='metric-sub {daily_color}'>Günlük Volatilite Etkisi</div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 6. GÖRSELLEŞTİRME (PLOTLY)
# ==========================================
st.markdown("### 🧬 Varlık Dağılım Topolojisi")
c_chart1, c_chart2 = st.columns(2)

# Grafik 1: Varlık Sınıfı Dağılımı
df_grouped = df_port.groupby('Sınıf')['Toplam (TRY)'].sum().reset_index()
fig_donut = px.pie(
    df_grouped, values='Toplam (TRY)', names='Sınıf', hole=0.7,
    color_discrete_sequence=['#00f3ff', '#b829ff', '#ff0055', '#00ff88', '#ffaa00', '#444444']
)
fig_donut.update_layout(
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#e0e0e0'),
    margin=dict(t=20, b=20, l=20, r=20),
    showlegend=True
)
fig_donut.add_annotation(text="VARLIK<br>SINIFI", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="#00f3ff")
c_chart1.plotly_chart(fig_donut, use_container_width=True)

# Grafik 2: En Büyük Pozisyonlar (Bar Chart)
df_sorted = df_port.sort_values(by='Toplam (TRY)', ascending=True).tail(10)
fig_bar = px.bar(
    df_sorted, x='Toplam (TRY)', y='Varlık', orientation='h',
    color='Kâr/Zarar %', color_continuous_scale=['#ff0055', '#222222', '#00ff88']
)
fig_bar.update_layout(
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#e0e0e0'),
    xaxis=dict(showgrid=True, gridcolor='#333'),
    yaxis=dict(showgrid=False),
    margin=dict(t=20, b=20, l=20, r=20)
)
c_chart2.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 7. DETAYLI PORTFÖY MATRİSİ
# ==========================================
st.markdown("### 🗃️ Kuantum Veri Matrisi (Tam Liste)")

# Formatlama
df_display = df_port.copy()
format_dict = {
    'Maliyet': '{:.2f}', 'Güncel Fiyat': '{:.2f}', 
    'Kâr/Zarar %': '{:+.2f}%', 'Toplam (TRY)': '₺{:,.0f}', 'Toplam (USD)': '${:,.0f}',
    '1G %': '{:+.2f}%', '1H %': '{:+.2f}%', '1A %': '{:+.2f}%', '1Y %': '{:+.2f}%'
}

def color_profit(val):
    if pd.isna(val) or type(val) == str: return ''
    color = '#00ff88' if val > 0 else '#ff0055' if val < 0 else '#888'
    return f'color: {color}; font-weight: bold;'

st.dataframe(
    df_display.style.format(format_dict)
    .map(color_profit, subset=['Kâr/Zarar %', '1G %', '1H %', '1A %', '1Y %'])
    .set_properties(**{'background-color': '#111', 'color': '#e0e0e0', 'border-color': '#333'}),
    use_container_width=True,
    height=400
)
