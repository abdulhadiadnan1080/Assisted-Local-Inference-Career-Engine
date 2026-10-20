import { useEffect, useRef, useState } from "react";
import CvSheet from "../components/CvSheet";
import { Banner, Field, Toast } from "../components/ui";
import { useAlice } from "../lib/useAlice";
import { api } from "../lib/api";
import type { ManualRun, Stage } from "../lib/api";
import type { Job } from "../data/jobs";

const STAGE_COPY: Record<string, [string, string]> = {
  read: ["Read input", "Parsing the posting into company, title, pay, and headcount."],
  snippet: ["Snippet scan", "Cheap regex pass for the obvious disqualifiers."],
  fetch: ["Fetch description", "Pulling the full JD within today's fetch budget."],
  gate_a: ["Gate A · hard rules", "Headcount under 20, hires internationally, pay in band."],
  gate_b: ["Gate B · scoring", "Hermes scores five dimensions against your profile."],
  poster: ["Find the poster", "Looking for a named human and a public address."],
  tailor: ["Tailor the CV", "Gemma rewrites from the master profile. Facts only."],
  draft: ["Draft the letter", "Short, specific, and saved as a draft. Never sent."],
};

const ORDER = ["read", "snippet", "fetch", "gate_a", "gate_b", "poster", "tailor", "draft"];

const SAMPLE_JD = `Founding inference engineer at Lumen Thread.
We are 8 people, fully remote, worldwide. Visa friendly.
Pay is $52/hr USD. You will own the local-model serving path, keep the stack tiny, and ship weekly.
Python and MLX are the daily tools. Email maya@lumenthread.dev.`;

