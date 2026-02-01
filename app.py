import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
from datetime import datetime
import requests
from bs4 import BeautifulSoup


# Inisialisasi fungsi scapping berita banjir
def scrape_berita_banjir():
    """
    Fitur ini BENAR-BENAR SCRAPING (Mengambil HTML dari web berita)
    Target: Google News (Search 'Banjir Jawa Barat')
    """
    try:
        url = "https://news.google.com/rss/search?q=banjir+jawa+barat&hl=id-ID&gl=ID&ceid=ID:id"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, features='xml') # Parsing XML/HTML
        
        berita_list = []
        items = soup.findAll('item')[:5] # Ambil 5 berita teratas
        
        for item in items:
            judul = item.title.text
            link = item.link.text
            tanggal = item.pubDate.text
            berita_list.append({'judul': judul, 'link': link, 'waktu': tanggal})
            
        return berita_list
    except Exception as e:
        return []

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Monitor Banjir Jawa Barat",
    layout="wide",
    page_icon="🌊"
)

st.title("🌧️ Curah Hujan di Jawa Barat serta Peringatan Siaga Banjir")
st.markdown("Dashboard monitoring berbasis data faktual untuk deteksi dini wilayah rawan banjir.")

# ==========================================
# 2. LOAD DATA DARI EXCEL
# ==========================================
@st.cache_data
def load_data_excel():
    try:
        # Membaca file hasil scraping
        df = pd.read_excel("data_hujan_faktual_jabar.xlsx")
        
        # memastikan format tanggal benar
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        # --- LOGIKA PENENTUAN STATUS & WARNA ---
        colors = []
        status_list = []
        radius_list = []
        
        for val in df['Curah_Hujan_mm']:
            if val > 100:
                # BAHAYA EKSTREM (Merah Pekat)
                colors.append([180, 0, 0, 255]) 
                status_list.append("BAHAYA EKSTREM")
                radius_list.append(6000)
            elif val > 50:
                # SIAGA BANJIR (Merah Terang)
                colors.append([255, 50, 50, 220]) 
                status_list.append("SIAGA BANJIR")
                radius_list.append(4000)
            elif val > 20:
                # WASPADA (Kuning/Oranye)
                colors.append([255, 165, 0, 180]) 
                status_list.append("Waspada")
                radius_list.append(2500)
            else:
                # AMAN (Hijau Transparan)
                colors.append([0, 128, 0, 100]) 
                status_list.append("Aman")
                radius_list.append(1000)
        
        df['Color'] = colors
        df['Status_Kini'] = status_list
        df['Radius'] = radius_list
        
        return df
    except FileNotFoundError:
        return None

# Load Data
df = load_data_excel()

if df is None:
    st.error("⚠️ File 'data_hujan_faktual_jabar.xlsx' tidak ditemukan!")
    st.stop()

# ==========================================
# 3. SIDEBAR: MODE TAMPILAN
# ==========================================
st.sidebar.header("⚙️ Navigasi Dashboard")

# --- FITUR PEMILIH MODE (KEMBALI ADA) ---
mode_tampilan = st.sidebar.radio(
    "Pilih Mode Tampilan:",
    ["🌏 Peta Sebaran (GIS)", "📊 Visualisasi & Analisis Data"]
)

st.sidebar.divider()

