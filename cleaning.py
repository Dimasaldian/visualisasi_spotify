# %% -------------------- IMPORT LIBRARIES --------------------
import pandas as pd
import numpy as np

# %% -------------------- LOAD DATA --------------------
# Ganti path ini sesuai file kamu
file_path = "Most Streamed Spotify Songs 2024.csv"

spotify = pd.read_csv(file_path, encoding="latin1")

print(spotify.info())

# %% -------------------- 1. CLEAN COLUMN NAMES --------------------
spotify.columns = (
    spotify.columns
    .str.replace(r"\.", "_", regex=True)
    .str.lower()
)

# %% -------------------- 2. CONVERT NUMERIC COLUMNS --------------------
numeric_cols = [
    "all_time_rank", "spotify_streams", "spotify_playlist_reach",
    "youtube_views", "youtube_playlist_reach",
    "airplay_spins", "siriusxm_spins",
    "deezer_playlist_reach",
    "pandora_streams", "shazam_counts"
]

for col in numeric_cols:
    if col in spotify.columns:
        spotify[col] = pd.to_numeric(spotify[col], errors="coerce")

# %% -------------------- 3. CONVERT RELEASE DATE --------------------
if "release_date" in spotify.columns:
    spotify["release_date"] = pd.to_datetime(
        spotify["release_date"],
        format="%m/%d/%Y",
        errors="coerce"
    )

# %% -------------------- 4. ALL TIME RANK AS ORDERED FACTOR --------------------
if "all_time_rank" in spotify.columns:
    spotify["all_time_rank_factor"] = (
        spotify["all_time_rank"]
        .rank(method="first", ascending=False)  # reverse order R-style
        .astype(int)
    )

# %% -------------------- 5. EXPLICIT TRACK LOGICAL --------------------
if "explicit_track" in spotify.columns:
    spotify["explicit_track_logical"] = spotify["explicit_track"].map({
        0: False,
        1: True
    })

# %% -------------------- CHECK MISSING VALUES --------------------
print("\nMissing values per column:")
print(spotify.isna().sum().sort_values(ascending=False))

# %% -------------------- 6. DROP 'tidal_popularity' COLUMN --------------------
if "tidal_popularity" in spotify.columns:
    spotify = spotify.drop(columns=["tidal_popularity"])

# %% -------------------- 7. REPLACE NA WITH ZERO FOR NUMERIC COLUMNS --------------------
num_cols = spotify.select_dtypes(include=["float64", "int64"]).columns
spotify[num_cols] = spotify[num_cols].fillna(0)

# %% -------------------- 8. REMOVE DUPLICATED ROWS --------------------
before = len(spotify)
spotify = spotify.drop_duplicates(keep="first")
after = len(spotify)

print(f"\nDuplicates removed: {before - after}")

# %% -------------------- FINAL CHECK --------------------
print("\nFinal dataset info:")
print(spotify.info())

# Dataset cleaned and ready to analyze
