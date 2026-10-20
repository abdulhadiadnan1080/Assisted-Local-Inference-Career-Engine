import { useEffect, useMemo, useState } from "react";
import type { Job } from "../data/jobs";
import CvSheet from "../components/CvSheet";
import { Banner, Toast } from "../components/ui";
import { useAlice, useJobs } from "../lib/useAlice";
import { api } from "../lib/api";

export default function Letters() {
  const { online, state } = useAlice();
  const { jobs, source, reload } = useJobs("briefing");
  const letters = useMemo(() => jobs.filter((j) => j.letter.body), [jobs]);

  const [activeId, setActiveId] = useState<string | null>(null);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");

  const active: Job | null = letters.find((j) => j.id === activeId) ?? letters[0] ?? null;

  useEffect(() => {
    if (!active) return;
    if (active.id === activeId && dirty) return;
    setActiveId(active.id);
    setSubject(active.letter.subject);
    setBody(active.letter.body);
    setDirty(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active?.id, letters.length]);

  function say(message: string) {
    setToast(message);
    setTimeout(() => setToast(""), 3000);
  }

  function select(job: Job) {
    setActiveId(job.id);
    setSubject(job.letter.subject);
    setBody(job.letter.body);
    setDirty(false);
  }

  async function save() {
    if (!active || source !== "live") return say("Sample deck — nothing to save");
    setBusy(true);
    try {
      await api.saveDraft(active.id, subject, body);
      setDirty(false);
      reload();
      say("Draft saved to SQLite");
    } catch (err) {
      say((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function send() {
    if (!active) return;
    if (source !== "live") return say("Sample deck — send is disabled");
    setBusy(true);
    try {
      await api.send(active.id);
      reload();
      say(`Sent to ${active.letter.to}`);
    } catch (err) {
      say((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const canSend = Boolean(active?.letter.to && active?.letter.gmailDraft && state?.gmail);
  const words = body.trim().split(/\s+/).filter(Boolean).length;

  return (
    <>
      <div className="ws-head">
        <div>
          <span className="eyebrow">Letters</span>
          <h2>Every draft, waiting on you</h2>
          <p>
            Alice writes five to eight sentences grounded in the posting, attaches the tailored CV, and stops. Edit
            anything you like — nothing leaves until you press send.
          </p>
        </div>
        <div className="chips">
          <span className="chip live">{letters.filter((j) => j.letter.gmailDraft).length} in Gmail</span>
          <span className="chip off">{letters.filter((j) => !j.letter.to).length} apply only</span>
        </div>
      </div>

      {!online ? (
        <Banner tone="warn">
          <b>Backend offline.</b> These are sample letters. Nothing here can be saved or sent.
        </Banner>
      ) : !state?.gmail ? (
        <Banner>
          <b>Gmail is not connected.</b> Drafts are written to SQLite and shown here, but the send button stays
          disabled until OAuth credentials are in place. Add them under Setup.
        </Banner>
      ) : null}

      {!letters.length ? (
        <div className="empty">
          <h3>No drafts yet</h3>
          <p>Letters appear once a listing clears Gate B and the writing model has run.</p>
        </div>
      ) : (
        <div className="inbox">
          <div className="list">
            {letters.map((job) => (
              <button
                key={job.id}
                className={`row${job.id === active?.id ? " on" : ""}`}
                onClick={() => select(job)}
              >
                <b>{job.company}</b>
                <div>{job.letter.subject}</div>
                <small>
                  {job.letter.to ?? "No public address"} ·{" "}
                  {job.letter.sent ? "Sent" : job.letter.gmailDraft ? "Gmail draft" : "Local only"}
                </small>
              </button>
            ))}
          </div>

          {active ? (
            <div>
              <div className="letter">
                <div className="field-line">
                  <span>To</span>
                  <b style={{ color: "var(--ink)" }}>
                    {active.letter.toName ?? "—"}{" "}
                    {active.letter.to ? `<${active.letter.to}>` : "(no address found)"}
                  </b>
                </div>
                <input
                  value={subject}
                  onChange={(e) => {
                    setSubject(e.target.value);
                    setDirty(true);
                  }}
                />
                <textarea
                  value={body}
                  onChange={(e) => {
                    setBody(e.target.value);
                    setDirty(true);
                  }}
                />
                <div className="field-line" style={{ borderBottom: 0, paddingBottom: 0 }}>
                  <span>{words} words</span>
                  <span>·</span>
                  <span>Attachment: {active.resume.fileName}</span>
                  {dirty ? <span style={{ color: "var(--accent)" }}>· unsaved</span> : null}
                </div>
                <div className="actions">
                  <button className="btn btn-primary btn-sm" disabled={!canSend || busy} onClick={send}>
                    Send via Gmail
                  </button>
                  <button className="btn btn-outline btn-sm" disabled={!dirty || busy} onClick={save}>
                    Save edits
                  </button>
                  <a className="btn btn-outline btn-sm" href={active.applyUrl} target="_blank" rel="noreferrer">
                    Open apply page
                  </a>
                  <button
                    className="btn btn-quiet btn-sm"
                    onClick={() => {
                      setBody(active.letter.body);
                      setSubject(active.letter.subject);
                      setDirty(false);
                    }}
                  >
                    Revert
                  </button>
                </div>
                {!active.letter.to ? (
                  <div className="note">
                    No public address on this posting, so there is nothing to send. Apply on the official page
                    instead.
                  </div>
                ) : null}
              </div>

              <div className="panel" style={{ marginTop: 16 }}>
                <span className="eyebrow">Attached packet</span>
                <h3>CV going out with this letter</h3>
                <CvSheet resume={active.resume} />
              </div>
            </div>
          ) : null}
        </div>
      )}

      {toast ? <Toast message={toast} /> : null}
    </>
  );
}
