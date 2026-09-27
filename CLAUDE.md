# CLAUDE.md — Neon Japan Route

Handover notes for Claude Code. Read this before changing anything.

## What this is
A personal, single-user trip planner for a Japan trip (Tokyo, Osaka, Kyoto, then Hakuba for snowboarding). It is a static web app on top of the Google Maps JavaScript API. No build step, no framework, no backend.

The user edits the plan in the app and navigates in Japan with the Google Maps phone app (via the app's "Open in Google Maps" / "Directions" links).

## Files
- `index.html` — the whole app: HTML, CSS and one inline `<script>` (vanilla JS, IIFE, `"use strict"`).
- `plan.json` — the itinerary. **Private: it lives in the private repo `bigplayzinc/japan-plan`, never in this public repo** (gitignored here). The current code still loads a local `plan.json` with `fetch("plan.json")` at boot; see "In progress" below.
- `README.md` — user-facing setup and hosting steps.

## Running
Needs an HTTP origin (Google key referrer restrictions + `fetch` of plan.json). Opening the file via `file://` will not work.
```
python3 -m http.server 8000   # then http://localhost:8000/
```
Hosting target: GitHub Pages from the repo root (`main` branch, `/` folder). The Pages URL must be added to the API key's website restrictions in Google Cloud.

## Google APIs used (user's own key)
- **Maps JavaScript API** — loaded by injecting `https://maps.googleapis.com/maps/api/js?...&libraries=marker,geometry,places&loading=async&callback=__njrInit`.
- **Advanced Markers** (`AdvancedMarkerElement`) with `mapId` (default `DEMO_MAP_ID`) and `colorScheme: DARK`.
- **Places API (New)** — `Place.searchByText` for "Add place".
- **Routes API** — REST `POST https://routes.googleapis.com/directions/v2:computeRoutes` from the browser with `X-Goog-Api-Key` and a field mask. Polylines decoded with `google.maps.geometry.encoding.decodePath`.

The API key and Map ID are entered in the in-app setup screen and stored in `localStorage` only. **Never commit a key.**

### Known limitation: transit in Japan
Google's developer APIs generally return no TRANSIT routes in Japan (the Maps app has them; the API doesn't). The app therefore:
- asks Routes API for `WALK` when a leg is ≤ 1.5 km,
- tries `TRANSIT`, then falls back to `WALK` if ≤ 3 km, else draws a dashed straight line,
- treats legs > 100 km as long-distance rail with a rough time estimate (no API call),
- always offers a Google Maps deep link (`/maps/dir/?api=1&...&travelmode=transit`) for real train times.
Results (including "no route") are cached in `localStorage` (`njr-routes-v1`) keyed by rounded coordinates to limit billable calls. If adding real Japanese transit data, the realistic options are the paid NAVITIME route API or ODPT open data; neither is integrated.

## Data model (`plan.json`)
```jsonc
{
  "version": 1,
  "trip": "Japan trip",
  "days": [
    { "date": "YYYY-MM-DD", "city": "Tokyo", "title": "…", "note": "…",
      "stops": [
        { "id": "a1", "time": "16:00", "name": "…", "cat": "stay",
          "lat": 35.6938, "lng": 139.7034, "note": "…",
          "booked": false,        // optional: false = needs booking, true = booked, absent = n/a
          "placeId": "…",         // optional: Google place id (set when added via search)
          "q": "…" }              // optional: custom Google Maps search text
      ] }
  ],
  "ideas": [ { "name": "…", "cat": "anime", "lat": 0, "lng": 0, "note": "…" } ]
}
```
- Categories (`cat`): `anime, gaming, theme, night, food, gamble, museum, temple, event, transit, stay`.
- Cities with styling: `Tokyo, Osaka, Kyoto, Hakuba` (see `CITY`).
- Stops are always sorted by time within a day. Times before 05:00 sort after 23:59 (New Year's Eve after-party at 01:00).

## State and persistence
- `localStorage` keys: `njr-plan-v1` (the user's edited plan), `njr-key`, `njr-mapid`, `njr-routes-v1`.
- On boot: if `njr-plan-v1` exists it wins over `plan.json`. So **editing `plan.json` does not change what the user sees** unless they reset (menu → "Reset to the original plan") or import. If you change the data model, add a migration for stored plans rather than breaking them.
- Export/Import of the whole plan as JSON in the ⋯ menu is how the user moves the plan between laptop and phone. They use it alone; multi-user sync was explicitly not wanted (for now).

## UI concepts (keep these)
- Dark "neon" look: Chakra Petch (display), IBM Plex Sans (body), JetBrains Mono (data). Palette tokens in `:root`.
- **Colour = chronology.** Every stop gets a colour from one ramp over the whole trip (cyan → violet → pink → amber) by its position in the chronological sequence (`seq`). The same colour is used for the pin, list badge, day-chip bar and the route leg leaving that stop.
- Selected day: large numbered, draggable pins + routed legs. Other days: small dots. "All" view: dots + thin per-day lines.
- Clicking a pin or list row selects the stop everywhere (pin pulse, row highlight, floating card with prev/next). Arrow keys step through the trip. Top slider scrubs the whole trip in order; "Play day/trip" auto-steps.
- Desktop: left panel 400px + map. ≤ 820px: map on top, panel below.

## Main code landmarks (in `index.html`)
`rebuildSeq` (chronology + colours) · `legRoute` / `routesApi` (routing + cache) · `renderMap` / `drawLines` / `applySel` · `renderPanel` / `renderCard` · `addStopAt` · `doSearch` / `guessCat` · menu handlers (export, import, KML for Google My Maps, reset, key).

## Working with the user
- The user is an engineer and codes; be direct, flag trade-offs honestly.
- Test in a real browser with their key before calling something done; the Maps parts can't be verified without a key.
- Keep it a no-build static app unless they ask otherwise.

## In progress: private sync across devices
The user edits on a desktop PC, and in Japan uses a Surface Pro (Windows) and an iPhone. Decided design:
- This repo stays **public** and holds only app code, hosted on GitHub Pages (`https://bigplayzinc.github.io/BigPlaysTravels/`). No itinerary, dates or personal details may be committed here.
- The plan lives in the **private** repo `bigplayzinc/japan-plan` (`plan.json`, later `config.json` with the Maps key). Each device reads and writes it through the GitHub REST contents API with a fine-grained personal access token scoped to that one repo (Contents: read and write). Every save is a commit, so history doubles as undo.
- Offline: cache the last plan locally and queue edits; installable (manifest + service worker + icons) for iPhone Home Screen and Edge on the Surface.
