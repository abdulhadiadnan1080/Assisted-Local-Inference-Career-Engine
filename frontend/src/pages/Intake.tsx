import { useMemo, useState } from "react";
import type { Job, JobStatus } from "../data/jobs";
import JobDrawer from "../components/JobDrawer";
import { Banner, Toast } from "../components/ui";
import { useAlice, useJobs } from "../lib/useAlice";
import { api } from "../lib/api";

type Filter = "all" | "review" | "new" | "archived";

const LABELS: Record<Filter, string> = {
  all: "All",
  review: "Needs review",
  new: "Backlog",
  archived: "Archived",
};

export default function Intake() {
  const { online } = useAlice();
  const { jobs, source, reload } = useJobs("intake");
  const [open, setOpen] = useState<Job | null>(null);
  const [query, setQuery] = useState("");
  const [only, setOnly] = useState<Filter>("all");
  const [toast, setToast] = useState("");

  const rows = useMemo(
    () =>
      jobs.filter((job) => {
        const matches = `${job.company} ${job.title} ${job.source}`.toLowerCase().includes(query.toLowerCase());
        return matches && (only === "all" || job.status === (only as JobStatus));
      }),
    [jobs, query, only],
  );

  const held = jobs.filter((j) => j.status === "review").length;

  function say(message: string) {
    setToast(message);
    setTimeout(() => setToast(""), 2800);
  }

  async function promote(job: Job) {
    if (source !== "live") return say("Sample deck — promote is disabled");
    try {
      const res = await api.promote(job.id);
      reload();
      say(`${job.company} → ${res.status}`);
    } catch (err) {
      say((err as Error).message);
    }
  }

  return (
    <>
      <div className="ws-head">
        <div>
          <span className="eyebrow">Intake</span>
          <h2>Everything else pulled today</h2>
          <p>
            The listings that did not take a briefing slot. Unknown headcount or pay lands in review rather than
            being guessed into the deck. Every row still carries the CV Alice would attach if you promote it.
          </p>
        </div>
        <div className="chips">
          <span className="chip">{jobs.length} listings</span>
          <span className="chip">{held} held for review</span>
        </div>
      </div>

      {!online ? (
        <Banner tone="warn">
          <b>Backend offline.</b> Showing the sample intake table.
        </Banner>
      ) : null}

      <div className="chips" style={{ marginBottom: 16, alignItems: "center" }}>
        <input
          className="inp"
          style={{ maxWidth: 280 }}
          placeholder="Filter by company, role, or source"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {(Object.keys(LABELS) as Filter[]).map((key) => (
          <button
            key={key}
            className={`btn btn-sm ${only === key ? "btn-primary" : "btn-outline"}`}
            onClick={() => setOnly(key)}
          >
            {LABELS[key]}
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
              <th>Pay / size</th>
              <th>Score</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((job) => (
              <tr key={job.id} onClick={() => setOpen(job)}>
                <td>
                  <b>{job.company}</b>
                </td>
                <td>{job.title}</td>
                <td>{job.source}</td>
                <td>
                  {job.pay} · {job.size}
                </td>
                <td>{job.scores.composite ? job.scores.composite.toFixed(2) : "—"}</td>
                <td>
                  <span className={`tag ${job.status === "review" ? "review" : "new"}`}>
                    {job.status === "review" ? "Needs review" : job.status}
                  </span>
                </td>
                <td>
                  {job.status === "review" ? (
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        promote(job);
                      }}
                    >
                      Promote
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
            {rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="small">
                  Nothing matches that filter.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {open ? (
        <JobDrawer
          job={open}
          live={source === "live"}
          onApply={() => window.open(open.applyUrl, "_blank", "noreferrer")}
          onClose={() => setOpen(null)}
        />
      ) : null}
      {toast ? <Toast message={toast} /> : null}
    </>
  );
}
