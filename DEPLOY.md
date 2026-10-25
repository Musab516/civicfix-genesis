# CivicFix Genesis — deployment and team collaboration

## Safe upgrade on Ubuntu

Back up your existing project first (especially `civicfix.db`):

```bash
cp -a ~/civicfix ~/civicfix-backup
```

Extract this release and copy its source files into `~/civicfix` without removing your database or `.venv`:

```bash
unzip civicfix-genesis-v3.zip -d ~/civicfix-v3-release
cp ~/civicfix-v3-release/civicfix/{backend.py,index.html,auth.js,auth.css,requirements.txt,requirements-ai.txt,render.yaml,.gitignore} ~/civicfix/
cd ~/civicfix
source .venv/bin/activate
uvicorn backend:app --reload
```

Database migrations run automatically and add only new columns/tables. Do not delete civicfix.db.

## Create a private GitHub repo

On GitHub, create a new **private** repository named `civicfix-genesis`, without initializing a README. Then on Ubuntu:

```bash
cd ~/civicfix
git init
git add backend.py index.html auth.js auth.css requirements.txt requirements-ai.txt README.md DEPLOY.md render.yaml .gitignore
git commit -m "CivicFix Genesis: authentication, prioritization, evidence, analytics"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/civicfix-genesis.git
git push -u origin main
```

If you use HTTPS and GitHub asks for a password, use the browser login via `gh auth login` / Git Credential Manager, or a personal access token, rather than your account password.

On GitHub: repo **Settings → Collaborators → Add people** and invite your teammate by GitHub username. They can clone the repo, create a `frontend-redesign` branch and send a pull request. Avoid sharing login credentials.

Do not commit `.venv`, `civicfix.db`, cached model files, personal photos, admin passwords or tokens. `.gitignore` protects common local artifacts, but check `git status` and `git diff --cached` before pushing.

## Deploy on Render

1. Push the repo to GitHub.
2. On Render, choose **New → Blueprint**, connect your repo, and use the included `render.yaml`.
3. The sample Blueprint requests a **paid Starter web service and persistent disk**; review current prices and confirm the charges before deploying.
4. Render builds and starts the app. The persistent disk stores the SQLite DB, account data, and report photos. Never run multiple worker processes against this SQLite-backed demo.
5. Once deployed, open your assigned `https://...onrender.com` URL. HTTPS permits browsers to request geolocation, but laptops without GPS might still be unable to locate themselves.
6. Create the first admin securely using a Render Shell (if available on your plan): `python backend.py create-admin`. Otherwise, use an authorized one-off job/SSH with access to the same disk. Do **not** create a public admin-creation endpoint or paste passwords into deployment commands/logs.

**AI on Render:** The default requirements intentionally omit local Torch/CLIP to keep deployments small. The local AI classifier still works on your Ubuntu machine with your installed CPU Torch/Transformers. If you want AI on the hosted app, upgrade RAM/storage and install CPU-only Torch plus compatible Transformers in the build step. A free/basic host may run out of RAM. The classify endpoint will return an explicit 503 until those optional dependencies/model weights are available; manual category selection remains functional.

For a production city-wide service, replace SQLite/large image blobs with managed Postgres and object storage, enforce rate limits and image privacy, add administrative auditing/verification, and review handling of publicly exposed coordinates and photos. This is a hackathon demo and **not connected to a municipal authority**.

## Suggested team workflow

- You: FastAPI/API, database, ML, deployment configuration.
- Teammate: `index.html`, `auth.css` and presentation, with changes to `auth.js` reviewed jointly.
- Keep feature branches and review pull requests before merging.
- Check `/api/health`, upload one report, upload repair evidence as admin, and view analytics after each deployment.
