"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { searchPeople, reachOut, isTerminalStatus, type Candidate, type ReachoutResult } from "@/lib/api";
import { useCallPoll } from "@/lib/use-call-poll";

function CallRow({ result }: { result: ReachoutResult }) {
  const { call, error } = useCallPoll(result.call_id ?? null);

  if (result.error) {
    return (
      <TableRow>
        <TableCell className="font-medium">{result.candidate_name}</TableCell>
        <TableCell colSpan={5} className="text-sm text-destructive">
          {result.error}
        </TableCell>
      </TableRow>
    );
  }

  const r = call?.result || {};
  return (
    <TableRow>
      <TableCell className="font-medium">{result.candidate_name}</TableCell>
      <TableCell>
        <Badge variant={isTerminalStatus(call?.status) ? "default" : "secondary"}>
          {call?.status ?? "PENDING"}
        </Badge>
      </TableCell>
      <TableCell>{r["interested"] || "—"}</TableCell>
      <TableCell>{r["notice_period"] || "—"}</TableCell>
      <TableCell>{r["expected_ctc"] || "—"}</TableCell>
      <TableCell className="max-w-xs truncate" title={r["summary"] || ""}>
        {error ? <span className="text-destructive">{error}</span> : r["summary"] || "—"}
      </TableCell>
    </TableRow>
  );
}

export default function PeopleSearchPage() {
  const [jobDescription, setJobDescription] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("Hunar.ai");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [sourceNote, setSourceNote] = useState<string | null>(null);

  const [campaign, setCampaign] = useState<ReachoutResult[]>([]);
  const [reachingOut, setReachingOut] = useState(false);
  const [reachoutError, setReachoutError] = useState<string | null>(null);

  const onSearch = async (e: FormEvent) => {
    e.preventDefault();
    setSearching(true);
    setSearchError(null);
    setCandidates([]);
    setSelected(new Set());
    try {
      const res = await searchPeople(jobDescription);
      setCandidates(res.candidates);
      setSourceNote(res.note);
      if (!jobTitle) setJobTitle(res.query_role);
    } catch (e) {
      setSearchError(e instanceof Error ? e.message : String(e));
    } finally {
      setSearching(false);
    }
  };

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const onReachOut = async () => {
    setReachingOut(true);
    setReachoutError(null);
    try {
      const chosen = candidates.filter((c) => selected.has(c.id));
      const res = await reachOut({
        job_description: jobDescription,
        job_title: jobTitle || "Open Role",
        company,
        candidates: chosen.map((c) => ({
          id: c.id,
          name: c.name,
          mobile_number: c.mobile_number,
          title: c.title,
        })),
      });
      setCampaign((prev) => [...res.results, ...prev]);
    } catch (e) {
      setReachoutError(e instanceof Error ? e.message : String(e));
    } finally {
      setReachingOut(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          People Search &amp; Reachout
        </h1>
        <p className="text-muted-foreground">
          Paste a job description, find candidates, reach out by voice
          through Hunar.ai, and watch responses land in the dashboard below.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>1. Search</CardTitle>
          <CardDescription>
            Candidate search currently uses demo data (see note below) — swap
            in a People Data Labs / Apollo.io / Proxycurl / Coresignal key in{" "}
            <code>api/_people_search.py</code> to go live.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSearch} className="flex flex-col gap-4">
            <div className="grid gap-1.5">
              <Label htmlFor="jd">Job description</Label>
              <Textarea
                id="jd"
                required
                rows={5}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the full job description here…"
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-1.5">
                <Label htmlFor="job_title">Job title (for the call script)</Label>
                <Input
                  id="job_title"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder="Senior Backend Engineer"
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="company">Company</Label>
                <Input
                  id="company"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                />
              </div>
            </div>
            <Button type="submit" disabled={searching} className="w-fit">
              {searching ? "Searching…" : "Search candidates"}
            </Button>
            {searchError && <p className="text-sm text-destructive">{searchError}</p>}
          </form>
        </CardContent>
      </Card>

      {candidates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>2. Select candidates to reach out to</CardTitle>
            {sourceNote && (
              <CardDescription>{sourceNote}</CardDescription>
            )}
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-8" />
                  <TableHead>Name</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Skills</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {candidates.map((c) => (
                  <TableRow
                    key={c.id}
                    className="cursor-pointer"
                    onClick={() => toggle(c.id)}
                  >
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selected.has(c.id)}
                        onChange={() => toggle(c.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell>{c.title}</TableCell>
                    <TableCell>{c.company}</TableCell>
                    <TableCell>{c.location}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {c.skills.join(", ")}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Button
              onClick={onReachOut}
              disabled={selected.size === 0 || reachingOut}
              className="w-fit"
            >
              {reachingOut
                ? "Calling…"
                : selected.size === 0
                  ? "Voice reach-out"
                  : `Voice reach-out to ${selected.size} candidate${
                      selected.size === 1 ? "" : "s"
                    }`}
            </Button>
            {reachoutError && (
              <p className="text-sm text-destructive">{reachoutError}</p>
            )}
          </CardContent>
        </Card>
      )}

      {campaign.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>3. Reachout dashboard</CardTitle>
            <CardDescription>
              Live call status and structured answers, polled from Hunar.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Candidate</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Interested</TableHead>
                  <TableHead>Notice period</TableHead>
                  <TableHead>Expected CTC</TableHead>
                  <TableHead>Summary</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {campaign.map((r, i) => (
                  <CallRow key={`${r.candidate_id}-${i}`} result={r} />
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
