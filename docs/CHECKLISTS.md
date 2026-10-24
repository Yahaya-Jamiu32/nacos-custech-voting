# Security checklist
- [ ] `.env` never committed; secrets only in Vercel env vars
- [ ] Strong SECRET_KEY, PHONE_PEPPER; admin password 12+ chars
- [ ] Supabase RLS enabled on all tables; use only the pooler DB URL; service-role key unused
- [ ] Penetration/concurrency test on a staging Postgres
# Pre-election readiness
- [ ] Official logos added; category 19 name confirmed and activated
- [ ] All candidates entered; test election run and cancelled
- [ ] Backup: Supabase backups enabled; export tables before opening
- [ ] Voters told: vote only with your own details; report disputes to committee
# Troubleshooting
- 500 on every call: check env vars in Vercel and DATABASE_URL (pooler, port 6543)
- Login always fails: matric must contain an eligible substring; phone must match first-used phone
