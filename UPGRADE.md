# CivicFix Genesis — Authentication + Municipal Demo Panel

Unzip this release and copy all files into your existing `~/civicfix/` folder, replacing index.html and backend.py. **Do not delete `civicfix.db`** or `.venv`: your existing records are preserved through an automatic additive migration.

Run:
```bash
cd ~/civicfix
source .venv/bin/activate
python backend.py create-admin
uvicorn backend:app --reload
```
Use the admin email and password you created to log in. The admin navigation item then appears.
Citizens can sign up normally through the website and submit reports, upvote issues, and see tracking statuses. Existing anonymous reports remain visible; they are not retroactively assigned to a citizen. Only admin accounts can change statuses.

New APIs:
- POST `/api/auth/register`, POST `/api/auth/login`, POST `/api/auth/logout`, GET `/api/auth/me`
- GET `/api/my-reports`, POST `/api/reports/{id}/vote`
- GET `/api/admin/overview`, PATCH `/api/reports/{id}` (admin only)

Security: Password hashes use PBKDF2-SHA256 with unique salts; sessions are random bearer tokens, stored hashed in SQLite and expire after 7 days. This is a **local hackathon demo**: deploy behind HTTPS, introduce rate limiting/email verification and hardened session storage, and use a proper identity service before any real-world launch. There is no actual municipal-government integration.

Note: AI model and existing frontend assets remain unchanged. The existing optional `requirements-ai.txt` may install GPU dependencies; if CPU PyTorch already works, do not reinstall that file.
