import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Monitor Cuaca Live",
    page_icon="⛈️",
    layout="wide"
)

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .metric-card {
        background-color: #262730;
        color: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

st.title("⛈️ Dashboard Cuaca Indonesia (Real-Time)")
st.markdown("Monitor peluang hujan (%) per jam di berbagai kota besar Indonesia.")

# --- 2. FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    # Pastikan file ini ada di folder yang sama
    file_path = "Data_Cuaca.xlsx"
    
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_excel(file_path)
        
        # --- CLEANING DATA ---
        if 'Peluang_Hujan' in df.columns:
            # Hapus simbol % dan ubah jadi angka integer
            df['Peluang_Angka'] = df['Peluang_Hujan'].astype(str).str.replace('%', '', regex=False)
            df['Peluang_Angka'] = pd.to_numeric(df['Peluang_Angka'], errors='coerce').fillna(0).astype(int)
        else:
            return pd.DataFrame()

        # Buat Kategori Risiko untuk Pie Chart
        def get_kategori(x):
            if x > 80: return "🔴 Badai (>80%)"
            elif x > 50: return "🟡 Hujan (>50%)"
            else: return "🟢 Aman (<50%)"
        
        df['Kategori_Risk'] = df['Peluang_Angka'].apply(get_kategori)

        # Gabungkan Tanggal & Jam untuk sorting yang benar
        df['Waktu_Lengkap'] = pd.to_datetime(df['Tanggal'].astype(str) + ' ' + df['Jam'].astype(str), errors='coerce')
        df = df.sort_values(by=['Kota', 'Waktu_Lengkap'])
        
        return df
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        return pd.DataFrame()

df = load_data()

# --- CEK DATA ---
if df is None or df.empty:
    st.error("⚠️ Data tidak ditemukan atau kosong.")
    st.info("Pastikan file 'Data_Cuaca_Hourly_Percent.xlsx' ada di folder yang sama.")
    st.stop()

# --- 3. SIDEBAR FILTER ---
st.sidebar.header("🔍 Filter Data")

# Filter Kota
kota_list = sorted(df['Kota'].unique().tolist())
# Default pilih semua kota agar peta langsung terlihat se-Indonesia
selected_kota = st.sidebar.multiselect("Pilih Kota:", kota_list, default=kota_list)

# Filter Tanggal
tanggal_list = sorted(df['Tanggal'].astype(str).unique().tolist())
if not tanggal_list:
    st.error("Data Tanggal Kosong.")
    st.stop()
selected_tanggal = st.sidebar.selectbox("Pilih Tanggal:", options=tanggal_list)

# --- 4. FILTER DATAFRAME ---
if not selected_kota:
    filtered_df = df[df['Tanggal'].astype(str) == selected_tanggal]
else:
    filtered_df = df[
        (df['Kota'].isin(selected_kota)) & 
        (df['Tanggal'].astype(str) == selected_tanggal)
    ]

if filtered_df.empty:
    st.warning("Tidak ada data untuk filter ini.")
    st.stop()

# --- 5. LOGIKA AUTO ZOOM PETA ---
# Hitung titik tengah dari kota yang dipilih
lat_center = filtered_df['Latitude'].mean()
lon_center = filtered_df['Longitude'].mean()

# Atur level zoom: Jika kota sedikit zoom dekat, jika banyak zoom jauh
zoom_level = 6 if len(selected_kota) <= 3 else 4

# --- 6. DASHBOARD UTAMA ---

# A. KPI (Statistik)
col1, col2, col3, col4 = st.columns(4)
avg_chance = filtered_df['Peluang_Angka'].mean()
max_chance = filtered_df['Peluang_Angka'].max()

# Cari lokasi dengan peluang tertinggi
idx_max = filtered_df['Peluang_Angka'].idxmax()
lokasi_max = filtered_df.loc[idx_max, 'Kota']
jam_max = filtered_df.loc[idx_max, 'Jam']

col1.metric("Rata-Rata Peluang", f"{avg_chance:.1f}%")
col2.metric("Peluang Tertinggi", f"{max_chance}%", f"{lokasi_max} ({jam_max})")
col3.metric("Total Lokasi", f"{len(filtered_df['Kota'].unique())} Kota")
col4.metric("Status Cuaca", "⛈️ Waspada" if max_chance > 50 else "☀️ Aman")

st.divider()

# B. GRAFIK LINE & PIE CHART
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Tren Peluang Hujan per Jam")
    
    # GRAFIK GARIS (LINE CHART) - LEBIH JELAS
    fig_line = px.line(
        filtered_df, 
        x="Jam", 
        y="Peluang_Angka", 
        color="Kota",
        markers=True,  # Menampilkan titik data
        title="Persentase Peluang (%)",
        labels={"Peluang_Angka": "Peluang (%)"},
        template="plotly_dark",
        range_y=[0, 105]
    )
    
    # Kustomisasi Garis & Titik
    fig_line.update_traces(
        line=dict(width=3), 
        marker=dict(size=8)
    )
    
    # Garis Batas Waspada
    fig_line.add_hline(
        y=50, line_dash="dot", line_color="#FF4B4B", 
        annotation_text="Batas Waspada (50%)", annotation_position="top right"
    )
    
    # Pindahkan Legenda ke Bawah agar grafik luas
    fig_line.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.subheader("🍰 Porsi Risiko Cuaca")
    # Hitung jumlah jam berdasarkan kategori risiko
    pie_data = filtered_df['Kategori_Risk'].value_counts().reset_index()
    pie_data.columns = ['Kategori', 'Jumlah']
    
    fig_pie = px.pie(
        pie_data, 
        names='Kategori', 
        values='Jumlah',
        color='Kategori',
        color_discrete_map={
            "🟢 Aman (<50%)": "#00CC96",
            "🟡 Hujan (>50%)": "#xFFA15A",
            "🔴 Badai (>80%)": "#EF553B"
        },
        hole=0.4 # Donut Chart
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# C. PETA SEBARAN (AUTO ZOOM)
st.subheader("🗺️ Peta Sebaran Lokasi")

# Ambil 1 data per kota untuk peta
map_df = filtered_df.drop_duplicates(subset=['Kota'])

fig_map = px.scatter_mapbox(
    map_df,
    lat="Latitude",
    lon="Longitude",
    hover_name="Kota",
    hover_data=["Deskripsi", "Peluang_Hujan"],
    color="Peluang_Angka",
    color_continuous_scale="RdYlGn_r", # Hijau aman, Merah bahaya
    size="Peluang_Angka",  # Ukuran titik sesuai peluang hujan
    size_max=35,           # Maksimum ukuran titik diperbesar agar terlihat
    zoom=zoom_level,       # Zoom otomatis
    center={"lat": lat_center, "lon": lon_center}, # Pusatkan peta
    mapbox_style="open-street-map",
    height=500
)
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map, use_container_width=True)

# D. TABEL DATA
with st.expander("📄 Lihat Data Detail"):
    st.dataframe(
        filtered_df[['Kota', 'Jam', 'Deskripsi', 'Peluang_Hujan', 'Kategori_Risk']], 
        use_container_width=True, 
        hide_index=True
    )