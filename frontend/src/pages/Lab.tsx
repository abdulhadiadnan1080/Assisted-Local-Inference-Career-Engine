import { useEffect, useMemo, useState } from "react";
import { Banner, Toast } from "../components/ui";
import { LightRow } from "../components/Lights";
import type { CheckResult, LightStatus } from "../components/Lights";
import { api } from "../lib/api";
import { useAlice } from "../lib/useAlice";

export default function Lab() {
  const { online } = useAlice();
  const [rows, setRows] = useState<CheckResult[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [toast, setToast] = useState("");

  useEffect(() => {
    if (!online) return;
    api
      .diagnostics()
      .then((res) =>
        setRows(res.checks.map((c) => ({ ...c, status: "idle" as const, detail: "Not run" }))),
      )
      .catch(() => undefined);
  }, [online]);

  const grouped = useMemo(() => {
    const map = new Map<string, CheckResult[]>();
    for (const row of rows) {
      const list = map.get(row.group) ?? [];
      list.push(row);
      map.set(row.group, list);
    }
    return [...map.entries()];
  }, [rows]);

  const summary = useMemo(() => {
    const ok = rows.filter((r) => r.status === "ok").length;
    const fail = rows.filter((r) => r.status === "fail").length;
    const warn = rows.filter((r) => r.status === "warn").length;
    return { ok, fail, warn, total: rows.length };
  }, [rows]);

  function upsert(result: CheckResult) {
    setRows((current) => {
      const rest = current.filter((r) => r.id !== result.id);
      return [...rest, result].sort((a, b) => a.group.localeCompare(b.group) || a.title.localeCompare(b.title));
    });
  }

  async function runAll() {
    if (!online) return;
    setBusy("all");
    try {
      const res = await api.runDiagnostics();
      setRows(res.results);
      setToast(`${res.summary.ok} green · ${res.summary.warn} amber · ${res.summary.fail} red`);
    } catch (err) {
      setToast((err as Error).message);
    } finally {
      setBusy(null);
      setTimeout(() => setToast(""), 3200);
    }
  }

  async function runOne(id: string) {
    setBusy(id);
    try {
      const res = await api.runCheck(id);
      upsert(res.result);
    } catch (err) {
      upsert({ id, title: id, group: "Core", status: "fail", detail: (err as Error).message });
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="wrap section" style={{ paddingTop: 40 }}>
      <div className="ws-head">
        <div>
          <span className="eyebrow">Lab</span>
          <h2>Every moving part, one light each</h2>
          <p>
            This is not a mock. Each button calls the backend and probes the real binary, model, board, or file.
            Amber means reachable but incomplete. Red means that path cannot run today.
          </p>
        </div>
        <div className="chips">
          {summary.total ? (
            <>
              <span className="chip live">{summary.ok} green</span>
              <span className="chip">{summary.warn} amber</span>
              <span className="chip off">{summary.fail} red</span>
            </>
          ) : (
            <span className="chip">Not run yet</span>
          )}
        </div>
      </div>

      {!online ? (
        <Banner tone="warn">
          <b>Backend offline.</b> Start the API on 8471 before these probes can run.
        </Banner>
      ) : null}

      <div className="actions" style={{ marginBottom: 22 }}>
        <button className="btn btn-primary" onClick={runAll} disabled={!online || busy === "all"}>
          {busy === "all" ? "Running every probe…" : "Run every test"}
        </button>
      </div>

      {grouped.length === 0 ? (
        <div className="empty">
          <h3>Nothing probed yet</h3>
          <p>Run every test, or open this page after using the button on the home screen.</p>
        </div>
      ) : (
        grouped.map(([group, list]) => (
          <section className="setup-card" key={group}>
            <header>
              <h3>{group}</h3>
            </header>
            <div className="lamp-list">
              {list.map((row) => (
                <LightRow
                  key={row.id}
                  title={row.title}
                  status={(busy === row.id ? "run" : row.status) as LightStatus}
                  detail={row.detail}
                  running={busy === row.id}
                  onRun={() => runOne(row.id)}
                />
              ))}
            </div>
          </section>
        ))
      )}

      {toast ? <Toast message={toast} /> : null}
    </div>
  );
}
