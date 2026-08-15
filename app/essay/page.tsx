import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function EssayPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          3. Attendance tracking without smartphones
        </h1>
        <p className="text-muted-foreground">
          &ldquo;If there were no smartphones but LLMs exist / everything
          else exists except apps, and you are an HR who has to track
          attendance of 1,000 people every day in 100 locations, what would
          you do?&rdquo;
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>The constraint, reframed</CardTitle>
          <CardDescription>
            No app means no push notifications, no GPS geofencing, no
            fingerprint scanner in everyone&apos;s pocket. But the telephone
            network, landlines, feature phones, and LLMs all still exist. So
            the phone call itself becomes the interface — and an LLM-powered
            voice agent becomes the &ldquo;app.&rdquo;
          </CardDescription>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>1. Daily automated roll-call, not 1,000 individual check-ins</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm leading-relaxed text-muted-foreground">
          <p>
            Every location gets one designated coordinator (a shift lead,
            security guard, or site office phone). At a fixed time each
            morning, a voice AI agent places an outbound bulk call — exactly
            the pattern Hunar&apos;s <code>/calls/bulk/</code> endpoint
            supports — to all 100 location numbers at once. The agent
            conversationally reads the expected roster and asks the
            coordinator to confirm who is present, who is absent, and why.
            That&apos;s 100 calls, not 1,000, and it finishes in minutes.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>2. Self-check-in for anyone with any phone</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm leading-relaxed text-muted-foreground">
          <p>
            In parallel, individuals can give a missed call (or dial a
            toll-free number) to a fixed IVR line to mark themselves present
            — a pattern already proven at scale in India for exactly this
            reason. The LLM agent picks up, confirms identity by voice
            (&ldquo;say your name and employee ID&rdquo;), timestamps it, and
            logs it. No app install, no data plan required — it works on
            the cheapest Nokia-style handset.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>3. Fraud and proxy-attendance controls</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm leading-relaxed text-muted-foreground">
          <p>
            The weak point of any remote check-in is someone answering on
            behalf of someone else. Two mitigations: (a) enroll a short
            voiceprint per employee once, and have the LLM agent do
            lightweight voice-match on a random daily sample (say 5-10%) of
            check-ins, flagging mismatches for HR review; (b) have the
            coordinator&apos;s roll-call cross-checked against the
            self-check-in log automatically — any employee present in one
            list but not the other gets a same-day automated follow-up call
            asking for clarification, with the transcript attached.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>4. Failure handling</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm leading-relaxed text-muted-foreground">
          <p>
            Unanswered calls get 2-3 automatic retries with increasing
            urgency, then an SMS fallback (works on any phone, no data
            needed), then escalate to a regional HR contact if still
            unresolved by a cutoff time (e.g. 11 AM). Locations with
            historically poor connectivity keep a paper register as a
            physical backup, reconciled weekly by faxing or scanning it into
            the office system, where the same LLM does OCR + cross-check
            against the voice-based log as an audit layer — not the primary
            mechanism, since it isn&apos;t real-time.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>5. One dashboard, zero manual data entry</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm leading-relaxed text-muted-foreground">
          <p>
            Every call — coordinator roll-call, self-check-in, voice-match
            audit, follow-up — returns a structured result (present/absent,
            reason, confidence score) the same way Hunar&apos;s{" "}
            <code>result_schema</code> does in this assignment. All of it
            lands in one HR dashboard by ~10 AM daily, with locations below
            an attendance threshold or with unresolved discrepancies
            surfaced first. No one is retyping anything from a paper sheet
            into a spreadsheet — the voice AI agent is the data-entry
            layer.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Why this works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm leading-relaxed text-muted-foreground">
          <p>
            It uses infrastructure that already reaches everyone — the phone
            network — instead of infrastructure that requires everyone to
            own and configure something new. It scales sub-linearly (100
            coordinator calls cover 1,000 people). And it turns the LLM into
            exactly what it&apos;s good at here: a tireless, consistent,
            simultaneous conversationalist that never forgets to call, never
            mis-transcribes a name twice, and frees HR to work exceptions
            instead of chasing 1,000 daily confirmations by hand.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
