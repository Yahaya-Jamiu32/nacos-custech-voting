# NACOS CUSTECH Electronic Voting System
Flask API + single-page frontend, Supabase PostgreSQL, hosted entirely on Vercel. You do NOT need to run anything on your laptop.

## Deploy in 5 steps (no local setup)
1. **GitHub:** make the repository **Private** (the admin matric and phone are in the code). unzip this project. On github.com click New repository, then "uploading an existing file", and drag in the *contents* of the unzipped folder (not the ZIP; make sure `.github` and `.gitignore` are included). Commit. The "tests" tab (Actions) runs the automated tests for you; open it and confirm a green tick.
2. **Supabase:** create a project. Connect > "Transaction pooler" > copy the URI (port 6543) and put your database password in it. If the password has symbols such as @ # / : %, change it to letters and numbers only, or the URL breaks.
3. **Vercel:** Add New > Project > import the GitHub repo. Before deploying, open Environment Variables and add: `SECRET_KEY`, `PHONE_PEPPER` (any long random text each), `DATABASE_URL` (from step 2), `ADMIN_PASSWORD` (12+ characters; the admin matric and phone are already built in). Framework preset: leave as detected (Flask). Deploy.
4. **Check:** open `https://YOUR-SITE.vercel.app/api/health`. You should see `"ok": true, "db": true, "admin_configured": true`. Tables and the 20 categories are created automatically on first start.
5. **Set up the election:** open the site, Login to Vote > Administrator login (matric, phone, admin password). Add candidates, rename and activate category 19 when you have the official name, then Election Control > Start Voting. Do a full test election first, then Cancel it and start the real one.

If `/api/health` fails: Vercel > Project > Logs. Most common causes: wrong DATABASE_URL, special characters in the DB password, a missing environment variable. After changing a variable you must Redeploy.

## Project layout
`app.py` (entrypoint) · `votingapp/` (models, routes, PDF) · `public/` (frontend) · `tests/` · `scripts/` (optional local tools) · `docs/CHECKLISTS.md`

## Rules
- Voting works only while the election is open; Stop and each vote use the same database lock, so a vote committed before Stop counts and any later vote is rejected.
- Categories and candidates can be edited only before voting starts. Removals are soft (records kept).
- Ties are flagged, never auto-decided. Results PDF only after voting is stopped.

## Security limits (tell your electorate)
- Matric + phone is not proof of identity; the first person to use a matric claims it. Corrections currently need a manual database edit.
- The database links votes to voter IDs, so ballot secrecy is not perfect. Results screens never show who voted for whom.
- Login rate limiting is per internet connection.

## Optional: run locally
`pip install -r requirements-dev.txt`, `pytest`; `vercel dev` for the full site.

## Not built yet
Photo upload (use an https photo URL), runoff screen for ties, matric/phone correction screen, Alembic migrations.
