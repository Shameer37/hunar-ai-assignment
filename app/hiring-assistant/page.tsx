"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { startScreeningCall, isTerminalStatus } from "@/lib/api";
import { useCallPoll } from "@/lib/use-call-poll";

const PHONE_RE = /^\+[1-9]\d{7,14}$/;

export default function HiringAssistantPage() {
  const [candidateName, setCandidateName] = useState("");
  const [mobileNumber, setMobileNumber] = useState("+91");
  const [jobRole, setJobRole] = useState("");
  const [company, setCompany] = useState("Hunar.ai");
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [callId, setCallId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { call, error: pollError } = useCallPoll(callId);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    if (!PHONE_RE.test(mobileNumber.trim())) {
      setSubmitError("Enter a valid phone number in E.164 format, e.g. +919876543210.");
      return;
    }
    if (!consentConfirmed) {
      setSubmitError("You must confirm this candidate has agreed to receive this call.");
      return;
    }
    setSubmitting(true);
    setCallId(null);
    try {
      const res = await startScreeningCall({
        candidate_name: candidateName,
        mobile_number: mobileNumber.trim(),
        job_role: jobRole,
        company,
        consent_confirmed: consentConfirmed,
      });
      setCallId(res.id);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          AI Hiring Assistant
        </h1>
        <p className="text-muted-foreground">
          Places a live outbound voice-screening call through Hunar.ai and
          streams the structured results back here.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Start a screening call</CardTitle>
            <CardDescription>
              Number must include country code, e.g. +919876543210
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="flex flex-col gap-4">
              <div className="grid gap-1.5">
                <Label htmlFor="candidate_name">Candidate name</Label>
                <Input
                  id="candidate_name"
                  required
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  placeholder="Jane Doe"
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="mobile_number">Mobile number (E.164)</Label>
                <Input
                  id="mobile_number"
                  required
                  value={mobileNumber}
                  onChange={(e) => setMobileNumber(e.target.value)}
                  placeholder="+919876543210"
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="job_role">Job role</Label>
                <Input
                  id="job_role"
                  required
                  value={jobRole}
                  onChange={(e) => setJobRole(e.target.value)}
                  placeholder="Senior Backend Engineer"
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="company">Company</Label>
                <Input
                  id="company"
                  required
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                />
              </div>
              <div className="flex items-start gap-2">
                <Checkbox
                  id="consent"
                  checked={consentConfirmed}
                  onCheckedChange={(checked) => setConsentConfirmed(checked === true)}
                />
                <Label htmlFor="consent" className="text-sm font-normal leading-snug text-muted-foreground">
                  I confirm this candidate has agreed to receive this screening call.
                </Label>
              </div>
              <Button type="submit" disabled={submitting || !consentConfirmed}>
                {submitting ? "Placing call…" : "Call candidate"}
              </Button>
              {submitError && (
                <p className="text-sm text-destructive">{submitError}</p>
              )}
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Call status</CardTitle>
            <CardDescription>
              {callId ? `Call ID: ${callId}` : "No call started yet"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!callId && (
              <p className="text-sm text-muted-foreground">
                Fill in the form and start a call to see live status and
                results here.
              </p>
            )}
            {pollError && (
              <p className="text-sm text-destructive">{pollError}</p>
            )}
            {call && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-2">
                  <Badge variant={isTerminalStatus(call.status) ? "default" : "secondary"}>
                    {call.status}
                  </Badge>
                  {call.engagement_status && (
                    <Badge variant="outline">{call.engagement_status}</Badge>
                  )}
                  {call.answered_by && (
                    <Badge variant="outline">{call.answered_by}</Badge>
                  )}
                </div>

                {!isTerminalStatus(call.status) && (
                  <p className="text-sm text-muted-foreground">
                    Call in progress — refreshing every few seconds…
                  </p>
                )}

                {call.result && Object.keys(call.result).length > 0 && (
                  <>
                    <Separator />
                    <div className="grid gap-2 text-sm">
                      {Object.entries(call.result).map(([k, v]) => (
                        <div key={k} className="grid grid-cols-3 gap-2">
                          <span className="col-span-1 font-medium capitalize text-muted-foreground">
                            {k.replaceAll("_", " ")}
                          </span>
                          <span className="col-span-2">{v || "—"}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}

                {call.recording_url && (
                  <>
                    <Separator />
                    <a
                      className="text-sm font-medium text-primary underline underline-offset-4"
                      href={call.recording_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Listen to recording
                    </a>
                  </>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
