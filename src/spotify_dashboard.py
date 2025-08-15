
# spotify_dashboard.py
# Streamlit dashboard for Spotify Data Analytics
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title="Spotify Data Dashboard", page_icon="🎵", layout="wide")

st.title("🎵 Spotify Data Dashboard")
st.write("Interactive analytics for your Spotify listening. Load your cleaned CSV or point to `data/processed/streaming_history_clean.csv`.")

# --- Data loading helpers ---
def load_clean_df(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Basic cleanup
    df['played_at'] = pd.to_datetime(df['played_at'], utc=True, errors='coerce')
    df = df.dropna(subset=['played_at'])
    df['date'] = pd.to_datetime(df['played_at'].dt.date)
    df['ms_played'] = pd.to_numeric(df['ms_played'], errors='coerce').fillna(0).astype('int64')
    # Normalize empty strings
    for c in ['track','artist']:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].fillna("")
    return df

# Sidebar: data source
st.sidebar.header("Data Source")
default_path = Path("data/processed/streaming_history_clean.csv")
use_uploaded = st.sidebar.checkbox("Upload CSV instead of using local file", value=False)

df = None
if use_uploaded:
    up = st.sidebar.file_uploader("Upload streaming_history_clean.csv", type=["csv"])
    if up is not None:
        df = pd.read_csv(up)
        # perform same transforms as loader
        df['played_at'] = pd.to_datetime(df['played_at'], utc=True, errors='coerce')
        df = df.dropna(subset=['played_at'])
        df['date'] = pd.to_datetime(df['played_at'].dt.date)
        df['ms_played'] = pd.to_numeric(df['ms_played'], errors='coerce').fillna(0).astype('int64')
        for c in ['track','artist']:
            if c not in df.columns:
                df[c] = ""
            df[c] = df[c].fillna("")
else:
    if default_path.exists():
        df = load_clean_df(default_path)
    else:
        st.warning(f"Couldn't find {default_path}. Upload a CSV in the sidebar or generate it via `python src/process_spotify_data.py --input data/raw`.")

if df is None or df.empty:
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")
min_date, max_date = df['date'].min(), df['date'].max()
date_range = st.sidebar.date_input("Date range", (min_date, max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range) == 2:
    df = df[(df['date'] >= pd.to_datetime(date_range[0])) & (df['date'] <= pd.to_datetime(date_range[1]))]

min_minutes = st.sidebar.slider("Minimum minutes per day for 'active' days (KPI)", min_value=0, max_value=240, value=10, step=5)
top_n = st.sidebar.slider("Top N artists/tracks", min_value=5, max_value=50, value=15, step=5)

# --- KPIs ---
total_minutes = df['ms_played'].sum() / 60000.0
total_plays = int(len(df))
active_days = (df.groupby('date')['ms_played'].sum() / 60000.0 >= min_minutes).sum()
unique_artists = df['artist'].nunique()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Minutes", f"{total_minutes:,.0f}")
kpi2.metric("Total Plays", f"{total_plays:,}")
kpi3.metric("Active Days", f"{active_days:,}")
kpi4.metric("Unique Artists", f"{unique_artists:,}")

# --- Daily minutes time series ---
daily = df.groupby('date', dropna=True)['ms_played'].sum().reset_index()
daily['minutes'] = daily['ms_played'] / 60000.0
daily = daily[['date','minutes']].sort_values('date')

st.subheader("Daily Listening Minutes")
fig1 = plt.figure()
plt.plot(daily['date'], daily['minutes'])
plt.title("Listening Minutes by Day")
plt.xlabel("Date")
plt.ylabel("Minutes")
plt.tight_layout()
st.pyplot(fig1)

# Rolling 7-day average
st.subheader("7-day Rolling Average")
rolling = daily.copy()
rolling['roll7'] = rolling['minutes'].rolling(window=7, min_periods=1).mean()
fig2 = plt.figure()
plt.plot(rolling['date'], rolling['roll7'])
plt.title("7-Day Rolling Average of Minutes")
plt.xlabel("Date")
plt.ylabel("Minutes (7-day avg)")
plt.tight_layout()
st.pyplot(fig2)

# --- Top artists/tracks ---
st.subheader("Top Artists by Minutes")
top_artists = (df.groupby('artist', dropna=True)['ms_played']
                 .sum()
                 .sort_values(ascending=False)
                 .head(top_n)
                 .reset_index())
top_artists['minutes'] = top_artists['ms_played'] / 60000.0

fig3 = plt.figure()
plt.barh(top_artists['artist'][::-1], top_artists['minutes'][::-1])
plt.title(f"Top {top_n} Artists by Minutes")
plt.xlabel("Minutes")
plt.ylabel("Artist")
plt.tight_layout()
st.pyplot(fig3)
st.dataframe(top_artists[['artist','minutes']])

st.subheader("Top Tracks by Minutes")
top_tracks = (df.groupby(['track','artist'], dropna=True)['ms_played']
               .sum()
               .sort_values(ascending=False)
               .head(top_n)
               .reset_index())
top_tracks['minutes'] = top_tracks['ms_played'] / 60000.0
labels = top_tracks.apply(lambda r: f"{r['track']} — {r['artist']}", axis=1)

fig4 = plt.figure()
plt.barh(labels[::-1], top_tracks['minutes'][::-1])
plt.title(f"Top {top_n} Tracks by Minutes")
plt.xlabel("Minutes")
plt.ylabel("Track — Artist")
plt.tight_layout()
st.pyplot(fig4)
st.dataframe(top_tracks[['track','artist','minutes']])

st.caption("Built by Yash + TARS 💥")
