# SkillPulse — Vercel deployment

## Recommended production setup

1. Import this folder/repository into Vercel.
2. Keep the Vercel project Root Directory set to this folder.
3. Add these Environment Variables:
   - `SECRET_KEY` — a long random secret
   - `JWT_SECRET_KEY` — another long random secret
   - `DATABASE_URL` — a PostgreSQL connection string from Neon, Supabase, or another managed PostgreSQL provider.
4. Deploy.

`vercel.json` routes every request through the Flask WSGI entrypoint at `api/index.py`. This prevents the SPA/API/portfolio paths from becoming Vercel 404s.

## Quick health check

After deployment, open:

`https://YOUR-DOMAIN.vercel.app/api/health`

Expected response:

`{"status":"ok"}`

Then open the root:

`https://YOUR-DOMAIN.vercel.app/`

The portfolio route is:

`https://YOUR-DOMAIN.vercel.app/portfolio/<username>`

## Important database note

If `DATABASE_URL` is omitted on Vercel, the app falls back to `/tmp/skillpulse.db` so the deployment can boot for a demo. `/tmp` is not persistent storage on Vercel, so registrations/data can disappear between serverless instances. Use PostgreSQL for real use.
