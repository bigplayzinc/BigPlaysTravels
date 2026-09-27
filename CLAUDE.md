# CLAUDE.md — Neon Japan Route

Handover notes for Claude Code. Read this before changing anything.

## What this is
A personal, single-user trip planner for a Japan trip (Tokyo, Osaka, Kyoto, then Hakuba for snowboarding). It is a static web app on top of the Google Maps JavaScript API. No build step, no framework, no backend.

The user edits the plan in the app and navigates in Japan with the Google Maps phone app (via the app's "Open in Google Maps" / "Directions" links).

## Files
- `index.html` — the whole app: HTML, CSS and one inline `<script>` (vanilla JS, IIFE, `"use strict"`).
- `sw.js` — service worker: network-first for the app's own files (cached for offline), cache-first for fonts and the CDN QR libraries. Never caches GitHub or Google Maps requests. Bump `CACHE` when changing the shell file list.
- `manifest.webmanifest`, `icons/` — Home Screen / installed-app support (iPhone, Edge on the Surface).
- `dev/mock_github.py` — in-memory fake of the GitHub contents API for testing sync locally (see Running).
- `README.md` — user-facing setup steps.
- The itinerary (`plan.json`) is **not** in this repo. It lives in the private repo `bigplayzinc/japan-plan` (a local copy may exist here for testing; it's gitignored). Nothing personal (itinerary, dates, names, keys, tokens) may be committed to this public repo.

## Running
Needs an HTTP origin (Google key referrer restrictions, service worker). Opening the file via `file://` will not work.
```
python -m http.server 8000   # then http://localhost:8000/   (launch config "site")
python dev/mock_github.py      # fake GitHub API on :8787      (launch config "mock-github")
```
To test sync without the user's real token: in the page's console run `localStorage.setItem("njr-gh-api","http://localhost:8787")`, then connect with repo `test/japan-plan` and token `test-token`. The mock seeds from a local `plan.json` if present, and has helpers to simulate another device saving (`POST /__file/plan.json`) and going offline (`POST /__offline/1`). Clear `njr-gh-api` afterwards.

Hosting: GitHub Pages from the repo root (`main`, `/`) at `https://bigplayzinc.github.io/BigPlaysTravels/`. That origin must be in the Maps key's website restrictions (the user has added it, plus `http://localhost:8000/*`).

## Google APIs used (user's own key)
- **Maps JavaScript API** — loaded by injecting `https://maps.googleapis.com/maps/api/js?...&libraries=marker,geometry,places&loading=async&callback=__njrInit`.
- **Advanced Markers** (`AdvancedMarkerElement`) with `mapId` (default `DEMO_MAP_ID`) and `colorScheme: DARK`.
- **Places API (New)** — `Place.searchByText` for "Add place".
- **Routes API** — REST `POST https://routes.googleapis.com/directions/v2:computeRoutes` from the browser with `X-Goog-Api-Key` and a field mask. Polylines decoded with `google.maps.geometry.encoding.decodePath`.

The Maps key and Map ID are entered in the app (⋯ → Google Maps key) and saved to `config.json` in the private plan repo, so every connected device picks them up; each device also keeps a copy in `localStorage`. **Never commit a key to this repo.**

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
      ],
      "maybe": [ { "name": "…", "cat": "…", "lat": 0, "lng": 0, "note": "…" } ] }   // optional: parked on this day, no time
  ],
  "ideas": [ { "name": "…", "cat": "anime", "lat": 0, "lng": 0, "note": "…" } ]
}
```
- Categories (`cat`): `anime, gaming, theme, night, food, gamble, museum, temple, wild, event, transit, stay`.
- Cities with styling: `Tokyo, Osaka, Kyoto, Hakuba` (see `CITY`).
- Stops are always sorted by time within a day. Times before 05:00 sort after 23:59 (New Year's Eve after-party at 01:00).

## State, persistence and sync
The user edits on a desktop PC and in Japan uses a Surface Pro (Windows) and an iPhone; all three share one plan. Single user: no multi-user features.
- **Source of truth:** `plan.json` in the private repo `bigplayzinc/japan-plan`, read/written with the GitHub REST contents API (`GET`/`PUT /repos/{repo}/contents/plan.json`) using a fine-grained personal access token scoped to that repo (Contents: read and write). Every save is a commit ("Edit from iPhone" etc.), so the repo history is the undo (⋯ → Version history).
- `planText()` writes one stop / maybe / idea per line so commits diff cleanly (an empty `maybe` is omitted). Keep that format.
- **Per device (`localStorage`):** `njr-gh` ({repo, token, device name}), `njr-plan-v1` (last known plan, shown immediately and offline), `njr-sync` ({sha, dirty}), `njr-key`, `njr-mapid`, `njr-routes-v1` (route cache), `njr-gh-api` (API base override, testing only).
- **Sync loop:** `save()` stores locally, marks dirty and debounces `push()` (1.2 s). `push()` PUTs with the last seen sha; 409/422 means another device saved first → `pull()` → if this device is dirty and the texts differ, `conflict()` asks which version to keep. `pull()` runs on boot, when the app becomes visible, when back online and every 60 s (skipped while the user is typing). A read that returns a version this device replaced in the last 2 minutes is treated as a stale read, not a change.
- **Pairing:** ⋯ → Connect another device shows a QR code of `<app url>#pair=njr1.<base64url {r:repo,t:token}>` plus the code. The connect screen accepts a code or a token and can scan the QR with the camera (jsQR, loaded on demand). The `#pair` fragment is stripped from the URL on load. Scanning inside the app matters on iPhone: Home Screen apps don't share storage with Safari.
- If you change the plan's data model, handle existing plans in the repo rather than breaking them.

