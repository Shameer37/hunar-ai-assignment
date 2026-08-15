"use client";

import { useEffect, useRef, useState } from "react";
import { getCall, isTerminalStatus, type HunarCall } from "@/lib/api";

type State = { callId: string; call: HunarCall | null; error: string | null };

/** Polls GET /api/calls/{id} every 4s until the call reaches a terminal status. */
export function useCallPoll(callId: string | null) {
  const [state, setState] = useState<State | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!callId) return;

    const poll = async () => {
      try {
        const data = await getCall(callId);
        setState({ callId, call: data, error: null });
        if (isTerminalStatus(data.status) && timer.current) {
          clearInterval(timer.current);
          timer.current = null;
        }
      } catch (e) {
        setState({
          callId,
          call: null,
          error: e instanceof Error ? e.message : String(e),
        });
        if (timer.current) {
          clearInterval(timer.current);
          timer.current = null;
        }
      }
    };

    poll();
    timer.current = setInterval(poll, 4000);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [callId]);

  // Ignore stale state left over from a previous callId until the first
  // poll for the new one resolves, without imperatively resetting state
  // inside the effect (which would trigger an extra render).
  const current = state?.callId === callId ? state : null;
  return { call: current?.call ?? null, error: current?.error ?? null };
}
