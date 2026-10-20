import { useMemo, useState } from "react";
import type { Job } from "../data/jobs";
import JobDrawer from "../components/JobDrawer";
import { Banner } from "../components/ui";
import { useAlice, useJobs } from "../lib/useAlice";

type Bucket =
  | "all"
  | "APPLIED"
  | "SENT"
  | "BOTH"
  | "SKIPPED"
  | "NEEDS_REVIEW"
  | "READY"
  | "BACKLOG"
  | "ARCHIVED";

const BUCKETS: { id: Bucket; label: string }[] = [
  { id: "all", label: "All" },
  { id: "APPLIED", label: "Applied" },
  { id: "SENT", label: "Email sent" },
  { id: "BOTH", label: "Applied + sent" },
  { id: "SKIPPED", label: "Skipped" },
  { id: "NEEDS_REVIEW", label: "Reviewed / held" },
  { id: "READY", label: "Ready" },
  { id: "BACKLOG", label: "Backlog" },
  { id: "ARCHIVED", label: "Archived" },
];

function rawOf(job: Job) {
  return job.rawStatus || job.status.toUpperCase();
}

function labelFor(job: Job) {
  const raw = rawOf(job);
  if (raw === "BOTH") return "Applied + sent";
  if (raw === "SENT") return "Email sent";
  if (raw === "APPLIED") return "Applied";
  if (raw === "NEEDS_REVIEW") return "Needs review";
  if (raw === "READY") return "Ready";
  if (raw === "BACKLOG") return "Backlog";
  if (raw === "ARCHIVED") return "Archived";
  if (raw === "SKIPPED") return "Skipped";
  return raw.replace(/_/g, " ").toLowerCase();
}

function tagClass(job: Job) {
  const raw = rawOf(job);
  if (raw === "NEEDS_REVIEW") return "review";
  if (raw === "ARCHIVED" || raw === "SKIPPED") return "archived";
  if (raw === "SENT" || raw === "BOTH") return "sent";
  if (raw === "APPLIED") return "applied";
  return "new";
}

export default function Database() {
  const { online, state } = useAlice();
  const { jobs, source, loading } = useJobs("all", { emptyOk: true });
  const [open, setOpen] = useState<Job | null>(null);
  const [query, setQuery] = useState("");
  const [only, setOnly] = useState<Bucket>("all");

  const counts = useMemo(() => {
    const acc: Record<string, number> = {};
    for (const job of jobs) {
      const key = rawOf(job);
      acc[key] = (acc[key] || 0) + 1;
    }
    return acc;
  }, [jobs]);

  const rows = useMemo(
    () =>
      jobs.filter((job) => {
        const hay = `${job.company} ${job.title} ${job.source} ${job.applyUrl}`.toLowerCase();
        const matches = hay.includes(query.toLowerCase());
        return matches && (only === "all" || rawOf(job) === only);
      }),
    [jobs, query, only],
  );

  return (
    <>
      <div className="ws-head">
        <div>
          <span className="eyebrow">Database</span>
          <h2>Every listing Alice has kept</h2>
          <p>
            Applied, emailed, skipped, held for review, backlog, ready, and archived — one SQLite ledger. Click a
            row for the scorecard. The posting URL is on the row.
          </p>
        </div>
        <div className="chips">
          <span className="chip">{jobs.length} rows</span>
          <span className="chip">{(counts.APPLIED || 0) + (counts.BOTH || 0)} applied</span>
          <span className="chip">{(counts.SENT || 0) + (counts.BOTH || 0)} emailed</span>
          <span className="chip">{counts.NEEDS_REVIEW || 0} in review</span>
        </div>
      </div>

      {!online ? (
        <Banner tone="warn">
          <b>Backend offline.</b> Showing a sample mix so the page still has shape.
        </Banner>
      ) : source === "sample" && loading ? (
        <Banner>Loading the ledger…</Banner>
      ) : null}

      <div className="chips" style={{ marginBottom: 16, alignItems: "center" }}>
        <input
          className="inp"
          style={{ maxWidth: 280 }}
          placeholder="Search company, role, source, URL"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {BUCKETS.map((b) => (
          <button
            key={b.id}
            className={`btn btn-sm ${only === b.id ? "btn-primary" : "btn-outline"}`}
            onClick={() => setOnly(b.id)}
          >
            {b.label}
            {b.id !== "all" ? ` ${counts[b.id] || 0}` : ""}
          </button>
        ))}
      </div>

      <div className="tablewrap">
        <table className="table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Role</th>
              <th>Source</th>
              <th>Score</th>
              <th>Status</th>
              <th>Posting</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((job) => {
              const href = job.applyUrl || job.sourceUrl || "";
              return (
                <tr key={job.id} onClick={() => setOpen(job)}>
                  <td>
                    <b>{job.company}</b>
                  </td>
                  <td>{job.title}</td>
                  <td>{job.source}</td>
                  <td>{job.scores.composite ? job.scores.composite.toFixed(2) : "—"}</td>
                  <td>
                    <span className={`tag ${tagClass(job)}`}>{labelFor(job)}</span>
                  </td>
                  <td>
                    {href ? (
                      <a
                        className="table-link"
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {href.replace(/^https?:\/\//, "")}
                      </a>
                    ) : (
                      <span className="small">No URL</span>
                    )}
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 ? (
              <tr>
                <td colSpan={6} className="small">
                  {jobs.length === 0
                    ? "SQLite is empty. Run now or seed a deck, then come back."
                    : "Nothing matches that filter."}
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {state?.counts ? (
        <p className="small" style={{ marginTop: 14 }}>
          Engine counts · ready {state.counts.READY ?? 0} · backlog {state.counts.BACKLOG ?? 0} · review{" "}
          {state.counts.NEEDS_REVIEW ?? 0} · archived {state.counts.ARCHIVED ?? 0} · applied {state.counts.APPLIED ?? 0}{" "}
          · sent {state.counts.SENT ?? 0} · both {state.counts.BOTH ?? 0} · skipped {state.counts.SKIPPED ?? 0}
        </p>
      ) : null}

      {open ? (
        <JobDrawer
          job={open}
          live={source === "live"}
          onApply={() => window.open(open.applyUrl || open.sourceUrl, "_blank", "noreferrer")}
          onClose={() => setOpen(null)}
        />
      ) : null}
    </>
  );
}
