import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================================
# 0. KONFIGURASI HALAMAN & STYLE
# ==========================================================
st.set_page_config(
    page_title="Spotify Unified Dashboard",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Palet Warna
COLOR_SPOTIFY = "#1DB954"
COLOR_ACCENT = "#FF0055"   
COLOR_YOUTUBE = "#FF0000"
COLOR_TIKTOK = "#00F2EA"

# Template Plotly
px.defaults.template = "plotly_dark"

# ==========================================================
# 1. LOAD & CLEAN DATA (MERGE DUPLICATES)
# ==========================================================
@st.cache_data
def load_data(csv_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_path, encoding='latin1')
    except:
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
            return pd.DataFrame()

    df.columns = df.columns.str.strip()

    # 1. Cleaning Kolom Numerik
    numeric_fields = [
        "Spotify Streams", "Spotify Playlist Count", "Spotify Playlist Reach",
        "Spotify Popularity", "YouTube Views", "TikTok Views", "AirPlay Spins"
    ]

    for col in numeric_fields:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(",", "", regex=False)
                .replace("nan", np.nan)
                .replace("None", np.nan)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2. Parse Tanggal
    if "Release Date" in df.columns:
        df["Release Date"] = pd.to_datetime(df["Release Date"], errors="coerce")
        df["Year"] = df["Release Date"].dt.year
        df["Month"] = df["Release Date"].dt.month_name()
    
    # 3. Explicit Boolean
    if "Explicit Track" in df.columns:
        df["Explicit"] = df["Explicit Track"].apply(lambda x: True if x == 1 else False)
    else:
        df["Explicit"] = False

    # =================================================================
    # 4. AGREGASI (PENGGABUNGAN DATA)
    # =================================================================
    # Buat kolom 'Key' bersih untuk pengelompokan (lowercase)
    df['Track_Clean'] = df['Track'].astype(str).str.lower().str.strip()
    df['Artist_Clean'] = df['Artist'].astype(str).str.lower().str.strip()

    # Aturan penggabungan: Ambil nilai MAX untuk angka, agar tidak double counting
    agg_rules = {
        'Spotify Streams': 'max',           
        'Spotify Playlist Count': 'max',    
        'Spotify Playlist Reach': 'max',
        'Spotify Popularity': 'max',
        'YouTube Views': 'max',
        'TikTok Views': 'max',
        'AirPlay Spins': 'max',
        'Track': 'first',                   # Ambil nama asli yg pertama
        'Artist': 'first',
        'Year': 'first',
        'Month': 'first',
        'Explicit': 'max',                  # Jika salah satu True, jadikan True
    }
    
    # Hanya gunakan aturan untuk kolom yang benar-benar ada
    valid_agg_rules = {k: v for k, v in agg_rules.items() if k in df.columns}

    # Lakukan Grouping -> Lagu dengan judul & artis sama akan DILEBUR jadi satu
    df_merged = df.groupby(['Track_Clean', 'Artist_Clean'], as_index=False).agg(valid_agg_rules)
    
    # Buat Label Lagu
    df_merged["SongLabel"] = df_merged["Track"].astype(str) + " – " + df_merged["Artist"].astype(str)

    return df_merged

df = load_data("Most_Streamed_Spotify_Songs_2024_Cleaned_Median_Imputed.csv")

# ==========================================================
# 2. SIDEBAR FILTER
# ==========================================================
st.sidebar.title("🟢 Spotify Analytics")

# Filter Tahun
if "Year" in df.columns and not df["Year"].isnull().all():
    min_y = int(df["Year"].min())
    max_y = int(df["Year"].max())
    default_start = 2015 if min_y < 2015 else min_y
    
    year_range = st.sidebar.slider(
        "📅 Tahun Rilis",
        min_value=min_y,
        max_value=max_y,
        value=(default_start, max_y)
    )
    df_filtered = df[df["Year"].between(year_range[0], year_range[1])]
else:
    df_filtered = df.copy()

# Filter Explicit
explicit_filter = st.sidebar.radio(
    "🔞 Tipe Konten", ["Semua", "Hanya Explicit", "Non-Explicit"]
)
if explicit_filter == "Hanya Explicit":
    df_filtered = df_filtered[df_filtered["Explicit"] == True]
elif explicit_filter == "Non-Explicit":
    df_filtered = df_filtered[df_filtered["Explicit"] == False]

top_n = st.sidebar.number_input("🏆 Top Ranking", 5, 50, 10)

st.sidebar.markdown("---")
st.sidebar.caption("Data: Lagu duplikat telah digabungkan (Merged) menjadi satu entitas.")

# ==========================================================
# 3. KPI METRICS
# ==========================================================
st.title("🎧 Analisis Lengkap Lagu Top Spotify")

total_streams = df_filtered["Spotify Streams"].sum()
total_reach = df_filtered["Spotify Playlist Reach"].sum()
avg_pop = df_filtered["Spotify Popularity"].mean()

if not df_filtered.empty:
    top_track = df_filtered.loc[df_filtered["Spotify Streams"].idxmax()]
    top_name = top_track["Track"]
else:
    top_name = "-"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Spotify Streams", f"{total_streams/1e9:.2f} B")
col2.metric("Total Playlist Reach", f"{total_reach/1e9:.2f} B")
col3.metric("Avg Popularity", f"{avg_pop:.0f}/100")
col4.metric("👑 Lagu #1", top_name)

st.markdown("---")

# ==========================================================
# 4. CHART SECTION
# ==========================================================
tab1, tab2, tab3 = st.tabs(["📊 Top Charts", "📅 Tren & Waktu", "💡 Insight Konten"])

# --- TAB 1: LEADERBOARD ---
with tab1:
    c1, c2 = st.columns(2)
    
    # CHART 1: TOP SONGS
    with c1:
        st.subheader(f"1️⃣ Top {top_n} Lagu (Streams)")
        df_songs = df_filtered.nlargest(top_n, "Spotify Streams").copy()
        
        df_songs["Val_B"] = df_songs["Spotify Streams"] / 1e9
        df_songs["Text_B"] = df_songs["Val_B"].apply(lambda x: f"{x:.2f}B")
        
        fig1 = px.bar(
            df_songs, y="SongLabel", x="Val_B", orientation='h',
            text="Text_B", color_discrete_sequence=[COLOR_SPOTIFY]
        )
        fig1.update_traces(textposition='outside')
        
        # PERBAIKAN: Menambahkan Title X-Axis yang Jelas
        fig1.update_layout(
            yaxis={'title': '', 'categoryorder':'total ascending'}, 
            xaxis={'showticklabels': False, 'title': 'Total Streams (Billions)'}, # Title Jelas
            margin=dict(r=50)
        )
        st.plotly_chart(fig1, use_container_width=True)
        
    # CHART 2: TOP ARTISTS
    with c2:
        st.subheader(f"2️⃣ Top {top_n} Artis (Total Streams)")
        df_art = df_filtered.groupby("Artist")["Spotify Streams"].sum().nlargest(top_n).reset_index()
        
        df_art["Val_B"] = df_art["Spotify Streams"] / 1e9
        df_art["Text_B"] = df_art["Val_B"].apply(lambda x: f"{x:.2f}B")
        
        fig2 = px.bar(
            df_art, y="Artist", x="Val_B", orientation='h',
            text="Text_B", color_discrete_sequence=[COLOR_SPOTIFY]
        )
        fig2.update_traces(textposition='outside')
        
        # PERBAIKAN: Menambahkan Title X-Axis yang Jelas
        fig2.update_layout(
            yaxis={'title': '', 'categoryorder':'total ascending'}, 
            xaxis={'showticklabels': False, 'title': 'Total Streams (Billions)'}, # Title Jelas
            margin=dict(r=50)
        )
        st.plotly_chart(fig2, use_container_width=True)

# --- TAB 2: TIME SERIES ---
with tab2:
    st.subheader("3️⃣ Evolusi Popularitas & Streams")
    
    df_trend = df_filtered.groupby("Year").agg({
        "Spotify Streams": "mean",
        "Spotify Popularity": "mean",
        "Track": "count"
    }).reset_index()

    c3, c4 = st.columns(2)
    
    with c3:
        fig3 = px.line(
            df_trend, x="Year", y="Spotify Popularity",
            markers=True, title="Rata-rata Popularitas per Tahun Rilis"
        )
        fig3.update_traces(line_color=COLOR_ACCENT, line_width=4)
        fig3.update_layout(
            yaxis=dict(range=[0, 100], title="Avg Popularity"), 
            xaxis_title="Tahun Rilis",
            hovermode="x unified"
        )
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        fig4 = px.bar(
            df_trend, x="Year", y="Track",
            title="Jumlah Lagu Top yang Rilis per Tahun",
            color_discrete_sequence=[COLOR_SPOTIFY]
        )
        fig4.update_layout(xaxis_title="Tahun Rilis", yaxis_title="Jumlah Lagu")
        st.plotly_chart(fig4, use_container_width=True)
        
    st.markdown("---")
    
    st.subheader("4️⃣ Bulan Favorit Rilis Lagu")
    if "Month" in df_filtered.columns:
        month_order = [
            'January', 'February', 'March', 'April', 'May', 'June', 
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        existing_months = df_filtered["Month"].dropna().unique()
        month_order_exist = [m for m in month_order if m in existing_months]
        
        df_month = df_filtered["Month"].value_counts().reindex(month_order_exist).reset_index()
        df_month.columns = ["Bulan", "Jumlah Lagu"]
        
        fig5 = px.bar(
            df_month, x="Bulan", y="Jumlah Lagu",
            color="Jumlah Lagu", color_continuous_scale="Greens"
        )
        fig5.update_layout(xaxis_title="Bulan", yaxis_title="Jumlah Lagu")
        st.plotly_chart(fig5, use_container_width=True)

# --- TAB 3: CONTENT & CONTEXT ---
with tab3:
    c5, c6 = st.columns(2)
    
    with c5:
        st.subheader("5️⃣ Performa Lagu Explicit")
        df_exp = df_filtered.groupby("Explicit")["Spotify Streams"].mean().reset_index()
        df_exp["Tipe"] = df_exp["Explicit"].map({True: "Explicit (18+)", False: "Non-Explicit"})
        
        fig6 = px.pie(
            df_exp, names="Tipe", values="Spotify Streams",
            title="Rata-rata Streams: Explicit vs Clean",
            color="Tipe",
            color_discrete_map={"Explicit (18+)": COLOR_ACCENT, "Non-Explicit": COLOR_SPOTIFY},
            hole=0.4
        )
        st.plotly_chart(fig6, use_container_width=True)
        
    with c6:
        st.subheader("6️⃣ Dampak Playlist Reach")
        fig7 = px.scatter(
            df_filtered, x="Spotify Playlist Reach", y="Spotify Streams",
            color="Spotify Popularity", size="Spotify Popularity",
            hover_name="SongLabel",
            log_x=True, log_y=True,
            title="Korelasi Reach vs Streams (Log Scale)",
            color_continuous_scale="Greens"
        )
        fig7.update_layout(xaxis_title="Playlist Reach (Log)", yaxis_title="Streams (Log)")
        st.plotly_chart(fig7, use_container_width=True)

    st.markdown("---")
    
    st.subheader("7️⃣ Konteks Platform Lain (Top 10 Songs)")
    
    df_compare = df_filtered.nlargest(10, "Spotify Streams")
    cols = ["SongLabel", "Spotify Streams", "YouTube Views", "TikTok Views"]
    existing_cols = [c for c in cols if c in df_filtered.columns]
    
    df_melt = df_compare[existing_cols].melt("SongLabel", var_name="Platform", value_name="Views")
    
    fig8 = px.bar(
        df_melt, x="SongLabel", y="Views", color="Platform",
        barmode="group",
        color_discrete_map={
            "Spotify Streams": COLOR_SPOTIFY,
            "YouTube Views": COLOR_YOUTUBE,
            "TikTok Views": COLOR_TIKTOK
        }
    )
    fig8.update_layout(yaxis_type="log", xaxis_title="", yaxis_title="Views (Log Scale)")
    st.plotly_chart(fig8, use_container_width=True)

# ==========================================================
# 5. DATA TABLE
with st.expander("📂 Lihat Data Detail"):
    st.dataframe(
        df_filtered
        .sort_values("Spotify Streams", ascending=False)
        .style.format({
            "Spotify Streams": "{:,.0f}",
            "YouTube Views": "{:,.0f}",
            "TikTok Views": "{:,.0f}",
            "Spotify Popularity": "{:.1f}"
        })
    )