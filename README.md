# Neon Japan Route

Personal Google Maps trip planner. The app is public; the itinerary lives in a private repo and syncs between devices through GitHub.

**App:** https://bigplayzinc.github.io/BigPlaysTravels/

## How it works
- The plan is `plan.json` in a private repo (`bigplayzinc/japan-plan`). Each device reads and saves it through the GitHub API, so every edit is a commit there.
- Undo: ⋯ → **Version history** opens the file's history on GitHub; restore any older version from there.
- Each device keeps its last copy, so the itinerary opens without signal. Edits made offline are saved when you're back online. If the plan changed elsewhere in the meantime, the app asks which version to keep.
- The Google Maps key is stored in the same private repo (`config.json`), so you enter it once.

## First device (once)
1. Create a fine-grained token: https://github.com/settings/personal-access-tokens/new
   - Expiration: a date after the trip
   - Repository access: **Only select repositories** → `bigplayzinc/japan-plan`
   - Repository permissions → **Contents: Read and write**
2. Open the app, paste the token, keep the repo as `bigplayzinc/japan-plan`, tap **Connect**.
3. Tap **Add Google Maps key** and paste your key. Its website restrictions must include `https://bigplayzinc.github.io/*` (and `http://localhost:8000/*` for local use), with Maps JavaScript API, Places API (New) and Routes API enabled.

## Other devices
On a connected device: ⋯ → **Connect another device** shows a QR code and a pairing code.
- **iPhone:** open the app link in Safari → Share → **Add to Home Screen**. Open it from the Home Screen, tap **Scan pairing QR** and point the camera at the QR code.
- **Surface / other PC:** open the app in Edge (⋯ → Apps → Install this site as an app, if you like) and paste the pairing code, or scan the QR.

The pairing code contains the token: anyone who has it can read and edit the plan. If a device is lost, delete the token on GitHub (Settings → Developer settings → Personal access tokens), create a new one and connect again.

## Run locally
```
python -m http.server 8000
```
Open http://localhost:8000/. To test sync without a real token, see `dev/mock_github.py`.

## Files
- `index.html` – the app
- `sw.js`, `manifest.webmanifest`, `icons/` – offline support and Home Screen install
- `dev/mock_github.py` – fake GitHub API for local testing
- `CLAUDE.md` – notes for Claude Code
