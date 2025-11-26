import math
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import streamlit as st

# ==========================================================
# 0. GLOBAL STYLE (Plotly)
# ==========================================================
px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = px.colors.qualitative.Set2

BG_DARK = "#191414"   # Spotify dark
FG_TEXT = "white"

# ==========================================================
# 1. LOAD & CLEAN DATA
# ==========================================================

@st.cache_data
def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="latin1")

    # Bersihkan whitespace nama kolom
    df.columns = df.columns.str.strip()

    # Numeric fields yang punya koma pemisah ribuan
    numeric_fields = [
        "Spotify Streams",
        "Spotify Playlist Count",
        "Spotify Playlist Reach",
        "Spotify Popularity",
        "YouTube Views",
        "YouTube Likes",
        "TikTok Posts",
        "TikTok Likes",
        "TikTok Views",
        "YouTube Playlist Reach",
        "Apple Music Playlist Count",
        "AirPlay Spins",
        "SiriusXM Spins",
        "Deezer Playlist Count",
        "Deezer Playlist Reach",
        "Amazon Playlist Count",
        "Pandora Streams",
        "Pandora Track Stations",
        "Soundcloud Streams",
        "Shazam Counts",
        "TIDAL Popularity",
    ]

    for col in numeric_fields:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(",", "", regex=False)
                .replace("nan", np.nan)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse tanggal
    if "Release Date" in df.columns:
        df["Release Date"] = pd.to_datetime(
            df["Release Date"], format="%m/%d/%Y", errors="coerce"
        )
        df["Year"] = df["Release Date"].dt.year

    # Label tampilan: Track – Artist
    df["SongLabel"] = df["Track"].astype(str) + " – " + df["Artist"].astype(str)

    # Explicit boolean
    if "Explicit Track" in df.columns:
        df["Explicit"] = df["Explicit Track"].astype(int).replace({1: True, 0: False})
    else:
        df["Explicit"] = False

    return df


df = load_data("Most Streamed Spotify Songs 2024.csv")


# ==========================================================
# 2. PAGE SETUP & FILTER
# ==========================================================

st.set_page_config(page_title="Spotify Dashboard", layout="wide")
st.sidebar.title("⚙️ Filter Dataset")

# Filter tahun
if "Year" in df.columns:
    min_y = int(df["Year"].min())
    max_y = int(df["Year"].max())

    year_rng = st.sidebar.slider(
        "Filter Tahun Rilis",
        min_value=min_y,
        max_value=max_y,
        value=(min_y, max_y),
    )
    df = df[df["Year"].between(year_rng[0], year_rng[1])]

# Filter explicit
filter_explicit = st.sidebar.radio(
    "Filter Explicit",
    ("Semua", "Explicit", "Non Explicit")
)

if filter_explicit == "Explicit":
    df = df[df["Explicit"] == True]
elif filter_explicit == "Non Explicit":
    df = df[df["Explicit"] == False]

# Top N
top_n = st.sidebar.slider("Top N Ranking", 5, 50, 10, 5)


# ==========================================================
# 3. HEADER KPIs
# ==========================================================

st.title("🎧 Spotify Most Streamed Songs 2024 Dashboard")

total_streams = df["Spotify Streams"].sum()
total_streams_B = total_streams / 1e9 if not np.isnan(total_streams) else 0

# jumlah rekaman unik → pakai ISRC kalau ada
if "ISRC" in df.columns:
    total_tracks = df["ISRC"].nunique()
else:
    total_tracks = df["Track"].nunique()

