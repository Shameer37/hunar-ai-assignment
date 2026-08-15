# Hunar.ai Take-Home Assignment

AI Hiring Assistant + People Search & Reachout, built on [Hunar.ai](https://hunar.ai) Voice Agents.

- **Frontend**: Next.js (App Router) + TypeScript + shadcn/ui
- **Backend**: FastAPI (Python), deployed as a Vercel Python serverless function under `/api`
- **Voice AI**: [Hunar Voice Agents API](https://api.voice.hunar.ai/docs/external/)
- **Deployed solution**: https://hunar-ai-assignment-flax.vercel.app
- **Repo**: https://github.com/Shameer37/hunar-ai-assignment

## What's implemented

### 1. AI Hiring Assistant (`/hiring-assistant`)

Recruiter enters a candidate's name, phone number, and the role, and
explicitly confirms the candidate has agreed to receive the call (checkbox,
enforced both client- and server-side — the same phone-format + consent
pattern Task 2's reachout uses). The backend places a live outbound call
through a Hunar voice agent ("AI Hiring Screener") that conducts a short
structured phone screen (experience, current role, notice period, CTC,
availability) and the frontend polls for the call's status and structured
result in real time.

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

**Known limitation:** PDL's `search` credits are a separate, much smaller
pool than its enrichment/purchased credits, and the trial key used here has
very few left. A request for more results than remain in that pool is
rejected outright (`402`, 0 partial results) rather than truncated, so
`_people_search.py` deliberately asks for a small page size (`size: 5`) to
stay within budget. If search returns a clean "PDL API access denied /
payment required" error, the account's search pool is exhausted — that's a
real, surfaced error per the no-mock-fallback design, not a bug.

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
  index.py                  all routes, CORS, per-IP rate limiting, exception handlers
  _hunar.py                 Hunar API client (reads HUNAR_API_KEY from env) -- unchanged, reused by both tasks
  _pdl.py                     real PDL Person Search client (reads PDL_API_KEY from env)
  _people_search.py          JD -> PDL search criteria -> normalized candidates; no mock fallback
/scripts/setup_agents.py    one-time script: creates the two Hunar agents this app uses
/tests/test_api.py          FastAPI TestClient smoke tests (mocked Hunar/PDL, no real API calls)
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

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

11 smoke tests against the FastAPI app (`tests/test_api.py`) using
`TestClient`, with `api._hunar.create_call` / `api._pdl.search_people`
mocked — no real calls placed, no real API credits spent. Covers: health
check, phone-format + consent validation on both call-placing endpoints,
the reachout dedupe guard, the per-IP rate limiter, and — regression-tested
directly from a real bug hit during development — that a PDL response
where redacted fields come back as the literal boolean `true` instead of a
string doesn't crash the candidate normalizer.

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
- **CORS** is restricted to `localhost:3000` and this project's own Vercel
  domains (`api/index.py`) instead of `*`. This only affects *other*
  websites' browser JS calling the API cross-origin — our own frontend
  calls it same-origin via the `vercel.json` rewrite either way, so this
  doesn't change how the app itself behaves.
- **Per-IP rate limiting** on the three endpoints that either place a real
  phone call or hit a metered third-party API (`/api/hiring/screen`,
  `/api/people/reachout`: 5 requests / 15 min; `/api/people/search`: 20
  requests / 15 min) — so a bot or a curious visitor can't casually drain
  the finite, 3-day Hunar key or PDL's search credits. Deliberately
  in-memory and per-serverless-instance, the same honest trade-off as the
  existing reachout dedupe guard: real protection against a burst, not a
  distributed guarantee across every cold instance — an acceptable bar for
  a take-home demo, not a claim of production-grade abuse protection.
- **Task 1** now requires the same E.164 phone format and explicit consent
  confirmation as Task 2's reachout, enforced both client-side (the form)
  and server-side (`ScreeningRequest`) — previously only Task 2 had this.
