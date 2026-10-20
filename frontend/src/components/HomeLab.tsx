import { useState } from "react";
import { Link } from "react-router-dom";
import { LightRow } from "./Lights";
import type { CheckResult } from "./Lights";
import { api } from "../lib/api";
import { useAlice } from "../lib/useAlice";

const CORE = [
  { id: "backend", title: "API / UI connection", group: "Core" },
  { id: "hermes", title: "Hermes (scoring)", group: "Models" },
  { id: "gemma", title: "Gemma (writing)", group: "Models" },
  { id: "typst", title: "Typst PDF compiler", group: "Paper" },
  { id: "gmail", title: "Gmail API", group: "Mail" },
];

const BOARDS = [
  { id: "src_remoteok", title: "RemoteOK", group: "Boards" },
  { id: "src_remotive", title: "Remotive", group: "Boards" },
  { id: "src_arbeitnow", title: "Arbeitnow", group: "Boards" },
  { id: "src_himalayas", title: "Himalayas", group: "Boards" },
  { id: "src_wwr", title: "We Work Remotely", group: "Boards" },
  { id: "src_hnhiring", title: "HN Who's Hiring", group: "Boards" },
  { id: "src_ats_boards", title: "Greenhouse / Lever / Ashby", group: "Boards" },
  { id: "jobspy", title: "JobSpy (LinkedIn / Indeed)", group: "Boards" },
];

const PREVIEW = [...CORE, ...BOARDS];

export default function HomeLab() {
  const { online } = useAlice();
  const [rows, setRows] = useState<CheckResult[]>(
    PREVIEW.map((p) => ({ ...p, status: "idle", detail: "Not run" })),
  );
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    try {
      const res = await api.runDiagnostics(PREVIEW.map((p) => p.id));
      const byId = Object.fromEntries(res.results.map((r) => [r.id, r]));
      setRows(PREVIEW.map((p) => byId[p.id] ?? { ...p, status: "fail", detail: "no result" }));
    } catch (err) {
      setRows(PREVIEW.map((p) => ({ ...p, status: "fail", detail: (err as Error).message })));
    } finally {
      setBusy(false);
    }
  }

  const coreRows = rows.filter((r) => r.group !== "Boards");
  const boards = rows.filter((r) => r.group === "Boards");
  const boardLeft = boards.filter((_, i) => i % 2 === 0);
  const boardRight = boards.filter((_, i) => i % 2 === 1);
  const ok = rows.filter((r) => r.status === "ok").length;
  const fail = rows.filter((r) => r.status === "fail").length;
  const ran = rows.some((r) => r.status !== "idle");

  return (
    <div className="preview lab-preview">
      <div className="preview-top">
        <div className="dots">
          <i />
          <i />
          <i />
        </div>
        <span className="small">Live diagnostics</span>
      </div>
      <div className="lab-grid">
        <p className="eyebrow lab-col-label">Core</p>
        <p className="eyebrow lab-col-label lab-boards-label">Boards</p>
        <div className="lamp-list compact lab-core-col">
          {coreRows.map((row) => (
            <LightRow
              key={row.id}
              title={row.title}
              status={busy ? "run" : row.status}
              detail={row.detail}
              running={busy}
              dense
            />
          ))}
        </div>
        <div className="lamp-list compact lab-board-a">
          {boardLeft.map((row) => (
            <LightRow
              key={row.id}
              title={row.title}
              status={busy ? "run" : row.status}
              detail={row.detail}
              running={busy}
              dense
            />
          ))}
        </div>
        <div className="lamp-list compact lab-board-b">
          {boardRight.map((row) => (
            <LightRow
              key={row.id}
              title={row.title}
              status={busy ? "run" : row.status}
              detail={row.detail}
              running={busy}
              dense
            />
          ))}
        </div>
      </div>
      <div className="lab-foot">
        <div className="actions">
          <button className="btn btn-primary btn-sm" onClick={run} disabled={!online || busy}>
            {busy ? "Probing…" : "Run tests"}
          </button>
          <Link className="btn btn-outline btn-sm" to="/lab">
            Full lab
          </Link>
        </div>
        <p className="small lab-tally">
          {!online
            ? "Engine offline — start 8471"
            : busy
              ? "Probing every board…"
              : ran
                ? `${ok} green · ${fail} red`
                : `${PREVIEW.length} checks`}
        </p>
      </div>
    </div>
  );
}
