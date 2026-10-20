import { useEffect } from "react";
import type { Job } from "../data/jobs";
import CvSheet from "./CvSheet";

export default function JobDrawer({
  job,
  live,
  onClose,
  onApply,
  onSkip,
}: {
  job: Job;
  live?: boolean;
  onClose: () => void;
  onApply?: () => void;
  onSkip?: () => void;
}) {
  const canSend = Boolean(job.letter.to && job.letter.gmailDraft);
  const applied = job.status === "applied" || job.status === "sent" || job.rawStatus === "BOTH";

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="drawer-bg" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div>
          <section className="panel">
            <span className="eyebrow">
              {job.company} · {job.posted}
            </span>
            <h3>{job.title}</h3>
            <div className="meta">
              <span>{job.pay}</span>
              <span>{job.size}</span>
              <span>{job.source}</span>
              <span>{job.international ? "Hires internationally" : job.location || "Location unstated"}</span>
              {applied ? <span>Applied</span> : null}
            </div>
            <p className="small" style={{ marginTop: 14, whiteSpace: "pre-wrap" }}>
              {job.description.slice(0, 1800)}
            </p>
            <div className="scorerow">
              <div>
                <b>{job.scores.skills.toFixed(1)}</b>
                <span>Skills</span>
              </div>
              <div>
                <b>{job.scores.experience.toFixed(1)}</b>
                <span>Experience</span>
              </div>
              <div>
                <b>{job.scores.location.toFixed(1)}</b>
                <span>Location</span>
              </div>
              <div>
                <b>{job.scores.trajectory.toFixed(1)}</b>
                <span>Trajectory</span>
              </div>
              <div>
                <b>{job.scores.culture.toFixed(1)}</b>
                <span>Culture</span>
              </div>
            </div>
            <p className="small">
              Composite <b style={{ color: "var(--forest)", fontSize: 15 }}>{job.scores.composite.toFixed(2)}</b> of 5
            </p>
          </section>

          <section className="panel">
            <span className="eyebrow">What they actually need</span>
            {job.need.length ? (
              <ul style={{ marginTop: 12, color: "var(--ink-2)", fontSize: 14 }}>
                {job.need.map((n) => (
                  <li key={n} style={{ marginBottom: 6 }}>
                    {n}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="small" style={{ marginTop: 10 }}>
                The scorer did not extract hiring problems for this listing.
              </p>
            )}
            <p className="small" style={{ marginTop: 14 }}>
              {job.letter.to
                ? `Poster found · ${job.letter.toName ?? "Hiring"} · ${job.letter.to}`
                : "No public address on this posting — Apply is the only route."}
            </p>
            <div className="actions">
              <button className="btn btn-primary btn-sm" onClick={onApply}>
                {applied ? "Open posting again" : "Apply on the official posting"}
              </button>
              <button className="btn btn-outline btn-sm" disabled={!canSend} title={canSend ? "" : "No Gmail draft"}>
                {canSend ? "Draft is in Letters" : "No letter to send"}
              </button>
              {onSkip ? (
                <button className="btn btn-quiet btn-sm" onClick={onSkip} disabled={!live}>
                  Skip
                </button>
              ) : null}
              <button className="btn btn-quiet btn-sm" onClick={onClose}>
                Close
              </button>
            </div>
            <div className="note">Send stays a human click, and it lives in Letters so you can edit first.</div>
          </section>
        </div>

        <section className="panel">
          <span className="eyebrow">Attached packet</span>
          <h3>CV being submitted</h3>
          <div className="cv-file">
            <span>{job.resume.fileName}</span>
            <span>{job.resume.pending ? "master profile, not yet tailored" : `tailored for ${job.company}`}</span>
          </div>
          <CvSheet resume={job.resume} />
          {job.pdfUrl ? (
            <div className="actions">
              <a className="btn btn-outline btn-sm" href={job.pdfUrl} target="_blank" rel="noreferrer">
                Open compiled PDF
              </a>
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}
