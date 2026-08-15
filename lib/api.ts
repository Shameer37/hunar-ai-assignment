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
  name: string;
  title: string;
  company: string;
  location: string;
  mobile_number: string;
  email: string;
  skills: string[];
};

export type SearchResponse = {
  query_role: string;
  source: string;
  note: string;
  candidates: Candidate[];
};

export type ReachoutResult = {
  candidate_id: string;
  candidate_name: string;
  call_id?: string;
  status?: string;
  error?: string;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function health() {
  return api<{
    status: string;
    hunar_key_configured: boolean;
    hiring_agent_configured: boolean;
    reachout_agent_configured: boolean;
  }>("/api/health");
}

export function startScreeningCall(body: {
  candidate_name: string;
  mobile_number: string;
  job_role: string;
  company: string;
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

export function reachOut(body: {
  job_description: string;
  job_title: string;
  company: string;
  candidates: { id: string; name: string; mobile_number: string; title: string }[];
}) {
  return api<{ results: ReachoutResult[] }>("/api/people/reachout", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED", "CANCELLED", "ERROR"]);

export function isTerminalStatus(status?: string | null) {
  return !!status && TERMINAL_STATUSES.has(status.toUpperCase());
}
