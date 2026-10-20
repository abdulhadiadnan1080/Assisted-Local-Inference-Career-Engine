import type { Job } from "../data/jobs";

/** Empty base means same-origin, which the Vite dev proxy forwards to 8471. */
const BASE = import.meta.env.VITE_ALICE_API ?? "";

export type AliceState = {
  ok: boolean;
  today: string;
  liveCrawl: boolean;
  running: boolean;
  gmail: boolean;
  jdBudget: number;
  counts: Record<string, number>;
  ollama: {
    reachable: boolean;
    installed: string[];
    scoring: string;
    writing: string;
    ready?: boolean;
  };
  candidate: { name: string; headline: string; email: string };
};

export type JobView = "briefing" | "intake" | "review" | "backlog" | "history" | "all";

export type Stage = { name: string; state: "ok" | "fail" | "skip"; detail: string };

export type ManualRun = {
  id: string;
  stages: Stage[];
  done: boolean;
  outcome: string | null;
  error: string | null;
  jobId: string | null;
  startedAt: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.reason ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

const post = <T,>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  state: () => request<AliceState>("/api/state"),
  jobs: (view: JobView, limit = 500) => request<{ jobs: Job[]; count: number }>(`/api/jobs?view=${view}&limit=${limit}`),
  job: (id: string) => request<{ job: Job }>(`/api/jobs/${id}`),
  sources: () =>
    request<{ sources: { id: string; name: string; enabled: boolean; paused: boolean }[] }>("/api/sources"),
  setSource: (id: string, enabled: boolean) =>
    post<{ sources: { id: string; name: string; enabled: boolean; paused: boolean }[] }>("/api/sources", {
      id,
      enabled,
    }),

  config: () => request<{ config: Record<string, unknown> }>("/api/config"),
  saveConfig: (config: Record<string, unknown>) => post<{ saved: boolean; config: Record<string, unknown> }>("/api/config", config),

  setLiveCrawl: (enabled: boolean) => post<{ live_crawl: boolean }>("/api/settings/live-crawl", { enabled }),
  runPipeline: () => post<{ started: boolean }>("/api/pipeline/run"),
  stopPipeline: () => post<{ stopped: boolean }>("/api/pipeline/stop"),
  seedDemo: () => post<{ count: number }>("/api/demo/seed"),

  apply: (id: string) => post<{ apply_url: string; status: string }>(`/api/jobs/${id}/apply`),
  send: (id: string) => post<{ status: string }>(`/api/jobs/${id}/send`),
  skip: (id: string) => post<{ status: string }>(`/api/jobs/${id}/skip`),
  saveDraft: (id: string, subject: string, body_text: string) =>
    post<{ ok: boolean }>(`/api/jobs/${id}/draft`, { subject, body_text }),
  promote: (id: string) => post<{ status: string }>(`/api/jobs/${id}/promote`),

  manualRun: (body: { url?: string; text?: string; company?: string; title?: string; tailor?: boolean }) =>
    post<{ runId: string; stageOrder: string[] }>("/api/manual/run", body),
  manualStatus: (runId: string) =>
    request<{ run: ManualRun; job: Job | null; stageOrder: string[] }>(`/api/manual/${runId}`),

  diagnostics: () => request<{ checks: { id: string; group: string; title: string }[] }>("/api/diagnostics"),
  runDiagnostics: (ids?: string[]) =>
    post<{ results: import("../components/Lights").CheckResult[]; summary: { ok: number; fail: number; warn: number } }>(
      "/api/diagnostics/run",
      { ids },
    ),
  runCheck: (id: string) =>
    post<{ result: import("../components/Lights").CheckResult }>(`/api/diagnostics/run/${id}`),
};
