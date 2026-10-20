import { useMemo, useState } from "react";
import type { Job } from "../data/jobs";
import JobTile from "../components/JobTile";
import JobDrawer from "../components/JobDrawer";
import { Banner, Toast } from "../components/ui";
import { useAlice, useJobs } from "../lib/useAlice";
import { api } from "../lib/api";

type Sort = "score" | "pay" | "time";

export default function Briefing() {
  const { online, state } = useAlice();
  const { jobs, loading, source, reload } = useJobs("briefing");
  const [open, setOpen] = useState<Job | null>(null);
  const [sort, setSort] = useState<Sort>("score");
  const [toast, setToast] = useState("");
  const [seeding, setSeeding] = useState(false);

  const sorted = useMemo(() => {
    const list = [...jobs];
    if (sort === "score") list.sort((a, b) => b.scores.composite - a.scores.composite);
    if (sort === "pay") {
      const rate = (p: string) => parseInt(p.replace(/\D/g, "") || "0", 10);
      list.sort((a, b) => rate(b.pay) - rate(a.pay));
    }
    if (sort === "time") list.sort((a, b) => a.posted.localeCompare(b.posted));
    return list;
  }, [jobs, sort]);

  const median = sorted.length ? sorted[Math.floor(sorted.length / 2)].scores.composite.toFixed(2) : "—";

  function say(message: string) {
    setToast(message);
    setTimeout(() => setToast(""), 2800);
  }

  async function onApply(job: Job) {
    window.open(job.applyUrl, "_blank", "noreferrer");
    if (source !== "live") return;
    try {
      await api.apply(job.id);
      reload();
      say(`Marked applied · ${job.company}`);
    } catch (err) {
      say((err as Error).message);
    }
  }

  async function onSkip(job: Job) {
    if (source !== "live") return say("Sample deck — skip is disabled");
    try {
      await api.skip(job.id);
      setOpen(null);
      reload();
      say(`Skipped ${job.company}`);
    } catch (err) {
      say((err as Error).message);
    }
  }

  async function seed() {
    setSeeding(true);
    try {
      const res = await api.seedDemo();
      reload();
      say(`Seeded ${res.count} jobs through the local models`);
    } catch (err) {
      say((err as Error).message);
    } finally {
      setSeeding(false);
    }
  }

  return (
    <>
      <div className="ws-head">
        <div>
          <span className="eyebrow">
            Briefing ·{" "}
            {new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}
          </span>
          <h2>Today’s fifteen</h2>
          <p>
            Under twenty people, hires internationally, $40–60 an hour, composite of at least 3.5. Open a tile for
            the full brief, the scorecard, and the CV Alice has attached.
          </p>
        </div>
        <div className="chips">
          <span className="chip live">{sorted.length} released</span>
          <span className="chip">Median {median}</span>
          {state?.running ? <span className="chip live">Pipeline running</span> : null}
        </div>
      </div>

      {!online ? (
        <Banner tone="warn">
          <b>Backend offline.</b> Showing the sample deck. Start it with{" "}
          <code>python -m uvicorn app:app --port 8471</code> from the <code>alice</code> folder.
        </Banner>
      ) : source === "sample" ? (
        <Banner>
          <b>No jobs released yet.</b> This is the sample deck. Seed a real one through Hermes and Gemma, or turn
          on live crawl in Automate.
          <button className="btn btn-primary btn-sm" onClick={seed} disabled={seeding}>
            {seeding ? "Running the models…" : "Seed a real deck"}
          </button>
        </Banner>
      ) : null}

      <div className="chips" style={{ marginBottom: 18 }}>
        {(
          [
            ["score", "Best fit"],
            ["pay", "Highest pay"],
            ["time", "Posted earliest"],
          ] as [Sort, string][]
        ).map(([key, label]) => (
          <button
            key={key}
            className={`btn btn-sm ${sort === key ? "btn-primary" : "btn-outline"}`}
            onClick={() => setSort(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {loading && !sorted.length ? (
        <section className="grid">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div className="skeleton" key={i} />
          ))}
        </section>
      ) : sorted.length ? (
        <section className="grid">
          {sorted.map((job) => (
            <JobTile key={job.id} job={job} onOpen={() => setOpen(job)} />
          ))}
        </section>
      ) : (
        <div className="empty">
          <h3>Nothing released today</h3>
          <p>Run the pipeline from Automate, or push a single listing through Manual run.</p>
        </div>
      )}

      {open ? (
        <JobDrawer
          job={open}
          live={source === "live"}
          onApply={() => onApply(open)}
          onSkip={() => onSkip(open)}
          onClose={() => setOpen(null)}
        />
      ) : null}
      {toast ? <Toast message={toast} /> : null}
    </>
  );
}
