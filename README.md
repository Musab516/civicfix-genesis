<div align="center">

# 🏙️ CivicFix

### Report issues. Empower communities. Build better cities.

**An AI-assisted civic issue reporting and management platform built for the Genesis Hackathon.**

[🌐 Live Demo](https://civicfix-genesis.onrender.com) · [🐛 Report an Issue](https://github.com/Musab516/civicfix-genesis/issues) · [💻 Source Code](https://github.com/Musab516/civicfix-genesis)

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?logo=javascript&logoColor=black)
![Render](https://img.shields.io/badge/Render-Deployment-000000)

</div>

---

## 🔑 Try the live demo

**[Open CivicFix](https://civicfix-genesis.onrender.com)** and sign in with this dedicated **citizen demo account**:

| Field | Demo credential |
| --- | --- |
| Email | `citizen1@pak.pk` |
| Password | `citizen123` |

Use this account to explore citizen reporting, AI category suggestions, the issue map and complaint tracking. This is a shared public demo account: **do not upload private photos, personal information or sensitive locations.** Administrator credentials are not published.

---

## The problem

Potholes, overflowing garbage, broken streetlights and damaged infrastructure affect everyday life. Reporting them can be slow, fragmented and difficult to track. Communities need a simple way to document issues, find existing reports and see whether something has been addressed.

## Our solution

**CivicFix** lets residents submit photo-based, location-aware reports and gives administrators a dashboard for reviewing, prioritizing and resolving them. Citizens can follow report statuses and support existing complaints instead of filing duplicates.

> **Genesis theme:** A new beginning for community-driven, transparent urban issue reporting.

## ✨ Features

| Feature | What it does |
| --- | --- |
| 📷 **Photo-based reports** | Attach a photo and description of a local infrastructure issue. |
| 🧠 **Free browser AI** | Suggest an issue category using a browser-side image model; no paid inference API required. |
| 📍 **Map & locations** | Use browser geolocation or manually enter decimal coordinates (`latitude, longitude`). |
| 🔎 **Duplicate detection** | Flag nearby existing reports to reduce repeated complaints. |
| 🙋 **Citizen accounts** | Register, log in and participate in the reporting workflow. |
| 🕵️ **Anonymous public reporting** | Public report views do not identify the account that submitted the report. |
| 👍 **Community upvotes** | Help indicate which existing issues affect more residents. |
| 🚦 **Prioritization** | Explainable, rule-based severity levels help sort reports by urgency. |
| 🛠️ **Admin management** | Authorized admins can manage report statuses and review issues. |
| 📸 **Resolution evidence** | Add repair photos so a resolved report has visible evidence. |
| 📊 **Analytics** | Track report categories, statuses, resolution progress and issue hotspots. |
| 📱 **Mobile-friendly UI** | Responsive reporting and dashboard layouts for phones and desktops. |

**Important:** The AI provides suggestions, not guaranteed classifications. Users should confirm or change the predicted category. Severity scoring is rule-based, not a separately trained prediction model.

## 🚀 Try the live app

**https://civicfix-genesis.onrender.com**

1. Register or log in.
2. Select **Report an Issue**, attach a photo and request an AI category suggestion.
3. Review the category, enter a description and set a location (GPS or decimal coordinates).
4. Submit and find your report on the map/dashboard.
5. Upvote existing reports and follow their status.

Administrators can additionally review priorities, change statuses, inspect analytics and upload resolution photos.

### Privacy note

Public reports are anonymous **with respect to the submitting account**, but attached images, descriptions and map locations are visible. Do not upload faces, addresses or other identifying details if privacy matters. Coordinates may reveal a precise location.

## 🧰 Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML, CSS, JavaScript |
| Mobile UI | Responsive CSS (`mobile.css`) |
| Image classification | Browser-side JavaScript model (`browser-ai.js`) |
| Map | Leaflet + OpenStreetMap |
| Backend | Python + FastAPI + Uvicorn |
| Database | SQLite |
| Hosting | Render (Python web service + persistent storage) |
| Version control | Git + GitHub |

Browser AI downloads model assets on first use and may run slowly on older devices. Internet access is needed for the initial download and map tiles.

## 💻 Run locally

### Prerequisites

- Python 3.12 (or a compatible Python 3 version)
- A modern browser
- Internet access for the first browser AI model download and map tiles

```bash
git clone https://github.com/Musab516/civicfix-genesis.git
cd civicfix-genesis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend:app --reload
```

Visit **http://127.0.0.1:8000**.

**Browser AI does not require installing local PyTorch or `requirements-ai.txt`.** Those dependencies belong to the older optional server-side classifier and should not be added to the lightweight Render deployment.

### Create an administrator

From the project root, with the virtual environment activated:

```bash
python backend.py create-admin
```

Follow the prompts. Never commit credentials, local database files, uploads or environment secrets.

### Troubleshooting

- **Location unavailable:** Grant browser location permission or enter decimal coordinates such as `24.9000, 67.1000`. GPS depends on device/browser permissions.
- **No map marker:** Enter valid *numeric* latitude and longitude separated by a comma when reporting manually.
- **AI takes time:** The first browser classification may download and initialize the model. Keep the tab open; use manual classification if the device cannot run it.
- **`Could not import module "backend"`:** Run Uvicorn from the project root, not the home directory.
- **Render out-of-memory:** Keep inference in the browser. Avoid installing or initializing the large Python CLIP model on the 512 MB web service.

## 🗂️ Project structure

```text
civicfix-genesis/
├── backend.py          # FastAPI, database, auth, reports and admin APIs
├── index.html          # App interface
├── auth.js             # Authentication UI logic
├── auth.css            # Authentication styling
├── browser-ai.js       # Browser-side AI classification
├── mobile.css          # Responsive styles
├── requirements.txt    # Lightweight Python backend dependencies
├── requirements-ai.txt# Legacy optional server-side AI dependencies
├── render.yaml         # Render deployment configuration
├── DEPLOY.md           # Deployment instructions
└── README.md
```

## 🤝 Team collaboration

Frontend and backend changes should be developed independently to keep the live demonstration stable.

```bash
git clone https://github.com/Musab516/civicfix-genesis.git
cd civicfix-genesis
git switch -c frontend-redesign
```

Frontend contributors can work on `index.html`, `mobile.css`, `auth.css` and presentation/UI details. Preserve the backend API contracts, element IDs and JavaScript event hooks used by `auth.js` and `browser-ai.js`. Open a **pull request** to `main` instead of pushing unreviewed visual changes directly to production.

To sync your branch:

```bash
git fetch origin
git merge origin/main
```

## ☁️ Deployment

CivicFix is deployed on **Render** and connected to the repository's `main` branch. See [`DEPLOY.md`](DEPLOY.md) and [`render.yaml`](render.yaml) for configuration details.

**Persistence matters:** Account, report and uploaded-photo data must be kept on a persistent volume or other durable storage; an ephemeral deployment filesystem is not suitable for permanent data. Do not replace an existing disk configuration when updating build commands.

## 🔐 Current limitations

CivicFix is a **hackathon prototype**, not an official municipal complaint portal. It does not automatically submit reports to city authorities or guarantee repairs. Before use by a larger public audience, the application needs a dedicated security/privacy review, abuse prevention and moderation, stronger operational monitoring, and a clearly communicated retention/deletion policy.

## 🎬 Suggested Genesis demo

1. **Show the problem:** A real pothole or streetlight issue has no easy public tracking trail.
2. **Submit a report:** Upload a photo, get a browser AI suggestion and pin the location.
3. **Show community impact:** Find the report on the map and demonstrate upvotes or duplicate detection.
4. **Show the administrative workflow:** Review severity, move the report to *In Progress* and attach repair evidence when resolved.
5. **Show the outcome:** Open analytics to illustrate transparent tracking.

---

<div align="center">

**Built for Genesis — from reporting a problem to making its resolution visible.**

[Live App](https://civicfix-genesis.onrender.com) · [Repository](https://github.com/Musab516/civicfix-genesis)

</div>
