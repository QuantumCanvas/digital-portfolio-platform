# SkillPulse backend

A real Flask + SQLite backend for your "WT Project" (SkillPulse Network) React
app, which currently has **no backend at all** — auth is a fake `setIsAuthenticated(true)`,
and every piece of data (profile, skills, roadmap progress, circles, feed
posts) lives only in the browser's `localStorage`. This replaces that with
real accounts, a real database, and real APIs, matching the shape of the data
your `AppContext.jsx` already uses.

## Running it

```bash
cd skillpulse-backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Serves the API at `http://localhost:5000/api/...`. A SQLite DB is created
automatically at `instance/app.db` on first run, seeded with:
- the 3 target roles from your `initialData.js`
- the 5-node "fullstack-ai" skill roadmap
- the 3 growth circles + 2 sample discussions
- the 4 market trend cards
- 3 demo peer accounts (Maya, Liam, Devon) with sample posts, so the feed,
  circles and matchmaker aren't empty on a fresh install
  (all demo accounts use password `password123`)

## Endpoints

| Area | Route |
|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| Profile | `GET /api/profile/<id>`, `PUT /api/profile/me`, `POST/DELETE /api/profile/me/skills[/<id>]`, `POST/DELETE /api/profile/me/projects[/<id>]`, `POST /api/profile/projects/<id>/clap` |
| Roadmaps | `GET /api/roadmaps/<role_id>`, `POST /api/roadmaps/<role_id>/<node_id>/complete` |
| Circles | `GET /api/circles`, `POST /api/circles/<id>/join`, `POST /api/circles/<id>/discussions` |
| Feed | `GET /api/feed`, `POST /api/feed`, `POST /api/feed/<id>/clap`, `POST /api/feed/<id>/comments` |
| Peers | `GET /api/peers` |
| Connections | `GET /api/connections`, `POST /api/connections/request/<user_id>`, `POST /api/connections/<user_id>/accept`, `POST /api/connections/<user_id>/decline`, `DELETE /api/connections/<user_id>` |
| Portfolio | `PUT /api/profile/me/portfolio` (publish/unpublish + theme), public page at `GET /portfolio/<username>` |
| Meta | `GET /api/meta/target-roles`, `GET /api/meta/market-trends` |

All writes require `Authorization: Bearer <token>` from login/register.

## Wiring it into the React app

This is the piece your frontend doesn't have yet: an API client, and
swapping `AppContext.jsx`'s `localStorage` calls for real requests. At a
high level:

1. Add a small `src/services/api.js` with a `fetch` wrapper that attaches
   the JWT (same pattern as `Authorization: Bearer <token>`).
2. In `AppContext.jsx`, replace:
   - `login()` / `signup()` → call `/api/auth/login` / `/api/auth/register`,
     store the returned token (e.g. in `localStorage` under one key, just
     for the token — not the whole user object), and store `user` in state
     from the response instead of building it locally.
   - The `localStorage.getItem('skillpulse_user')` / `_roadmaps` / `_circles`
     / `_posts` initializers → fetch from the matching endpoint on mount.
   - `completeSkillNode`, `addProject`, `clapProject`, `toggleJoinCircle`,
     `clapPost`, `addComment`, `createFeedPost` → call the matching endpoint
     instead of mutating local state directly, then update state from the
     response.
3. `fetchRealTimeMarketData()` in `realtimeDataService.js` can stay exactly
   as-is — it already calls the public GitHub API directly and doesn't need
   your backend.

Happy to do this wiring for you — just say the word and I'll go through
`AppContext.jsx` and the components that call it.

## Notes on scope

`replies` inside circle discussions aren't a full nested endpoint yet (just
`repliesCount`); `endorsements` from the original seed data aren't modeled
either. Both are natural next additions if you need them for the project.

## Frontend (added)

A full single-page frontend now lives in `frontend/index.html` and is served
by Flask at `http://localhost:5000/` — no separate build step or Node needed.
Run `python run.py` and open that URL. Log in with the demo account
`maya@example.com` / `password123`, or create your own.

Pages: Dashboard (skill radar, XP, next step), Roadmap (role switcher,
expandable trail, mark as mastered), Circles, Feed (compose, filter, clap,
comment, delete own posts), Peers (with profile preview), Trends, Profile
(edit details, skills, projects, claps).

## Connections & portfolio (added)

**Connections.** Any user can open another user's full profile (click a name or
avatar in the Feed, a card on Peers, or an invitation on Network) and press
**+ Connect**. That creates a *pending* request. The other person sees a badge on
the **Network** tab and can **Accept** or **Decline** from the Network page or from
the requester's profile. Only once accepted do both users count as connected.
The sender can undo a pending request, and either side can remove a connection.
If two people send each other a request, it is accepted automatically.

**Portfolio.** On **Profile → Portfolio**, press *Generate my portfolio* to publish a
public page at `/portfolio/<your-username>`, built from your profile, skills and
projects. Copy the link, pick one of four themes, or unpublish it (the link then
returns 404). Published portfolios also show a *View portfolio* button on your
profile when others visit it.

**Upgrading an existing `instance/app.db`:** no action needed. Two new columns
(`portfolio_enabled`, `portfolio_theme`) are added automatically on startup, and
the `connections` table is created by `db.create_all()`.

**Security notes.** `GET /api/profile/<id>` no longer returns a user's email unless
you are that user. Project demo/repo URLs and feed links must start with
`http://` or `https://` (checked on the server and again when rendering), so a
`javascript:` link can't be stored or clicked.
