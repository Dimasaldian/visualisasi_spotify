import pandas as pd
import numpy as np

# 1. Load the original dataset dengan menambahkan 'encoding'
# Menggunakan 'latin1' untuk mengatasi UnicodeDecodeError
try:
    df = pd.read_csv("Most Streamed Spotify Songs 2024.csv", encoding='latin1')
except UnicodeDecodeError:
    # Jika latin1 gagal, coba cp1252
    df = pd.read_csv("Most Streamed Spotify Songs 2024.csv", encoding='cp1252')

print("File berhasil dimuat.")
print(f"Jumlah baris awal: {df.shape[0]}")

# 2. Hapus Kolom dengan Persentase Missing Value Sangat Tinggi (>= 46%)
columns_to_drop = [
    'TIDAL Popularity',  # 100% missing
    'Soundcloud Streams', # 72.46% missing
    'SiriusXM Spins'     # 46.15% missing (Imputasi terlalu berisiko)
]
df = df.drop(columns=columns_to_drop, axis=1)

# 3. Definisikan Kolom Numerik yang Perlu Dibersihkan (Hapus Koma dan Konversi ke Float)
stream_count_cols = [
    'Spotify Streams', 'Spotify Playlist Count', 'Spotify Playlist Reach',
    'YouTube Views', 'YouTube Likes', 'TikTok Posts', 'TikTok Likes',
    'TikTok Views', 'YouTube Playlist Reach', 'AirPlay Spins',
    'Deezer Playlist Reach', 'Pandora Streams', 'Pandora Track Stations',
    'Shazam Counts'
]

for col in stream_count_cols:
    # Mengganti koma dan mengkonversi ke float.
    df[col] = df[col].astype(str).str.replace(',', '', regex=False)
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 4. Imputasi Kolom Numerik dengan Median
float_cols_for_imputation = df.select_dtypes(include=np.number).columns.tolist()

float_cols_for_imputation = [col for col in float_cols_for_imputation if col not in ['Track Score', 'Explicit Track']]

for col in float_cols_for_imputation:
    median_val = df[col].median()
    df[col].fillna(median_val, inplace=True)

# 5. Menghapus Baris dengan NaN pada Kolom Kategorikal (Artist)
df.dropna(subset=['Artist'], inplace=True)

# 6. Verifikasi Akhir
print(f"Jumlah baris setelah cleaning: {df.shape[0]}")

# 7. Simpan Data yang Sudah Dibersihkan
output_file = 'Most_Streamed_Spotify_Songs_2024_Cleaned_Median_Imputed.csv'
df.to_csv(output_file, index=False)
print(f"Data yang sudah dibersihkan tersimpan di: {output_file}")