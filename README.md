# ✈️ AI Trip Planner
### Full Stack Multi-Agent Travel App — Zero API Costs. Runs 100% Locally.

---

## 📁 Folder Structure

```
ai-trip-planner/
│
├── frontend/
│   ├── index.html           ← Home / Landing page
│   ├── suggestions.html     ← Browse destinations with live weather
│   ├── planner.html         ← Trip input form (live geocoding + map)
│   ├── itinerary.html       ← Live streaming AI itinerary output
│   ├── dashboard.html       ← Saved trips (localStorage)
│   └── about.html           ← How it works, tech stack
│
└── backend/
    ├── main.py              ← FastAPI server (health + SSE /stream)
    ├── requirements.txt     ← Python dependencies
    ├── .env                 ← No keys needed
    ├── agents/
    │   ├── weather_agent.py     ← Open-Meteo live weather
    │   ├── attraction_agent.py  ← Overpass API live attractions
    │   ├── hotel_agent.py       ← Overpass API live hotels
    │   └── itinerary_agent.py   ← Ollama local LLM (streaming)
    └── utils/
        ├── geo.py           ← Nominatim geocoding
        └── weather.py       ← Open-Meteo weather fetch
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- A modern browser (Chrome, Firefox, Edge)
- VS Code with "Live Server" extension *(recommended)*

---

### Step 1 — Install Ollama

```bash
# Linux / Mac
curl -fsSL https://ollama.com/install.sh | sh

# Windows — download from:
# https://ollama.com/download
```

### Step 2 — Pull the AI Model

```bash
ollama signin
ollama run gpt-oss:20b-cloud

# To stop Ollama on Windows:
taskkill /F /IM "ollama app.exe" /T; taskkill /F /IM "ollama.exe" /T
```

### Step 3 — Start Ollama

```bash
ollama serve
# Keep this terminal open!
```

### Step 4 — Setup the Backend

```bash
cd backend

python -m venv venv
.\venv\Scripts\activate

# If you get an execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

uvicorn main:app --reload --port 8000
# You should see: INFO: Uvicorn running on http://127.0.0.1:8000
```

### Step 5 — Open the Frontend

**Option A — VS Code Live Server (recommended)**
1. Open the `ai-trip-planner/` folder in VS Code
2. Right-click `frontend/index.html`
3. Click **Open with Live Server**

**Option B — Direct file open**
Double-click `frontend/index.html` in your file explorer.

---

## 🧠 Live Data Sources

| Source | What it provides | API Key | Cost |
|---|---|---|---|
| Open-Meteo | Real-time weather + 5-day forecast | ❌ None | Free |
| Nominatim (OSM) | Geocoding any city/destination | ❌ None | Free |
| Overpass API (OSM) | Live attractions, parks, hotels | ❌ None | Free |
| Ollama | AI itinerary generation (streaming) | ❌ None | Free |

> **Total monthly cost: ₹0**

---

## 🔌 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Check if backend is running |
| `GET /stream` | SSE stream — see params below |

**Stream query parameters:**

| Parameter | Default | Example |
|---|---|---|
| `destination` | *(required)* | `Bali, Indonesia` |
| `days` | `5` | `7` |
| `budget` | `Mid-range` | `Budget` / `Luxury` |
| `transport` | `Mix` | `Public` / `Taxi/Ride` / `Walking` |
| `interests` | — | `Food,History,Nature` |
| `travelers` | `1` | `2` |
| `requirements` | — | `wheelchair accessible` |

---

## 🔄 How the App Flows

```
index.html
  └→ planner.html         (form + live geocoding via Nominatim)
       └→ itinerary.html  (SSE stream from backend)
            └→ /stream endpoint
                 ├→ weather_agent.py     (Open-Meteo)    ─┐
                 ├→ attraction_agent.py  (Overpass/OSM)   ├─ parallel
                 └→ hotel_agent.py       (Overpass/OSM)  ─┘
                      └→ itinerary_agent.py  (Ollama LLM, streamed)

suggestions.html  →  Weather button  →  Open-Meteo (called from browser)
dashboard.html    →  Reads saved trips from localStorage
about.html        →  Static info page
```

---

## ⚙️ AI Model

This app uses **`gpt-oss:20b-cloud`** — a 20B cloud-routed model via Ollama.

```python
# backend/agents/itinerary_agent.py — line 12
MODEL = "gpt-oss:20b-cloud"
```

To switch to a different model, replace that value and run `ollama pull <model>`:

| Model | Notes |
|---|---|
| `gpt-oss:20b-cloud` | ✅ Currently used — best quality |
| `mistral` | Faster, lighter |
| `gemma3` | Lightest, good for low-RAM machines |
| `llama3.1:70b` | Highest quality *(needs ~48 GB RAM)* |
| `phi3` | Compact Microsoft model |

---

## 📱 Pages Overview

| Page | File | Description |
|---|---|---|
| Home | `index.html` | Landing page with search bar |
| Suggestions | `suggestions.html` | Browse 12 destinations with live weather |
| Planner | `planner.html` | Full form with live geocoding + map preview |
| Itinerary | `itinerary.html` | Streaming AI output with sidebar map |
| Dashboard | `dashboard.html` | Saved trips from localStorage |
| About | `about.html` | How it works, tech stack, booking links |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| "Backend not reachable" | Run `uvicorn main:app --reload --port 8000` inside `backend/` |
| "Cannot connect to Ollama" | Run `ollama serve` and keep that terminal open |
| "Model not found" | Run `ollama pull llama3` |
| Map not loading | Check internet connection (Leaflet + OSM require internet) |
| Weather not loading | Check internet connection (Open-Meteo requires internet) |
| Slow itinerary | Normal for CPU inference — switch to `mistral` or `gemma3` for speed |