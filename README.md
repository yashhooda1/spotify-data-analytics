# 🎵 Spotify Data Analytics

This project processes your personal Spotify listening history and generates insights like:

- **Top Artists** (total minutes listened & play counts)
- **Top Tracks** (total minutes listened & play counts)
- **Daily Listening Minutes** (trend over time)
- **Visualizations** (listening minutes by day)

All analysis is done **locally** — your data stays on your machine unless you choose to share it.

---

## 📂 Repository Structure

```
spotify-data-analytics/
├── data/
│   ├── raw/                  # Place your unzipped Spotify export JSONs here (ignored in git)
│   ├── processed/             # Clean processed CSV (streaming_history_clean.csv)
│   └── analytics/             # Output analytics CSVs & daily_minutes.png
├── src/
│   └── process_spotify_data.py  # Script to process Spotify export
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### 1️⃣ Request Your Data from Spotify
1. Go to [Spotify Privacy Settings](https://www.spotify.com/account/privacy/).
2. Under **Download your data**, request your **Account data**.
3. When you receive the email from Spotify, download and unzip the archive.

---

### 2️⃣ Install Dependencies
Make sure you have Python 3.x installed.

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Add Your Data
Place all JSON files from your unzipped export inside:
```
data/raw/
```

---

### 4️⃣ Run the Processing Script
```bash
python src/process_spotify_data.py --input data/raw
```

This will:
- Clean and unify the streaming history into `data/processed/streaming_history_clean.csv`
- Generate analytics:
  - `data/analytics/top_artists.csv`
  - `data/analytics/top_tracks.csv`
  - `data/analytics/listening_minutes_by_day.csv`
  - `data/analytics/daily_minutes.png` (visualization)

---

## 📊 Example Outputs

**Top Artists** (minutes listened & plays):
| artist         | minutes | plays |
|----------------|---------|-------|
| Artist A       | 1234.56 | 200   |
| Artist B       | 987.65  | 150   |

**Daily Listening Minutes Plot:**
![Daily Minutes](data/analytics/daily_minutes.png)

---

## 🔒 Privacy
This repo **does not** contain personal data by default.  
`data/raw/` is listed in `.gitignore` so your raw Spotify export isn’t committed.

---

## 🛠 Requirements
- Python 3.x
- `pandas`
- `matplotlib`

---

## 🔗 Live App & Badges

[![Python](https://img.shields.io/badge/Python-3.11-blue)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-app-red)](#)
![License](https://img.shields.io/badge/License-MIT-green)
![Last Commit](https://img.shields.io/github/last-commit/yashhooda1/spotify-data-analytics)
![Stars](https://img.shields.io/github/stars/yashhooda1/spotify-data-analytics?style=social)

> **Live dashboard (optional):** If you deploy to Streamlit Cloud, update this link:  
> **https://streamlit.io/cloud** → create an app, point to `src/spotify_dashboard.py`, then put your app URL here.

---

## 🖥️ Streamlit App (Local)

```bash
pip install -r requirements.txt
pip install -r requirements_streamlit.txt
streamlit run src/spotify_dashboard.py
```

- The app loads `data/processed/streaming_history_clean.csv` by default.  
- Or use the **Upload CSV** toggle in the sidebar to provide a file manually.

---

## 🤖 Auto-Refresh Analytics (GitHub Actions)

This workflow updates `data/processed/` and `data/analytics/` **whenever new files are pushed to `data/raw/`** (or when you trigger it manually).

### Add the workflow
Save this file as: `.github/workflows/analytics-refresh.yml`

```yaml
name: Refresh Spotify Analytics

on:
  push:
    paths:
      - 'data/raw/**'
      - 'src/process_spotify_data.py'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Process data
        run: |
          python src/process_spotify_data.py --input data/raw

      - name: Commit analytics (if changed)
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/processed data/analytics
          if git diff --cached --quiet; then
            echo "No changes to commit."
          else
            git commit -m "Auto-refresh analytics [skip ci]"
            git push
          fi
```

> **Note:** If you add extra Python deps later, ensure they are listed in `requirements.txt` so the workflow can install them.

---

## 📜 License
This project is open-source under the MIT License.  
Feel free to fork and adapt for your own Spotify analytics!
