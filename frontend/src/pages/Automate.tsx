import { useEffect, useState } from "react";
import { Banner, Toast, Toggle } from "../components/ui";
import { useAlice } from "../lib/useAlice";
import { api } from "../lib/api";

type Source = { id: string; name: string; enabled: boolean; paused: boolean };

export default function Automate() {
  const { state, online, refresh } = useAlice();
  const [sources, setSources] = useState<Source[]>([]);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    if (!online) return;
    api
      .sources()
      .then((res) => setSources(res.sources))
      .catch(() => setSources([]));
  }, [online, state?.running]);

  function say(message: string) {
    setToast(message);
    setTimeout(() => setToast(""), 3200);
  }

  async function toggleLive(next: boolean) {
    if (!online) return say("Backend offline");
    try {
      await api.setLiveCrawl(next);
      refresh();
      say(next ? "Live crawl on — Run now will hit the boards" : "Live crawl off");
    } catch (err) {
      say((err as Error).message);
    }
  }

  async function runNow() {
    setBusy(true);
    try {
      await api.runPipeline();
      refresh();
      say("Pipeline started");
    } catch (err) {
      say((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function stopNow() {
    setBusy(true);
    try {
      await api.stopPipeline();
      refresh();
      say("Stopped. The listing already in Hermes may finish, then Alice halts.");
    } catch (err) {
      say((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function flipSource(src: Source) {
    try {
      const res = await api.setSource(src.id, !src.enabled);
      setSources(res.sources);
    } catch (err) {
      say((err as Error).message);
    }
  }

  const live = Boolean(state?.liveCrawl);
  const counts = state?.counts ?? {};
  const ollama = state?.ollama;
  const armed = sources.filter((s) => s.enabled).length;

  return (
    <div className="wrap section" style={{ paddingTop: 40 }}>
      <div className="ws-head">
        <div>
          <span className="eyebrow">Automate</span>
          <h2>Run when you are ready. Nothing is on a clock.</h2>
          <p>
            Live crawl is the network switch. Run now is the only trigger. Source toggles here are the same list as
            Setup — they persist in SQLite and are what the pipeline reads.
          </p>
        </div>
        <div className="chips">
          <span className={live ? "chip live" : "chip off"}>{live ? "Live crawl on" : "Live crawl off"}</span>
          <span className="chip">{armed} sources armed</span>
          {state?.running ? <span className="chip live">Running</span> : null}
        </div>
      </div>

      {!online ? (
        <Banner tone="warn">
          <b>Backend offline.</b> Start the API on 8471 first.
        </Banner>
      ) : null}

      <div className="stats-4">
        <div className="stat">
          <b>{counts.READY ?? 0}</b>
          <span>Released and ready</span>
        </div>
        <div className="stat">
          <b>{counts.NEEDS_REVIEW ?? 0}</b>
          <span>Held for review</span>
        </div>
        <div className="stat">
          <b>{state?.jdBudget ?? "—"}</b>
          <span>Description fetches left today</span>
        </div>
        <div className="stat">
          <b>$0.00</b>
          <span>Inference spend, lifetime</span>
        </div>
      </div>

      <div className="split">
        <div>
          <div className="panel">
            <span className="eyebrow">Run</span>
            <h3>Live crawl + Run now</h3>
            <p className="small" style={{ margin: "8px 0 16px" }}>
              Off means Alice never touches a job board. On means the next press of Run now pulls from every armed
              source below.
            </p>
            <Toggle
              title="Pull real listings"
              note="Persisted in SQLite."
              on={live}
              onChange={toggleLive}
              locked={!online}
            />
            <div className="actions">
              {state?.running ? (
                <button className="btn btn-accent" disabled={!online || busy} onClick={stopNow}>
                  Stop
                </button>
              ) : (
                <button className="btn btn-primary" disabled={!online || !live || busy} onClick={runNow}>
                  Run now
                </button>
              )}
            </div>
            {state?.running ? (
              <div className="note">
                Crawling and scoring is slow. Stop clears the lock and skips remaining listings after the one in
                flight.
              </div>
            ) : !live ? (
              <div className="note">Turn live crawl on before Run now. Manual run and seeding do not need it.</div>
            ) : null}
          </div>

          <div className="panel">
            <span className="eyebrow">Pipeline state</span>
            <h3>Where the jobs are</h3>
            <div className="timeline" style={{ marginTop: 10 }}>
              {[
                ["BACKLOG", "Cleared both gates, waiting for a slot"],
                ["READY", "Released to the briefing board"],
                ["NEEDS_REVIEW", "Size or pay unknown"],
                ["ARCHIVED", "Failed a gate"],
                ["APPLIED", "You opened the posting"],
                ["SENT", "A letter went out"],
                ["SKIPPED", "You passed"],
              ].map(([key, body]) => (
                <div className="tl" key={key}>
                  <time>{counts[key] ?? 0}</time>
                  <div>
                    <b>{key.replace("_", " ").toLowerCase()}</b>
                    <span>{body}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div>
          <div className="panel">
            <span className="eyebrow">Sources</span>
            <h3>Boards Alice will call</h3>
            <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
              {sources.map((s) => (
                <div className={`stage ${s.paused ? "fail" : s.enabled ? "done" : ""}`} key={s.id}>
                  <span className="bead">{s.paused ? "!" : s.enabled ? "✓" : "○"}</span>
                  <div>
                    <b>{s.name}</b>
                    <span>
                      {s.paused ? "Circuit open" : s.enabled ? "Armed" : "Off — skipped on Run now"}
                    </span>
                  </div>
                  <button type="button" className={`switch${s.enabled ? " on" : ""}`} aria-label={s.name} onClick={() => flipSource(s)}>
                    <i />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <span className="eyebrow">Engine</span>
            <h3>Local models</h3>
            <dl className="kv" style={{ marginTop: 12 }}>
              <dt>Ollama</dt>
              <dd>{ollama?.reachable ? "Reachable" : "Not responding"}</dd>
              <dt>Scoring</dt>
              <dd>{ollama?.scoring ?? "—"}</dd>
              <dt>Writing</dt>
              <dd>{ollama?.writing ?? "—"}</dd>
              <dt>Gmail</dt>
              <dd>{state?.gmail ? "Connected" : "Not connected"}</dd>
            </dl>
          </div>
        </div>
      </div>

      {toast ? <Toast message={toast} /> : null}
    </div>
  );
}