export default function Manual() {
  const { online, state } = useAlice();
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [run, setRun] = useState<ManualRun | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [toast, setToast] = useState("");
  const poll = useRef<number | null>(null);

  useEffect(
    () => () => {
      if (poll.current) window.clearInterval(poll.current);
    },
    [],
  );

  function say(message: string) {
    setToast(message);
    setTimeout(() => setToast(""), 3200);
  }

  async function start() {
    if (!online) return say("Backend offline — start it on 8471 first");
    setJob(null);
    try {
      const { runId } = await api.manualRun({ url, text, company, title: role });
      setRun({
        id: runId,
        stages: [],
        done: false,
        outcome: null,
        error: null,
        jobId: null,
        startedAt: new Date().toISOString(),
      });
      if (poll.current) window.clearInterval(poll.current);
      poll.current = window.setInterval(async () => {
        try {
          const res = await api.manualStatus(runId);
          setRun(res.run);
          if (res.job) setJob(res.job);
          if (res.run.done && poll.current) {
            window.clearInterval(poll.current);
            poll.current = null;
          }
        } catch {
          // keep polling; a transient failure is not fatal
        }
      }, 900);
    } catch (err) {
      say((err as Error).message);
    }
  }

  function reset() {
    if (poll.current) window.clearInterval(poll.current);
    poll.current = null;
    setRun(null);
    setJob(null);
  }

  const reported = new Map<string, Stage>((run?.stages ?? []).map((s) => [s.name, s]));
  const running = Boolean(run && !run.done);
  const nextPending = ORDER.find((name) => !reported.has(name));

  function classFor(name: string) {
    const stage = reported.get(name);
    if (stage) return stage.state === "fail" ? "fail" : stage.state === "skip" ? "" : "done";
    if (running && name === nextPending) return "run";
    return "";
  }

  return (
    <div className="wrap section" style={{ paddingTop: 40 }}>
      <div className="ws-head">
        <div>
          <span className="eyebrow">Manual run</span>
          <h2>Push one listing through the whole engine</h2>
          <p>
            Paste a posting or a URL and watch every stage report. This is the same code path the morning run takes,
            one listing at a time, with nothing scheduled and nothing sent.
          </p>
        </div>
        <div className="chips">
          <span className="chip">Ignores the daily cap</span>
          <span className={state?.ollama.ready ? "chip live" : "chip off"}>
            {state?.ollama.ready ? "Hermes + Gemma ready" : "Models not ready"}
          </span>
        </div>
      </div>

      {!online ? (
        <Banner tone="warn">
          <b>Backend offline.</b> Manual runs need the API on 8471 because the models run server-side.
        </Banner>
      ) : !state?.ollama.ready ? (
        <Banner>
          <b>Ollama is not serving both models.</b> Alice will fall back to heuristics, which still produces a
          scorecard but not a model-written one.
        </Banner>
      ) : null}

      <div className="split">
        <div>
          <div className="panel">
            <span className="eyebrow">Input</span>
            <h3>Listing URL or pasted description</h3>
            <input
              className="inp"
              style={{ marginTop: 12 }}
              placeholder="https://boards.greenhouse.io/…"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <textarea
              className="ta"
              style={{ marginTop: 10 }}
              placeholder="…or paste the full job description here"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="fields two" style={{ marginTop: 12 }}>
              <Field label="Company" hint="Optional — Alice guesses from the text when blank.">
                <input className="inp" value={company} onChange={(e) => setCompany(e.target.value)} />
              </Field>
              <Field label="Role" hint="Optional override for the title.">
                <input className="inp" value={role} onChange={(e) => setRole(e.target.value)} />
              </Field>
            </div>
            <div className="actions">
              <button className="btn btn-primary btn-sm" onClick={start} disabled={running || (!url && !text)}>
                {running ? "Running…" : "Run the pipeline"}
              </button>
              <button className="btn btn-outline btn-sm" onClick={() => setText(SAMPLE_JD)}>
                Use a sample posting
              </button>
              <button className="btn btn-quiet btn-sm" onClick={reset} disabled={!run}>
                Reset
              </button>
            </div>
            {run?.error ? <div className="note" style={{ color: "var(--accent)" }}>{run.error}</div> : null}
          </div>

          <div className="panel">
            <span className="eyebrow">Stages</span>
            <h3>What the engine is doing</h3>
            <div className="pipeline" style={{ marginTop: 12 }}>
              {ORDER.map((name, i) => {
                const stage = reported.get(name);
                const [label, hint] = STAGE_COPY[name];
                const cls = classFor(name);
                return (
                  <div className={`stage ${cls}`} key={name}>
                    <span className="bead">{cls === "done" ? "✓" : cls === "fail" ? "×" : i + 1}</span>
                    <div>
                      <b>{label}</b>
                      <span>{stage?.detail || hint}</span>
                    </div>
                    <span className="small">
                      {stage ? stage.state : cls === "run" ? "working" : "waiting"}
                    </span>
                  </div>
                );
              })}
            </div>
            {run?.done ? (
              <div className="note">
                Finished as <b>{run.outcome ?? "unknown"}</b>.{" "}
                {run.outcome === "BACKLOG"
                  ? "It cleared both gates and is queued for the next release."
                  : run.outcome === "NEEDS_REVIEW"
                    ? "Size or pay was unknown, so it is held rather than guessed."
                    : "It did not clear a gate — the reason is on the failing stage above."}
              </div>
            ) : null}
          </div>
        </div>

        <div>
          <div className="panel">
            <span className="eyebrow">Result</span>
            <h3>{job ? job.title : "Nothing scored yet"}</h3>
            {job ? (
              <>
                <div className="meta" style={{ marginTop: 8 }}>
                  <span>{job.company}</span>
                  <span>{job.pay}</span>
                  <span>{job.size}</span>
                  <span>{job.international ? "Hires internationally" : "Location unstated"}</span>
                </div>
                <div className="scorerow">
                  {(
                    [
                      ["Skills", job.scores.skills],
                      ["Experience", job.scores.experience],
                      ["Location", job.scores.location],
                      ["Trajectory", job.scores.trajectory],
                      ["Culture", job.scores.culture],
                    ] as [string, number][]
                  ).map(([label, value]) => (
                    <div key={label}>
                      <b>{value.toFixed(1)}</b>
                      <span>{label}</span>
                    </div>
                  ))}
                </div>
                <p className="small">
                  Composite{" "}
                  <b style={{ color: "var(--forest)" }}>{job.scores.composite.toFixed(2)}</b>
                  {job.scores.composite >= 3.5 ? " · above the 3.5 threshold" : " · below the 3.5 threshold"}
                </p>
                {job.need.length ? (
                  <>
                    <span className="eyebrow">What they need</span>
                    <ul style={{ marginTop: 8, fontSize: 14, color: "var(--ink-2)" }}>
                      {job.need.map((n) => (
                        <li key={n}>{n}</li>
                      ))}
                    </ul>
                  </>
                ) : null}
              </>
            ) : (
              <p className="small" style={{ marginTop: 8 }}>
                Run a listing to see its scorecard, the tailored CV, and the letter Alice would draft. Nothing here
                touches your inbox.
              </p>
            )}
          </div>

          {job ? (
            <>
              <div className="panel">
                <span className="eyebrow">Packet</span>
                <h3>The CV that would be submitted</h3>
                <div className="cv-file">
                  <span>{job.resume.fileName}</span>
                  <span>{job.resume.pending ? "master profile" : "compiled just now"}</span>
                </div>
                <CvSheet resume={job.resume} />
              </div>
              {job.letter.body ? (
                <div className="panel">
                  <span className="eyebrow">Letter</span>
                  <h3>{job.letter.subject}</h3>
                  <p className="small" style={{ marginTop: 10, whiteSpace: "pre-wrap" }}>
                    {job.letter.body}
                  </p>
                  <div className="note">
                    {job.letter.to ? `Addressed to ${job.letter.to}.` : "No public address found."} Send stays a
                    human click in Letters.
                  </div>
                </div>
              ) : null}
            </>
          ) : null}
        </div>
      </div>

      {toast ? <Toast message={toast} /> : null}
    </div>
  );
}