# ==========================================
# 4. LOGIKA TAMPILAN 1: PETA SEBARAN (GIS)
# ==========================================
if mode_tampilan == "🌏 Peta Sebaran (GIS)":
    
    st.sidebar.subheader("📅 Filter Waktu")
    min_date = df['Tanggal'].min().date()
    max_date = df['Tanggal'].max().date()
    
    # Pilih Tanggal hanya muncul di mode Peta
    tgl_pilih = st.sidebar.date_input("Tanggal Pemantauan:", max_date, min_value=min_date, max_value=max_date)
    
    # Filter Data
    df_display = df[df['Tanggal'].dt.date == tgl_pilih]
    
    # --- ALERT SYSTEM (PERINGATAN DINI) ---
    titik_banjir = df_display[df_display['Curah_Hujan_mm'] > 50]
    jumlah_bahaya = len(titik_banjir)

    if jumlah_bahaya > 0:
        st.error(f"🚨 PERINGATAN: Terdeteksi {jumlah_bahaya} Wilayah SIAGA BANJIR pada {tgl_pilih}!")
        kota_bahaya = ", ".join(titik_banjir['Lokasi_KabKota'].unique())
        st.markdown(f"**Wilayah Terdampak:** {kota_bahaya}")
    else:
        st.success(f"✅ Tanggal {tgl_pilih}: Kondisi terpantau AMAN.")
        
    st.divider()

    # --- METRIK & PETA ---
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Ringkasan")
        max_hujan = df_display['Curah_Hujan_mm'].max()
        lokasi_max = df_display.loc[df_display['Curah_Hujan_mm'].idxmax()]['Lokasi_KabKota'] if not df_display.empty else "-"
        
        st.metric("Curah Hujan Tertinggi", f"{max_hujan:.1f} mm")
        st.caption(f"Lokasi: {lokasi_max}")
        st.metric("Rata-rata Jabar", f"{df_display['Curah_Hujan_mm'].mean():.1f} mm")
        
        st.info("💡 **Legenda:**\n\n🔴 Merah: Banjir (>50mm)\n🟠 Oranye: Waspada (>20mm)\n🟢 Hijau: Aman")

    with col2:
        st.subheader(f"📍 Peta Potensi Banjir ({tgl_pilih})")
        
        layer_column = pdk.Layer(
            "ColumnLayer",
            data=df_display,
            get_position='[Longitude, Latitude]',
            get_elevation='Curah_Hujan_mm',
            elevation_scale=300, 
            radius=2000,
            get_fill_color='Color',
            pickable=True,
            auto_highlight=True,
        )

        layer_scatter = pdk.Layer(
            "ScatterplotLayer",
            data=df_display,
            get_position='[Longitude, Latitude]',
            get_radius='Radius',
            get_fill_color='Color',
            pickable=True,
            opacity=0.4,
            stroked=True,
            get_line_color=[255, 255, 255],
        )

        view_state = pdk.ViewState(latitude=-6.95, longitude=107.60, zoom=8, pitch=45)
        
        st.pydeck_chart(pdk.Deck(
            map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
            initial_view_state=view_state,
            layers=[layer_scatter, layer_column],
            tooltip={"html": "<b>{Lokasi_KabKota}</b><br/>Hujan: {Curah_Hujan_mm} mm<br/>Status: {Status_Kini}"}
        ))

# ==========================================
# 5. LOGIKA TAMPILAN 2: VISUALISASI DATA
# ==========================================
elif mode_tampilan == "📊 Visualisasi & Analisis Data":
    
    st.subheader("📈 Analisis Tren & Statistik")
    
    # Tabulasi agar rapi
    tab1, tab2, tab3 = st.tabs(["📊 Tren 30 Hari", "🏆 Top Wilayah Hujan", "📂 Data Mentah"])
    
    with tab1:
        st.write("Grafik pergerakan curah hujan di berbagai kota selama 30 hari terakhir.")
        
        # Pilihan Kota untuk dibandingkan
        list_kota = df['Lokasi_KabKota'].unique()
        kota_pilih = st.multiselect("Pilih Kota untuk dibandingkan:", list_kota, default=list_kota[:3])
        
        if not kota_pilih:
            df_chart = df # Tampilkan semua jika kosong
        else:
            df_chart = df[df['Lokasi_KabKota'].isin(kota_pilih)]
            
        chart_line = alt.Chart(df_chart).mark_line(point=True).encode(
            x=alt.X('Tanggal:T', title='Tanggal'),
            y=alt.Y('Curah_Hujan_mm:Q', title='Curah Hujan (mm)'),
            color=alt.Color('Lokasi_KabKota:N', title='Kota'),
            tooltip=['Tanggal', 'Lokasi_KabKota', 'Curah_Hujan_mm', 'Status_Kini']
        ).interactive()
        
        st.altair_chart(chart_line, use_container_width=True)
        
    with tab2:
        st.write("Akumulasi total curah hujan tertinggi selama periode pemantauan.")
        top_cities = df.groupby('Lokasi_KabKota')['Curah_Hujan_mm'].sum().nlargest(10).reset_index()
        
        bar_chart = alt.Chart(top_cities).mark_bar().encode(
            x=alt.X('Curah_Hujan_mm:Q', title='Total Hujan (mm)'),
            y=alt.Y('Lokasi_KabKota:N', sort='-x', title='Kota'),
            color=alt.Color('Curah_Hujan_mm:Q', scale=alt.Scale(scheme='reds')),
            tooltip=['Lokasi_KabKota', 'Curah_Hujan_mm']
        )
        st.altair_chart(bar_chart, use_container_width=True)
        
    with tab3:
        st.write("Data lengkap dari hasil scraping (Excel).")
        st.dataframe(df.sort_values(by='Tanggal', ascending=False), use_container_width=True)
        

# ==========================================
# TAMPILKAN HASIL SCRAPING DI SIDEBAR
# ==========================================
st.sidebar.divider()
st.sidebar.subheader("📰 Berita Banjir (Live Scraping)")

# Panggil fungsi scraping yang sudah kamu buat
berita_terkini = scrape_berita_banjir() 

if berita_terkini:
    for b in berita_terkini:
        # Tampilkan Judul Berita sebagai Link
        st.sidebar.markdown(f"[{b['judul']}]({b['link']})")
        st.sidebar.caption(f"🕒 {b['waktu']}")
else:
    st.sidebar.write("Belum ada berita terbaru.")