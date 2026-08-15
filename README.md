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

Recruiter pastes a job description. The backend extracts search criteria
(job-title phrases) and calls **People Data Labs' real Person Search API**
(`POST /v5/person/search`, `api/_pdl.py`) — there is no mock fallback; if PDL
is unreachable, denies access, or rate-limits, the app returns a clean, real
error instead of fabricated candidates (`api/_people_search.py`).

PDL profiles *can* include phone numbers (`mobile_phone` / `phone_numbers`),
unlike some People Search APIs — so the normalizer in `api/_people_search.py`
deliberately never reads or forwards those fields to the frontend. Voice
reachout is a **separate, explicit, single-candidate flow**: pick a candidate
→ a dialog asks for a "Demo / Consenting Phone Number" you type in yourself →
confirming calls the existing Hunar `create_call()` client, unchanged, with
that number — never a number sourced from search results. This is enforced
server-side too: `ReachoutRequest` (`api/index.py`) has no field for
candidate contact data at all, only an explicit `phone_number` +
`consent_confirmed`.

Results (candidate list, and the reachout dashboard with live-polled Hunar
call status/answers) persist to `localStorage` (`lib/use-persisted-state.ts`)
so a refresh doesn't lose them — no database was added, per the assignment's
guidance to prioritize the real integration over persistence infrastructure.

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
  /people-search           Task 2 UI (search + reachout dialog + dashboard)
  /essay                   Task 3 writeup
/components/ui             shadcn/ui components (incl. dialog for reachout confirm)
/lib
  api.ts                    typed API client
  use-call-poll.ts           polls a Hunar call until terminal status
  use-persisted-state.ts     localStorage-backed state (Task 2 "dashboard")
/api                        FastAPI backend (Vercel Python serverless function)
  index.py                  all routes
  _hunar.py                 Hunar API client (reads HUNAR_API_KEY from env) -- unchanged, reused by both tasks
  _pdl.py                     real PDL Person Search client (reads PDL_API_KEY from env)
  _people_search.py          JD -> PDL search criteria -> normalized candidates; no mock fallback
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
# paste your PDL API key into .env as PDL_API_KEY

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
npx vercel env add PDL_API_KEY production
npx vercel --prod
```

Environment variables are set through Vercel's Environment Variables UI/CLI
only — never committed. `.env` is gitignored; `.env.example` documents the
required keys without values.

## Security notes

- `HUNAR_API_KEY` and `PDL_API_KEY` are read only from the environment on
  the backend (`api/_hunar.py`, `api/_pdl.py`); neither is ever sent to or
  readable from the browser, and no candidate phone/contact data from PDL
  is ever passed to Hunar automatically (see Task 2 above).
- `.env`, `.env.local`, and `.vercel` are gitignored.
- `scripts/setup_agents.py` never prints the API key, only the resulting
  (non-secret) agent IDs.
- The Hunar API key provided for this assignment is revoked 3 days after
  issuance, so the deployed demo's live-calling features will stop working
  after that window; the UI and code remain fully reviewable.
