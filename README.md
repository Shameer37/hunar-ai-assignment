# Hunar.ai Take-Home Assignment

AI Hiring Assistant + People Search & Reachout, built on [Hunar.ai](https://hunar.ai) Voice Agents.

- **Frontend**: Next.js (App Router) + TypeScript + shadcn/ui
- **Backend**: FastAPI (Python), deployed as a Vercel Python serverless function under `/api`
- **Voice AI**: [Hunar Voice Agents API](https://api.voice.hunar.ai/docs/external/)
- **Deployed solution**: https://hunar-ai-assignment-flax.vercel.app
- **Repo**: https://github.com/Shameer37/hunar-ai-assignment

## What's implemented

### 1. AI Hiring Assistant (`/hiring-assistant`)

Recruiter enters a candidate's name, phone number, and the role. The backend
places a live outbound call through a Hunar voice agent ("AI Hiring
Screener") that conducts a short structured phone screen (experience,
current role, notice period, CTC, availability) and the frontend polls for
the call's status and structured result in real time.

### 2. People Search & Reachout (`/people-search`)

Recruiter pastes a job description. The backend returns candidates matching
the role (see **Note on the people-search API** below), the recruiter picks
who to reach out to, and the backend places one outbound call per candidate
through a second Hunar voice agent ("Candidate Reachout Agent") that
introduces the role, gauges interest, and captures notice period / expected
compensation / callback preference. All calls land in a dashboard table
that polls Hunar for live status and results — no manual data entry.

**Note on the people-search API:** the assignment lists People Data Labs,
Apollo.io, Proxycurl, and Coresignal as options, but obtaining and testing a
key for any of them wasn't feasible inside this assignment's turnaround
time. `api/_people_search.py` returns realistic mock candidates behind the
exact interface a real provider call would use — swap the body of
`search_candidates()` for a live API call (using keywords extracted from the
JD) and nothing else in the app needs to change.

### 3. Attendance-tracking thought experiment (`/essay`)

Answer to: *"If there were no smartphones but LLMs exist / everything else
exists except apps, and you are an HR who has to track attendance of 1,000
people every day in 100 locations, what would you do?"*

**Short version:** use the phone network itself as the interface. A Hunar-style
voice AI agent places one daily bulk call per location (100 calls, not
1,000) to a site coordinator for a conversational roll-call, while
individuals can self-check-in with a missed call to an IVR line on any
phone. A random daily sample gets a lightweight voiceprint check to catch
proxy attendance, unanswered calls retry then fall back to SMS then escalate
to a human, and every call returns a structured result straight into one HR
dashboard — no manual data entry, no app install required. Full writeup with
reasoning is on the deployed site's `/essay` page.

## Architecture

```
/app                      Next.js App Router pages (frontend)
  /hiring-assistant        Task 1 UI
  /people-search           Task 2 UI
  /essay                   Task 3 writeup
/components/ui             shadcn/ui components
/lib                        typed API client + polling hook
/api                        FastAPI backend (Vercel Python serverless function)
  index.py                  all routes
  _hunar.py                 Hunar API client (reads HUNAR_API_KEY from env)
  _people_search.py         mock candidate search (swap-in point for a real provider)
/scripts/setup_agents.py    one-time script: creates the two Hunar agents this app uses
```

All `/api/*` requests are rewritten to the single FastAPI function
(`vercel.json`), so the frontend just calls same-origin `/api/...` routes in
both local dev (`vercel dev`) and production.

## Local setup

```bash
npm install
python -m venv .venv && .venv/Scripts/activate   # or source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# paste your Hunar API key into .env as HUNAR_API_KEY

python scripts/setup_agents.py
# copy the two printed agent IDs into .env as HIRING_AGENT_ID / REACHOUT_AGENT_ID

npx vercel dev
```

`vercel dev` runs the Next.js frontend and the Python backend together so
`/api/*` calls resolve locally exactly as they do in production.

## Deploying

```bash
npx vercel login      # one-time, opens a browser
npx vercel link       # one-time, links this folder to a Vercel project
npx vercel env add HUNAR_API_KEY production
npx vercel env add HIRING_AGENT_ID production
npx vercel env add REACHOUT_AGENT_ID production
npx vercel --prod
```

Environment variables are set through Vercel's Environment Variables UI/CLI
only — never committed. `.env` is gitignored; `.env.example` documents the
required keys without values.

## Security notes

- `HUNAR_API_KEY` is read only from the environment on the backend
  (`api/_hunar.py`); it is never sent to or readable from the browser.
- `.env`, `.env.local`, and `.vercel` are gitignored.
- `scripts/setup_agents.py` never prints the API key, only the resulting
  (non-secret) agent IDs.
- The Hunar API key provided for this assignment is revoked 3 days after
  issuance, so the deployed demo's live-calling features will stop working
  after that window; the UI and code remain fully reviewable.
