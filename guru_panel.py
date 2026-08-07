import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Portföy Diversifikasyon ve Maliyet Takip Sistemi")

# 1. Varsayılan Başlangıç Verisi (Manuel olarak arayüzden değiştirilebilir)
initial_data = {
    "Varlık": ["BTC", "NVDA", "THYAO", "Altın (Gram)", "XLU"],
    "Ana Sınıf": ["Kripto", "ABD Hisse", "BIST", "Emtia", "ABD Hisse"],
    "Sektör": ["L1 Zincir", "Yarı İletken", "Havacılık", "Kıymetli Maden", "Altyapı/Enerji"],
    "Miktar": [0.25, 15.0, 500.0, 150.0, 20.0],
    "Birim Maliyet": [42000.0, 95.0, 250.0, 2100.0, 60.0],
    "Güncel Fiyat": [64000.0, 130.0, 310.0, 2450.0, 72.0]
}

df_initial = pd.DataFrame(initial_data)

st.markdown("### 📝 Manuel Portföy Veri Girişi")
st.write("Aşağıdaki tabloya tıklayarak verileri düzenleyebilir, en alta inerek yeni varlıklar (Örn: yeni coinler veya fonlar) ekleyebilirsin.")

# 2. Dinamik Veri Editörü (Kullanıcı manuel entry yapar, satır ekleyip çıkarabilir)
edited_df = st.data_editor(
    df_initial,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Miktar": st.column_config.NumberColumn(format="%.4f"),
        "Birim Maliyet": st.column_config.NumberColumn(format="$ %.2f"),
        "Güncel Fiyat": st.column_config.NumberColumn(format="$ %.2f"),
    }
)

# 3. Arka Plan Hesaplamaları
edited_df["Toplam Maliyet"] = edited_df["Miktar"] * edited_df["Birim Maliyet"]
edited_df["Güncel Değer"] = edited_df["Miktar"] * edited_df["Güncel Fiyat"]
edited_df["Kar/Zarar (%)"] = ((edited_df["Güncel Fiyat"] - edited_df["Birim Maliyet"]) / edited_df["Birim Maliyet"]) * 100

st.markdown("### 📊 Portföy Dağılımı (Sankey Diyagramı)")

# 4. Sankey Diyagramı için Veri Hazırlığı
def generate_sankey(df):
    # Düğümleri (Nodes) oluştur: Portföy -> Ana Sınıf -> Sektör -> Varlık
    labels = ["Tüm Portföy"] + list(df["Ana Sınıf"].unique()) + list(df["Sektör"].unique()) + list(df["Varlık"].unique())
    label_dict = {label: i for i, label in enumerate(labels)}

    source = []
    target = []
    value = []

    # Seviye 1: Tüm Portföy -> Ana Sınıf
    for sinif, group in df.groupby("Ana Sınıf"):
        source.append(label_dict["Tüm Portföy"])
        target.append(label_dict[sinif])
        value.append(group["Güncel Değer"].sum())

    # Seviye 2: Ana Sınıf -> Sektör
    for (sinif, sektor), group in df.groupby(["Ana Sınıf", "Sektör"]):
        source.append(label_dict[sinif])
        target.append(label_dict[sektor])
        value.append(group["Güncel Değer"].sum())

    # Seviye 3: Sektör -> Varlık
    for (sektor, varlik), group in df.groupby(["Sektör", "Varlık"]):
        source.append(label_dict[sektor])
        target.append(label_dict[varlik])
        value.append(group["Güncel Değer"].sum())

    # 5. Çizim İşlemi (Görseldeki koyu tema ve mavi akış renklerine benzer şekilde)
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=25,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="#2E86C1"
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color="rgba(52, 152, 219, 0.4)" # Yarı saydam mavi akış
        )
    )])

    fig.update_layout(
        title_text="Endüstri ve Varlık Bazlı Dağılım",
        font_size=12,
        height=700,
        plot_bgcolor='black',
        paper_bgcolor='#1E1E1E',
        font=dict(color='white')
    )
    return fig

# Tablo boş değilse diyagramı çiz
if not edited_df.empty:
    fig = generate_sankey(edited_df)
    st.plotly_chart(fig, use_container_width=True)
    
    # Alt kısımda özet istatistikler
    st.markdown("### 📈 Özet Metrikler")
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Yatırılan Tutar", f"${edited_df['Toplam Maliyet'].sum():,.2f}")
    col2.metric("Güncel Portföy Büyüklüğü", f"${edited_df['Güncel Değer'].sum():,.2f}")
    
    toplam_kar_zarar_yuzde = ((edited_df['Güncel Değer'].sum() - edited_df['Toplam Maliyet'].sum()) / edited_df['Toplam Maliyet'].sum()) * 100
    col3.metric("Toplam Portföy Kar/Zarar", f"{toplam_kar_zarar_yuzde:.2f}%")
