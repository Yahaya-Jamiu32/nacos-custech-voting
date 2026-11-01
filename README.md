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

## Who can vote (strict roll)
Only matrics of the form `<prefix><3- or 4-digit number: 001-999 or 0001-9999>` for the 40 department groups (20 for L1 and 20 for L2) can log in, e.g. `23L1CS100`, `23L1CS0301`, `23L2CS8602`. Anything else (000 or 0000, 1-2 digit or 5-digit numbers, letters or symbols after the prefix, other years or levels) is refused. The only exception is the built-in admin matric. The rule lives in `is_eligible` in `votingapp/core.py`; change `MAX_SERIAL`, `ELIGIBLE_L1` or `ELIGIBLE_L2` there if the roll changes.

## Face check
After login each voter scans their face once. The browser turns the face into 128 numbers (no photo is sent or stored). The server refuses a face that is already linked to another matric, and on later logins the face must match the one stored for that matric. Ballot and voting stay locked until the check passes. The admin is exempt.
- **Consent and deletion:** a consent box is shown before scanning. After the election open Election Control and tap **Delete ALL face data**.
- **Wrongly blocked student:** Election Control > Face data > enter the matric > **Reset this voter's face** (recorded in the audit log).
- **Emergency off switch:** set `FACE_ENABLED=0` in Vercel and redeploy. `FACE_THRESHOLD` (default 0.5) is how close two scans must be to count as the same person; lower is stricter.
- **Scanner files:** loaded from the jsDelivr CDN by default. To self-host, put `face-api.js` in `public/js/` and the model files in `public/models/`.
- **Limits (tell your electorate):** the check runs in the voter's browser, so a determined person could bypass it, and there is no liveness test, so a photo of a face may pass. Twins and look-alikes can be wrongly matched. It deters casual duplicate accounts; it is not proof of identity.
- **Do not turn it on mid-election:** voters who already voted would have to register a face before logging in again.

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
