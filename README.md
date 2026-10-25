# CivicFix — Genesis hackathon

A community issue reporting MVP: GPS reports, shared SQLite persistence, photos, duplicate checks, statuses and optional AI photo classification.

## Run

```bash
cd civicfix
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend:app --reload --host 127.0.0.1 --port 8000
```

Open **http://localhost:8000**. Use the same server for the API and UI. For optional AI image classification:

```bash
pip install -r requirements-ai.txt
```

The first classification downloads the CLIP model from Hugging Face (requires internet and may take time). This is a zero-shot image classifier, not a model trained on municipal infrastructure; verify its suggestions. Manual selection works without AI.

## Demo flow

1. Open **Report an Issue**, attach a photo, and optionally click **Suggest with AI**.
2. Select or correct the category, describe the issue, and click **GPS** (or enter location text).
3. Submit, then inspect **All Reports** and **City Overview**. Duplicate checks apply when GPS is available.
4. Open a second browser tab: reports are shared through SQLite rather than localStorage.

## Notes

- No login: anyone can change statuses. This is a **hackathon demo**, not a production municipal system.
- Do not publicly deploy without authentication, moderation, rate limiting, CSRF/security review, and a privacy/retention policy.
- GPS works on localhost or HTTPS, subject to browser permission. Without GPS, textual locations do not create map pins.
- No automatic connection to municipal authorities; resolution statuses are demo controls.
- The map uses Leaflet and OpenStreetMap tiles (requires internet).
- Photos are limited to 5 MB and stored in SQLite. Avoid uploading personal/sensitive images.
