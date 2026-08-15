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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  searchPeople,
  reachOut,
  isTerminalStatus,
  type Candidate,
  type ReachoutResult,
} from "@/lib/api";
import { useCallPoll } from "@/lib/use-call-poll";
import { usePersistedState } from "@/lib/use-persisted-state";

function CallRow({ result }: { result: ReachoutResult }) {
  const { call, error } = useCallPoll(result.call_id ?? null);
  const r = call?.result || {};
  return (
    <TableRow>
      <TableCell className="font-medium">{result.candidate_name}</TableCell>
      <TableCell>
        <Badge variant={isTerminalStatus(call?.status) ? "default" : "secondary"}>
          {call?.status ?? result.status ?? "PENDING"}
        </Badge>
      </TableCell>
      <TableCell>{r["interested"] || "—"}</TableCell>
      <TableCell>{r["notice_period"] || "—"}</TableCell>
      <TableCell>{r["expected_ctc"] || "—"}</TableCell>
      <TableCell>{r["best_callback_time"] || "—"}</TableCell>
      <TableCell className="max-w-xs truncate" title={r["summary"] || ""}>
        {error ? <span className="text-destructive">{error}</span> : r["summary"] || "—"}
      </TableCell>
    </TableRow>
  );
}

export default function PeopleSearchPage() {
  const [jobDescription, setJobDescription] = usePersistedState("t2:jobDescription", "");
  const [jobTitle, setJobTitle] = usePersistedState("t2:jobTitle", "");
  const [company, setCompany] = usePersistedState("t2:company", "Hunar.ai");
  const [candidates, setCandidates] = usePersistedState<Candidate[]>("t2:candidates", []);
  const [campaign, setCampaign] = usePersistedState<ReachoutResult[]>("t2:campaign", []);

  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchMessage, setSearchMessage] = useState<string | null>(null);

  const [dialogCandidate, setDialogCandidate] = useState<Candidate | null>(null);
  const [phoneNumber, setPhoneNumber] = useState("+91");
  const [reachingOut, setReachingOut] = useState(false);
  const [reachoutError, setReachoutError] = useState<string | null>(null);

  const onSearch = async (e: FormEvent) => {
    e.preventDefault();
    setSearching(true);
    setSearchError(null);
    setSearchMessage(null);
    setCandidates([]);
    try {
      const res = await searchPeople(jobDescription);
      setCandidates(res.candidates);
      setSearchMessage(res.message ?? null);
      if (!jobTitle) setJobTitle(res.query_role);
    } catch (e) {
      setSearchError(e instanceof Error ? e.message : String(e));
    } finally {
      setSearching(false);
    }
  };

  const openReachoutDialog = (candidate: Candidate) => {
    setDialogCandidate(candidate);
    setPhoneNumber("+91");
    setReachoutError(null);
  };

  const alreadyContacted = (candidateId: string) =>
    campaign.some((r) => r.candidate_id === candidateId);

  const confirmReachout = async () => {
    if (!dialogCandidate) return;
    setReachingOut(true);
    setReachoutError(null);
    try {
      const result = await reachOut({
        candidate_id: dialogCandidate.id,
        candidate_name: dialogCandidate.name,
        candidate_title: dialogCandidate.title,
        job_description: jobDescription,
        job_title: jobTitle || "Open Role",
        company,
        phone_number: phoneNumber.trim(),
        consent_confirmed: true,
      });
      setCampaign((prev) => [result, ...prev]);
      setDialogCandidate(null);
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
          Real candidate search via Apollo.io. Voice reachout through Hunar.ai
          only ever dials a phone number you explicitly type in and confirm —
          never a number sourced from search results.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>1. Search</CardTitle>
          <CardDescription>
            Candidate data comes from Apollo.io&apos;s People Search API in
            real time (see <code>api/_apollo.py</code>). No mock or fabricated
            candidates are ever shown.
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
              {searching ? "Searching Apollo…" : "Search candidates"}
            </Button>
            {searchError && (
              <p className="text-sm text-destructive">{searchError}</p>
            )}
            {searchMessage && !searchError && (
              <p className="text-sm text-muted-foreground">{searchMessage}</p>
            )}
          </form>
        </CardContent>
      </Card>

      {candidates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>2. Candidates</CardTitle>
            <CardDescription>
              Profile information only — no phone numbers are shown or stored
              here. Pick a candidate and provide a separate test/consenting
              number to place a call.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Skills</TableHead>
                  <TableHead>Profile</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead className="w-40" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {candidates.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell>{c.title}</TableCell>
                    <TableCell>{c.company}</TableCell>
                    <TableCell>{c.location}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {c.skills?.length ? c.skills.join(", ") : "—"}
                    </TableCell>
                    <TableCell>
                      {c.linkedin_url ? (
                        <a
                          href={c.linkedin_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sm font-medium text-primary underline underline-offset-4"
                        >
                          LinkedIn
                        </a>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">Apollo</Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant={alreadyContacted(c.id) ? "outline" : "default"}
                        onClick={() => openReachoutDialog(c)}
                      >
                        {alreadyContacted(c.id) ? "Reach Out Again" : "Reach Out"}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {campaign.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>3. Reachout dashboard</CardTitle>
            <CardDescription>
              Live call status and structured answers, polled from Hunar.
              Persists across refreshes.
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
                  <TableHead>Best callback time</TableHead>
                  <TableHead>Summary</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {campaign.map((r, i) => (
                  <CallRow key={`${r.candidate_id}-${r.call_id ?? i}`} result={r} />
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Dialog
        open={!!dialogCandidate}
        onOpenChange={(open) => {
          if (!open) setDialogCandidate(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Voice Reachout</DialogTitle>
            <DialogDescription>
              {dialogCandidate && (
                <>
                  Real Apollo candidate:{" "}
                  <span className="font-medium text-foreground">
                    {dialogCandidate.name} — {dialogCandidate.title}
                  </span>
                </>
              )}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-1.5">
            <Label htmlFor="reachout_phone">Demo / Consenting Phone Number</Label>
            <Input
              id="reachout_phone"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+919876543210"
            />
            <p className="text-xs text-muted-foreground">
              By starting this call, you confirm this is a test/consenting
              number — not the candidate&apos;s real number sourced from
              search results.
            </p>
          </div>

          {reachoutError && (
            <p className="text-sm text-destructive">{reachoutError}</p>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogCandidate(null)}>
              Cancel
            </Button>
            <Button onClick={confirmReachout} disabled={reachingOut}>
              {reachingOut ? "Starting…" : "Start Voice Reachout"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
