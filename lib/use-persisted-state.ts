"use client";

import { useCallback, useRef, useSyncExternalStore } from "react";

type Listener = () => void;

const listeners = new Map<string, Set<Listener>>();
const cache = new Map<string, unknown>();

function notify(key: string) {
  listeners.get(key)?.forEach((l) => l());
}

function readFromStorage<T>(key: string, initial: T): T {
  try {
    const raw = window.localStorage.getItem(key);
    if (raw === null) return initial;
    return JSON.parse(raw) as T;
  } catch {
    return initial;
  }
}

/**
 * useState-like hook backed by localStorage. Implemented with
 * useSyncExternalStore -- React's sanctioned way to read an external
 * system -- rather than useState+useEffect, since setState synchronously
 * inside an effect body is flagged by react-hooks/set-state-in-effect.
 * Lightweight stand-in for a database so the Task 2 dashboard survives a
 * page refresh without introducing a backend data store.
 */
export function usePersistedState<T>(key: string, initial: T) {
  // Freeze the first `initial` this hook instance ever saw. Callers often
  // pass fresh literals (e.g. []) on every render; useSyncExternalStore
  // requires getServerSnapshot to return a referentially stable value.
  const initialRef = useRef(initial);

  const subscribe = useCallback(
    (onChange: Listener) => {
      if (!listeners.has(key)) listeners.set(key, new Set());
      listeners.get(key)!.add(onChange);
      return () => listeners.get(key)?.delete(onChange);
    },
    [key]
  );

  const getSnapshot = useCallback(() => {
    if (!cache.has(key)) cache.set(key, readFromStorage(key, initialRef.current));
    return cache.get(key) as T;
  }, [key]);

  const getServerSnapshot = useCallback(() => initialRef.current, []);

  const value = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const setValue = useCallback(
    (updater: T | ((prev: T) => T)) => {
      const prev = cache.has(key) ? (cache.get(key) as T) : readFromStorage(key, initialRef.current);
      const next = typeof updater === "function" ? (updater as (p: T) => T)(prev) : updater;
      cache.set(key, next);
      try {
        window.localStorage.setItem(key, JSON.stringify(next));
      } catch {
        // storage full/unavailable -- keep the in-memory cache only
      }
      notify(key);
    },
    [key]
  );

  return [value, setValue] as const;
}
