import type { Job } from "../data/jobs";

export default function JobTile({ job, onOpen }: { job: Job; onOpen: () => void }) {
  return (
    <button className="tile" onClick={onOpen}>
      <span className="co">
        {job.company} · {job.source}
      </span>
      <h3>{job.title}</h3>
      <p className="snip">{job.snippet}</p>
      <div className="meta">
        <span>{job.pay}</span>
        <span>{job.size}</span>
        <span>{job.international ? "Worldwide" : job.location}</span>
      </div>
      <div className="tile-foot">
        <span className="score">
          {job.scores.composite.toFixed(2)}
          <small>/ 5</small>
        </span>
        <span className="cv-flag">{job.letter.gmailDraft ? "CV + draft ready" : "CV ready · apply only"}</span>
      </div>
    </button>
  );
}
