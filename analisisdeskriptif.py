import pandas as pd
import matplotlib.pyplot as plt

# =====================
# 1. Load Data
# =====================
df = pd.read_csv("Most_Streamed_Spotify_Songs_2024_Cleaned_Median_Imputed.csv")

# =====================
# 2. Pilih variabel numerik utama
# =====================
cols = [
    'Track Score',
    'Spotify Streams',
    'YouTube Views',
    'TikTok Views',
    'Pandora Streams',
    'Shazam Counts'
]

num = df[cols]

# =====================
# 3. Statistik dasar
# =====================
print("\n=== Mean ===")
print(num.mean())

print("\n=== Median ===")
print(num.median())

print("\n=== Std (Standard Deviation) ===")
print(num.std())

# =====================
# 4. Korelasi
# =====================
print("\n=== Korelasi Antar Variabel ===")
print(num.corr())

# =====================
# 5. Plot distribusi histogram
# =====================
for c in cols:
    plt.figure(figsize=(6,4))
    df[c].hist(bins=40, edgecolor='black')
    plt.title(f"Distribution of {c}")
    plt.xlabel(c)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(f"{c.replace(' ', '_').lower()}_dist.png")
    plt.close()

print("\nPNG charts generated!")
