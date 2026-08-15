export type HunarCall = {
  id: string;
  callee_name?: string;
  mobile_number?: string;
  status: string;
  result?: Record<string, string> | null;
  recording_url?: string | null;
  duration_minutes?: number | null;
  engagement_status?: string | null;
  answered_by?: string | null;
};

export type Candidate = {
  id: string;
  pdl_id?: string | number;
  name: string;
  title: string;
  company: string;
  location: string;
  skills: string[];
  linkedin_url?: string | null;
  source: string;
};

export type SearchResponse = {
  query_role: string;
  source: string;
  total_entries?: number;
  message?: string | null;
  candidates: Candidate[];
};

export type ReachoutResult = {
  candidate_id: string;
  candidate_name: string;
  call_id?: string;
  status?: string;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    // FastAPI error bodies are either {detail: "message"} (our HTTPExceptions)
    // or {detail: [{msg: "...", ...}, ...]} (pydantic validation errors).
    // Surface a clean message either way instead of a raw status/stack trace.
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body?.detail)) {
        const joined = body.detail
          .map((d: { msg?: string }) => d.msg)
          .filter(Boolean)
          .join("; ");
        if (joined) message = joined;
      }
    } catch {
      // response wasn't JSON -- keep the generic message
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export function health() {
  return api<{
    status: string;
    hunar_key_configured: boolean;
    hiring_agent_configured: boolean;
    reachout_agent_configured: boolean;
    pdl_key_configured: boolean;
  }>("/api/health");
}

export function startScreeningCall(body: {
  candidate_name: string;
  mobile_number: string;
  job_role: string;
  company: string;
  consent_confirmed: boolean;
}) {
  return api<HunarCall>("/api/hiring/screen", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getCall(callId: string) {
  return api<HunarCall>(`/api/calls/${callId}`);
}

export function searchPeople(job_description: string) {
  return api<SearchResponse>("/api/people/search", {
    method: "POST",
    body: JSON.stringify({ job_description }),
  });
}

/**
 * Always single-candidate, and always requires an explicit, human-typed
 * test/consenting phone number -- never a number sourced from candidate
 * search data -- PDL profiles can include one, but it's never forwarded.
 */
export function reachOut(body: {
  candidate_id: string;
  candidate_name: string;
  candidate_title?: string;
  job_description: string;
  job_title: string;
  company: string;
  phone_number: string;
  consent_confirmed: boolean;
}) {
  return api<ReachoutResult>("/api/people/reachout", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED", "CANCELLED", "ERROR"]);

export function isTerminalStatus(status?: string | null) {
  return !!status && TERMINAL_STATUSES.has(status.toUpperCase());
}
