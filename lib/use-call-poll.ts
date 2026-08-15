"use client";

import { useEffect, useRef, useState } from "react";
import { getCall, isTerminalStatus, type HunarCall } from "@/lib/api";

/** Polls GET /api/calls/{id} every 4s until the call reaches a terminal status. */
export function useCallPoll(callId: string | null) {
  const [call, setCall] = useState<HunarCall | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!callId) return;
    setCall(null);
    setError(null);

    const poll = async () => {
      try {
        const data = await getCall(callId);
        setCall(data);
        if (isTerminalStatus(data.status) && timer.current) {
          clearInterval(timer.current);
          timer.current = null;
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
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

  return { call, error };
}
