
#!/usr/bin/env python3
"""
Spotify Export -> Clean CSV + Analytics (CSV-only version)
- Scans a folder (or zip extracted folder) for Spotify streaming history JSONs.
- Normalizes to a canonical CSV: data/processed/streaming_history_clean.csv
- Writes analytics to data/analytics/ (top artists/tracks, listening minutes per day).
Usage:
  python src/process_spotify_data.py --input data/raw
  # If your JSONs are elsewhere:
  python src/process_spotify_data.py --input /path/to/unzipped_export
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def find_history_jsons(root: Path):
    cand = []
    for p in root.rglob("*.json"):
        name = p.name.lower()
        if any(k in name for k in ["endsong","streaminghistory","streaming_history","audio"]):
            cand.append(p)
    return sorted(cand)

def parse_endsong(obj: dict) -> dict:
    ts = obj.get("ts")
    ms = obj.get("ms_played", obj.get("msPlayed", 0))
    track = obj.get("master_metadata_track_name") or obj.get("trackName") or obj.get("track") or obj.get("title")
    artist = obj.get("master_metadata_album_artist_name") or obj.get("artistName") or obj.get("artist")
    uri = obj.get("spotify_track_uri") or obj.get("spotifyTrackUri")
    return {"played_at": ts, "track": track or "", "artist": artist or "", "ms_played": ms, "spotify_uri": uri, "source": "endsong"}

def parse_streaming_history(obj: dict) -> dict:
    ts_end = obj.get("endTime")
    if ts_end and isinstance(ts_end, str) and len(ts_end) == 16:  # "YYYY-MM-DD HH:MM"
        ts = ts_end.replace(" ", "T") + ":00Z"
    else:
        ts = ts_end
    ms = obj.get("msPlayed", obj.get("ms_played", 0))
    return {"played_at": ts, "track": (obj.get("trackName") or obj.get("master_metadata_track_name") or ""),
            "artist": (obj.get("artistName") or obj.get("master_metadata_album_artist_name") or ""),
            "ms_played": ms, "spotify_uri": obj.get("spotifyTrackUri") or obj.get("spotify_track_uri"),
            "source": "streaming_history"}

def load_rows(json_files):
    rows = []
    for jp in json_files:
        try:
            data = json.loads(Path(jp).read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if "plays" in data and isinstance(data["plays"], list):
                    data = data["plays"]
                else:
                    data = [data]
            for obj in data:
                if not isinstance(obj, dict): 
                    continue
                name = jp.name.lower()
                if "endsong" in name or "audio" in name:
                    rows.append(parse_endsong(obj))
                else:
                    rows.append(parse_streaming_history(obj))
        except Exception:
            continue
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, default="data/raw", help="Folder containing unzipped Spotify export JSONs")
    args = ap.parse_args()
    input_root = Path(args.input)
    input_root.mkdir(parents=True, exist_ok=True)

    out_proc = Path("data/processed"); out_proc.mkdir(parents=True, exist_ok=True)
    out_an = Path("data/analytics"); out_an.mkdir(parents=True, exist_ok=True)

    json_files = find_history_jsons(input_root)
    rows = load_rows(json_files)
    df = pd.DataFrame(rows)

    if df.empty:
        print("No streaming history JSON files found. Put your unzipped export under", input_root)
        return 0

    df = df.dropna(subset=["played_at"])
    df["played_at"] = pd.to_datetime(df["played_at"], utc=True, errors="coerce")
    df = df.dropna(subset=["played_at"])
    for col in ["track","artist"]:
        if col not in df.columns: df[col] = ""
        df[col] = df[col].fillna("")
    df["ms_played"] = pd.to_numeric(df["ms_played"], errors="coerce").fillna(0).astype("int64")
    df["date"] = df["played_at"].dt.date

    # Save canonical clean CSV
    clean_csv = out_proc / "streaming_history_clean.csv"
    df.to_csv(clean_csv, index=False)

    # Analytics
    daily = df.groupby("date", dropna=True)["ms_played"].sum().reset_index()
    daily["minutes"] = daily["ms_played"] / 60000.0
    daily = daily.drop(columns=["ms_played"]).sort_values("date")
    daily.to_csv(out_an / "listening_minutes_by_day.csv", index=False)

    top_artists = (df.groupby("artist", dropna=True)["ms_played"].agg(["sum","count"]).reset_index()
                     .rename(columns={"sum":"ms_played","count":"plays"}))
    top_artists["minutes"] = top_artists["ms_played"] / 60000.0
    top_artists = top_artists.sort_values("minutes", ascending=False)[["artist","minutes","plays"]]
    top_artists.to_csv(out_an / "top_artists.csv", index=False)

    top_tracks = (df.groupby(["track","artist"], dropna=True)["ms_played"].agg(["sum","count"]).reset_index()
                   .rename(columns={"sum":"ms_played","count":"plays"}))
    top_tracks["minutes"] = top_tracks["ms_played"] / 60000.0
    top_tracks = top_tracks.sort_values("minutes", ascending=False)[["track","artist","minutes","plays"]]
    top_tracks.to_csv(out_an / "top_tracks.csv", index=False)

    # Plot a simple daily minutes chart
    if not daily.empty:
        plt.figure()
        plt.plot(pd.to_datetime(daily["date"]), daily["minutes"])
        plt.title("Listening Minutes by Day")
        plt.xlabel("Date")
        plt.ylabel("Minutes")
        plt.tight_layout()
        plt.savefig(out_an / "daily_minutes.png")

    print("Wrote:", clean_csv, "and analytics to", out_an)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
