# Neon Japan Route

Personal Google Maps trip planner for a Japan trip. The itinerary itself lives in a private repo.

## Run locally
```
python3 -m http.server 8000
```
Open http://localhost:8000/ and paste your Google Maps API key on the setup screen. The key is stored only in your browser.

## Google Cloud setup (once)
1. Enable **Maps JavaScript API**, **Places API (New)** and **Routes API** in your project (billing must be linked).
2. Credentials → API key → restrict it to those three APIs and to these websites:
   - `http://localhost:8000/*`
   - `http://127.0.0.1:8000/*`
   - `https://<your-github-username>.github.io/*`

## Host on GitHub Pages
Repo → **Settings → Pages** → Source: *Deploy from a branch* → `main` / `/ (root)` → Save.
The app appears at `https://<username>.github.io/<repo>/` after a minute.

Your edits are stored per web address. When moving from localhost to the Pages URL (or to your phone), use **⋯ → Export plan** and **Import plan**.

## Files
- `index.html` – the app
- `plan.json` – the itinerary (private repo, not committed here)
- `CLAUDE.md` – notes for Claude Code
