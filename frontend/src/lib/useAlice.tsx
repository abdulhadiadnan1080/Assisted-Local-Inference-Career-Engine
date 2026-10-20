import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { api } from "./api";
import type { AliceState, JobView } from "./api";
import type { Job } from "../data/jobs";
import { allIntake, todayFifteen } from "../data/jobs";

type Ctx = {
  state: AliceState | null;
  online: boolean;
  checked: boolean;
  refresh: () => void;
};

const AliceCtx = createContext<Ctx>({ state: null, online: false, checked: false, refresh: () => {} });

export function AliceProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AliceState | null>(null);
  const [online, setOnline] = useState(false);
  const [checked, setChecked] = useState(false);
  const [tick, setTick] = useState(0);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const next = await api.state();
        if (!alive) return;
        setState(next);
        setOnline(true);
      } catch {
        if (!alive) return;
        setOnline(false);
      } finally {
        if (alive) setChecked(true);
      }
    };
    load();
    const id = window.setInterval(load, 6000);
    return () => {
      alive = false;
      window.clearInterval(id);
    };
  }, [tick]);

  const value = useMemo(() => ({ state, online, checked, refresh }), [state, online, checked, refresh]);
  return <AliceCtx.Provider value={value}>{children}</AliceCtx.Provider>;
}

export const useAlice = () => useContext(AliceCtx);

const SAMPLES: Record<JobView, Job[]> = {
  briefing: todayFifteen,
  intake: allIntake,
  review: allIntake.filter((j) => j.status === "review"),
  backlog: allIntake,
  history: todayFifteen.slice(0, 2).map((j, i) => ({
    ...j,
    status: i === 0 ? "applied" : "sent",
    rawStatus: i === 0 ? "APPLIED" : "SENT",
    letter: { ...j.letter, sent: i === 1 },
    briefing: false,
  })),
  all: [
    ...todayFifteen.slice(0, 2).map((j, i) => ({
      ...j,
      status: (i === 0 ? "applied" : "sent") as Job["status"],
      rawStatus: i === 0 ? "APPLIED" : "SENT",
      letter: { ...j.letter, sent: i === 1 },
    })),
    ...todayFifteen.slice(2),
    ...allIntake,
  ],
};

export type JobsResult = {
  jobs: Job[];
  loading: boolean;
  /** "live" once the backend has returned rows; "sample" while it is offline or empty. */
  source: "live" | "sample";
  error: string | null;
  reload: () => void;
};

export function useJobs(view: JobView, opts?: { emptyOk?: boolean }): JobsResult {
  const { online, checked } = useAlice();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const reload = useCallback(() => setTick((t) => t + 1), []);
  const seen = useRef(false);

  useEffect(() => {
    if (!checked) return;
    if (!online) {
      setLoading(false);
      return;
    }
    let alive = true;
    setLoading(!seen.current);
    api
      .jobs(view)
      .then((res) => {
        if (!alive) return;
        setJobs(res.jobs);
        setError(null);
        seen.current = true;
      })
      .catch((err: Error) => alive && setError(err.message))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [view, online, checked, tick]);

  const live = online && (jobs.length > 0 || Boolean(opts?.emptyOk && seen.current));
  return {
    jobs: live ? jobs : SAMPLES[view],
    loading,
    source: live ? "live" : "sample",
    error,
    reload,
  };
}