total_artists = df["Artist"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("📀 Total Stream Spotify", f"{total_streams_B:.2f} B")
col2.metric("🎵 Jumlah Track (ISRC)", int(total_tracks))
col3.metric("👤 Jumlah Artist", int(total_artists))

st.markdown("---")


# ==========================================================
# 4. TOP SONGS (Per ISRC)
# ==========================================================

st.subheader(f"🏆 Top {top_n} Most Streamed Songs (Per ISRC)")

top_songs = (
    df.sort_values("Spotify Streams", ascending=False)
      .head(top_n)
      .copy()
)

top_songs["Streams_B"] = top_songs["Spotify Streams"] / 1e9

fig_isrc = px.bar(
    top_songs,
    x="Streams_B",
    y="SongLabel",
    orientation="h",
    color_discrete_sequence=["#1DB954"],  # Spotify green
    labels={
        "SongLabel": "",
        "Streams_B": "Spotify Streams (B)"
    },
)

fig_isrc.update_traces(
    text=top_songs["Streams_B"].round(2).astype(str) + "B",
    textposition="outside"
)

fig_isrc.update_layout(
    plot_bgcolor=BG_DARK,
    paper_bgcolor=BG_DARK,
    font_color=FG_TEXT,
    xaxis=dict(
        tickformat=".2f",
        title="Spotify Streams (B)",
    ),
    yaxis=dict(
        categoryorder='array',
        categoryarray=list(top_songs["SongLabel"]),
        title=""
    ),
    margin=dict(l=180, r=40, t=10, b=10),
    showlegend=False,
)

st.plotly_chart(fig_isrc, use_container_width=True, key="chart_top_songs")


# ==========================================================
# 5. TOP ARTISTS (aggregate)
# ==========================================================

st.subheader("🎤 Top Artists berdasarkan Total Spotify Streams")

top_artists = (
    df.groupby("Artist", as_index=False)["Spotify Streams"]
      .sum()
      .sort_values("Spotify Streams", ascending=False)
      .head(top_n)
      .copy()
)

top_artists["Streams_B"] = top_artists["Spotify Streams"] / 1e9

fig2 = px.bar(
    top_artists,
    x="Streams_B",
    y="Artist",
    orientation="h",
    color_discrete_sequence=["#1DB954"],
    labels={
        "Artist": "",
        "Streams_B": "Spotify Streams (B)"
    },
)

fig2.update_traces(
    text=top_artists["Streams_B"].round(2).astype(str) + "B",
    textposition="outside"
)

fig2.update_layout(
    plot_bgcolor=BG_DARK,
    paper_bgcolor=BG_DARK,
    font_color=FG_TEXT,
    yaxis=dict(autorange="reversed"),
    margin=dict(l=160, r=40, t=10, b=10),
    showlegend=False,
)

st.plotly_chart(fig2, use_container_width=True, key="chart_top_artists")

st.markdown("---")


# ==========================================================
# 6. LINE — AVG POPULARITY PER 5 TAHUN
# ==========================================================

st.subheader("📈 Rata-rata Popularity per Era (5 Tahun)")

def era_5(y):
    if pd.isna(y):
        return np.nan
    y = int(y)
    base = (y // 5) * 5
    return f"{base}-{base+4}"

if "Spotify Popularity" in df.columns and "Year" in df.columns:
    df["Era"] = df["Year"].apply(era_5)

    era_view = (
        df.dropna(subset=["Era"])
          .groupby("Era", as_index=False)["Spotify Popularity"]
          .mean()
    )

    fig3 = px.line(
        era_view,
        x="Era",
        y="Spotify Popularity",
        markers=True,
        labels={"Era": "Era (5 Tahun)", "Spotify Popularity": "Avg Popularity"},
    )
    fig3.update_layout(
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font_color=FG_TEXT,
        margin=dict(l=60, r=40, t=20, b=40),
    )
    st.plotly_chart(fig3, use_container_width=True, key="chart_era_pop")
else:
    st.info("Kolom Year atau Spotify Popularity tidak tersedia.")

st.markdown("---")


# ==========================================================
# 7. PIE – Explicit vs Non Explicit
# ==========================================================

st.subheader("🔞 Proporsi Explicit vs Non-Explicit")

exp_data = (
    df["Explicit"]
    .value_counts()
    .rename(index={True: "Explicit", False: "Non Explicit"})
    .reset_index()
)
exp_data.columns = ["Type", "Count"]

fig4 = px.pie(
    exp_data,
    names="Type",
    values="Count",
    hole=0.45,
    color="Type",
    color_discrete_map={
        "Explicit": "#FF2E63",
        "Non Explicit": "#1DB954",
    },
)

fig4.update_traces(textinfo="percent+label")
fig4.update_layout(
    plot_bgcolor=BG_DARK,
    paper_bgcolor=BG_DARK,
    font_color=FG_TEXT,
    margin=dict(l=40, r=40, t=20, b=20),
    showlegend=True,
)

st.plotly_chart(fig4, use_container_width=True, key="chart_explicit")

st.markdown("---")


# ==========================================================
# 8. SCATTER TikTok vs Spotify
# ==========================================================

st.subheader("📊 Viralitas vs Konsumsi — TikTok Views vs Spotify Streams")

if "TikTok Views" in df.columns:

    mode = st.selectbox(
        "Level Data Scatter",
        ("Per Lagu (rekaman/ISRC)", "Per Artist"),
        help="Per Lagu: 1 titik = 1 baris/rekaman. Per Artist: agregasi per artist."
    )

    if mode.startswith("Per Lagu"):
        dscatter = df.copy()
        hover = "SongLabel"
        color_col = "Artist"
    else:
        dscatter = (
            df.groupby("Artist", as_index=False)[["TikTok Views", "Spotify Streams"]]
              .sum()
        )
        dscatter["SongLabel"] = dscatter["Artist"]
        hover = "Artist"
        color_col = "Artist"

    dscatter = dscatter.replace(0, np.nan).dropna(
        subset=["TikTok Views", "Spotify Streams"]
    )

    if not dscatter.empty:
        fig5 = px.scatter(
            dscatter,
            x="TikTok Views",
            y="Spotify Streams",
            size="Spotify Streams",
            hover_name=hover,
            color=color_col,
            size_max=22,
            labels={
                "TikTok Views": "TikTok Views (log)",
                "Spotify Streams": "Spotify Streams (log)",
            },
        )
        fig5.update_xaxes(type="log")
        fig5.update_yaxes(type="log")
        fig5.update_layout(
            plot_bgcolor=BG_DARK,
            paper_bgcolor=BG_DARK,
            font_color=FG_TEXT,
            margin=dict(l=60, r=40, t=20, b=40),
        )
        st.plotly_chart(fig5, use_container_width=True, key="chart_tiktok_scatter")
    else:
        st.info("Data scatter kosong setelah filter.")
else:
    st.info("Kolom TikTok Views tidak tersedia.")

st.markdown("---")


# ==========================================================
# 9. HEATMAP Korelasi
# ==========================================================

st.subheader("🧠 Korelasi antar Platform & Metric")

corr_fields = [
    "Spotify Streams",
    "Spotify Playlist Reach",
    "Spotify Popularity",
    "YouTube Views",
    "TikTok Views",
    "TikTok Likes",
    "Shazam Counts",
    "Soundcloud Streams",
    "AirPlay Spins",
    "SiriusXM Spins",
    "Pandora Streams",
]

corr_fields = [c for c in corr_fields if c in df.columns]

if len(corr_fields) >= 2:
    corr = df[corr_fields].corr()

    fig6 = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
    )
    fig6.update_layout(
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font_color=FG_TEXT,
        margin=dict(l=80, r=40, t=40, b=40),
    )
    st.plotly_chart(fig6, use_container_width=True, key="chart_corr_heatmap")
else:
    st.info("Tidak cukup kolom numerik untuk membuat korelasi.")

st.markdown("Dashboard selesai 🎉 silakan explore 🙌")