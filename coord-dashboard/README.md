# Coordination Dashboard (sub-project)

A separate, smaller project from the allocation engine in the rest of this repo. It's kept
here as a subfolder because it's thematically related (disaster response) but has no shared
code with the engine — different stack, different problem.

Where the top-level engine answers "given zones and depots, what's the best allocation?",
this is a basic operational tool: log an incoming emergency request, rank pending requests
by urgency, and match each one to an available resource.

## What it does

- **Log emergency requests** — location, type (Medical/Food/Shelter/Rescue/etc.), number of
  people affected, severity (LOW/MEDIUM/HIGH/CRITICAL), and a free-text description.
- **Priority scoring** (`backend/models.py`) — severity is the dominant factor, people
  affected is secondary and capped so it can't outweigh severity (a CRITICAL request
  affecting 2 people still outranks a LOW request affecting 50).
- **Resource matching** (`backend/models.py`) — for a new request, prefers an available
  resource whose type matches the request and whose capacity covers the people affected,
  picking the smallest sufficient one; falls back to the largest available resource if
  nothing fully covers the request.
- **FastAPI backend** (`backend/main.py`) with endpoints to create/list requests and
  resources, get a ranked list of pending requests, mark a request resolved, and a
  dashboard summary (active incidents, people needing help, available/total resources).
- **Supabase persistence** (`backend/database.py`) — requests and resources are stored in
  Supabase tables (see `backend/schema.sql`) instead of in memory.
- **Static HTML/CSS/JS frontend** (`frontend/`) that calls the API directly with `fetch()` —
  no build step, no framework.

## Tech stack

Python, FastAPI, Supabase (Postgres), vanilla HTML/CSS/JS.

## How to run it

```bash
# 1. Create a Supabase project at supabase.com, then run backend/schema.sql
#    in Supabase's SQL Editor to create the two tables.

# 2. From this coord-dashboard/ folder:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create your .env file
cp .env.example .env
# then fill in SUPABASE_URL and SUPABASE_KEY

# 4. Run the backend
uvicorn backend.main:app --reload --port 8000
```

Check it's up: `curl http://127.0.0.1:8000/health`, or open
`http://127.0.0.1:8000/docs` for the interactive API docs. Open `frontend/index.html`
directly in a browser to use the dashboard UI (it talks to the API at
`http://127.0.0.1:8000` by default — see `API_BASE` in `frontend/script.js`).

## Known limitations

- Resource matching has no distance/location logic — it doesn't know how far a resource is
  from a request, unlike the haversine-distance scoring used in the main allocation engine.
  It could be upgraded to reuse that logic if real coordinates are added.
- Authentication is not implemented — the API has no access control.
- No evidence/photo storage or historical analytics.
- The Supabase Row Level Security policies in `schema.sql` allow full read/write access,
  which is fine for a local demo but not for a real deployment with sensitive data.