## UI concepts (keep these)
- Dark "neon" look: Chakra Petch (display), IBM Plex Sans (body), JetBrains Mono (data). Palette tokens in `:root`.
- **Colour = chronology.** Every stop gets a colour from one ramp over the whole trip (cyan → violet → pink → amber) by its position in the chronological sequence (`seq`). The same colour is used for the pin, list badge, day-chip bar and the route leg leaving that stop.
- Selected day: large numbered, draggable pins + routed legs. Other days: small dots. "All" view: dots + thin per-day lines.
- Clicking a pin or list row selects the stop everywhere (pin pulse, row highlight, floating card with prev/next). The card has ▾ minimise (to a one-line bar with ‹ › and tap-to-expand; also swipe down / up) and ✕ close. Minimised is remembered per device (`njr-cardmin`) so stepping through stops keeps the map clear.
- Three places for a thing: scheduled (`day.stops`, with a time), Maybe (`day.maybe`, parked on a day without a time) and Ideas (`plan.ideas`). Stop card → Maybe / → Ideas; Maybe card → Schedule / → Ideas; Idea card → Schedule on the viewed day / → Maybe. Maybe and idea cards share `renderIdeaCard` (`looseHome()` says where the item lives). Maybe items of the selected day show as dashed cyan pins.
- Opening hours: `ensureHours()` looks a place up once with Places (by `placeId`, else a text search near its coordinates) and caches the periods in this device's localStorage (`njr-hours`), never in the plan, so lookups make no commits. Adding a stop moves its provisional time into the opening hours (`fitNewStop` → `suggestTime`: a free half-hour slot nearest the wanted time, 45 min from other stops). The edit form checks live and offers "Use HH:MM"; cards and list rows flag "closed?" / "closing"; the day header has "Check opening hours". Stay / transit stops are skipped. Google's regular hours don't know event-only dates or New Year closures; notes carry those.
- Ideas (unscheduled): tapping one in the list or on the map opens an idea card (`idea` holds the object; ideas have no ids), pans there and shows a highlighted amber pin even when "Show ideas on the map" is off. The card edits name / category / notes and can delete the idea or add it to the selected day. List rows show the first line of the notes; the list's open state survives re-renders (`ideasOpen`). Arrow keys step through the trip. Top slider scrubs the whole trip in order; "Play day/trip" auto-steps.
- Desktop: left panel 400px + map. ≤ 820px (phones): map on top, panel below, split set by `--maph` on `.app`. A grip (and the panel header) drags the split and snaps to full list (0), split (42%) or big map (70%); tapping the grip toggles the full list; tapping a stop in full-list mode brings the map back. The split is remembered per device (`njr-split`). Day header and stops scroll together in `.pbody`. Grid columns use `minmax(0,1fr)` so the day-chip row can't widen the page. iPhone safe areas are padded on `.app`; inputs are 16px on touch screens so iOS doesn't zoom in.
- My location: the locate button (map toolbar) starts `watchPosition`, draws a pulsing dot plus an accuracy circle and centres on it; watching stops while the app is in the background. The stop card shows the distance from you and a "Directions from here" link (a Google Maps URL with no origin, so the Maps app routes from the phone's position).

## Main code landmarks (in `index.html`)
`rebuildSeq` (chronology + colours) · `legRoute` / `routesApi` (routing + cache) · `ghFetch` / `ghGet` / `ghPut` / `planText` (GitHub storage) · `save` / `push` / `pull` / `adopt` / `conflict` (sync) · `showConnect` / `connect` / `showPair` (pairing) · `showKey` / `loadConfig` (Maps key) · `renderMap` / `drawLines` / `applySel` · `renderPanel` / `renderCard` · `addStopAt` · `doSearch` / `guessCat` · menu handlers (export, import, KML for Google My Maps).

## Working with the user
- The user is an engineer and codes; be direct, flag trade-offs honestly.
- Test in a real browser with their key before calling something done; the Maps parts can't be verified without a key.
- Keep it a no-build static app unless they ask otherwise.
