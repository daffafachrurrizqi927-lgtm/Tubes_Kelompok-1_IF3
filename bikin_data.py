import pandas as pd
import requests
import time
from datetime import datetime, timedelta

# 1. Konfigurasi Lokasi Nyata di Jawa Barat (Nama, Lat, Lon)
# Saya masukkan 35 titik tersebar (Bandung, Bogor, Cirebon, Pantai, Pegunungan)
locations = [
    {"kota": "Bandung (Kota)", "lat": -6.9175, "lon": 107.6191},
    {"kota": "Bandung (Lembang)", "lat": -6.8123, "lon": 107.6040},
    {"kota": "Bandung (Soreang)", "lat": -7.0250, "lon": 107.5190},
    {"kota": "Bandung (Majalaya)", "lat": -7.0500, "lon": 107.7500},
    {"kota": "Cimahi", "lat": -6.8715, "lon": 107.5744},
    {"kota": "Bogor (Kota)", "lat": -6.5971, "lon": 106.8060},
    {"kota": "Bogor (Cibinong)", "lat": -6.4795, "lon": 106.8436},
    {"kota": "Bogor (Puncak)", "lat": -6.7020, "lon": 106.9940},
    {"kota": "Depok", "lat": -6.4025, "lon": 106.7942},
    {"kota": "Bekasi (Kota)", "lat": -6.2383, "lon": 106.9756},
    {"kota": "Bekasi (Cikarang)", "lat": -6.2610, "lon": 107.1520},
    {"kota": "Karawang", "lat": -6.3040, "lon": 107.3050},
    {"kota": "Purwakarta", "lat": -6.5560, "lon": 107.4420},
    {"kota": "Subang (Kota)", "lat": -6.5710, "lon": 107.7600},
    {"kota": "Subang (Pamanukan)", "lat": -6.2830, "lon": 107.8160},
    {"kota": "Indramayu", "lat": -6.3270, "lon": 108.3220},
    {"kota": "Cirebon (Kota)", "lat": -6.7320, "lon": 108.5520},
    {"kota": "Cirebon (Sumber)", "lat": -6.7600, "lon": 108.4800},
    {"kota": "Kuningan", "lat": -6.9780, "lon": 108.4840},
    {"kota": "Majalengka (Kertajati)", "lat": -6.6500, "lon": 108.1300},
    {"kota": "Majalengka (Kota)", "lat": -6.8360, "lon": 108.2260},
    {"kota": "Sumedang", "lat": -6.8580, "lon": 107.9260},
    {"kota": "Garut (Kota)", "lat": -7.2270, "lon": 107.9080},
    {"kota": "Garut (Pameungpeuk)", "lat": -7.6500, "lon": 107.7300},
    {"kota": "Tasikmalaya (Kota)", "lat": -7.3270, "lon": 108.2200},
    {"kota": "Tasikmalaya (Singaparna)", "lat": -7.3500, "lon": 108.1100},
    {"kota": "Ciamis", "lat": -7.3260, "lon": 108.3530},
    {"kota": "Banjar", "lat": -7.3700, "lon": 108.5300},
    {"kota": "Pangandaran", "lat": -7.6970, "lon": 108.6540},
    {"kota": "Sukabumi (Kota)", "lat": -6.9270, "lon": 106.9300},
    {"kota": "Sukabumi (Pelabuhan Ratu)", "lat": -6.9870, "lon": 106.5500},
    {"kota": "Sukabumi (Ujung Genteng)", "lat": -7.3600, "lon": 106.4200},
    {"kota": "Cianjur (Kota)", "lat": -6.8200, "lon": 107.1400},
    {"kota": "Cianjur (Cipanas)", "lat": -6.7300, "lon": 107.0400},
    {"kota": "Cianjur (Sindangbarang)", "lat": -7.4500, "lon": 107.1300},
]

# 2. Setup Waktu (Ambil data 30 hari terakhir agar jadi ~1000 baris)
end_date = datetime.now().date()
start_date = end_date - timedelta(days=30) 

print(f"Sedang mengambil data faktual dari {start_date} sampai {end_date}...")
print("Mohon tunggu sebentar (Proses download data)...")

all_data = []

# 3. Loop Request ke Open-Meteo
# Kita gabungkan request lat/lon jadi satu biar cepat (batch processing)
url = "https://archive-api.open-meteo.com/v1/archive"

for loc in locations:
    params = {
        "latitude": loc['lat'],
        "longitude": loc['lon'],
        "start_date": start_date,
        "end_date": end_date,
        "daily": "rain_sum",
        "timezone": "Asia/Jakarta"
    }
    
    try:
        r = requests.get(url, params=params)
        data = r.json()
        
        # Parsing hasil
        dates = data['daily']['time']
        rains = data['daily']['rain_sum']
        
        for d, r_val in zip(dates, rains):
            # Tentukan status sederhana untuk data excel
            status = "Aman"
            if r_val is None: r_val = 0.0
            if r_val > 100: status = "Bahaya Ekstrem"
            elif r_val > 50: status = "Bahaya"
            elif r_val > 20: status = "Waspada"
            
            all_data.append({
                "Tanggal": d,
                "Lokasi_KabKota": loc['kota'],
                "Latitude": loc['lat'],
                "Longitude": loc['lon'],
                "Curah_Hujan_mm": r_val,
                "Status_Awal": status
            })
            
    except Exception as e:
        print(f"Error di {loc['kota']}: {e}")

# 4. Simpan ke Excel
df_hasil = pd.DataFrame(all_data)
nama_file = "data_hujan_faktual_jabar.xlsx"
df_hasil.to_excel(nama_file, index=False)

print("="*50)
print(f"SUKSES! Data berhasil disimpan di: {nama_file}")
print(f"Total Data: {len(df_hasil)} baris (Faktual).")
print("="*50)