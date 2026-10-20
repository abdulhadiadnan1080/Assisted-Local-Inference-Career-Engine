import type { Resume } from "../data/jobs";
import { useAlice } from "../lib/useAlice";

export default function CvSheet({ resume }: { resume: Resume }) {
  const { state } = useAlice();
  const name = state?.candidate.name || "Hadi Adnan";

  return (
    <article className="cv">
      <header>
        <strong>{name}</strong>
        <span>{resume.headline}</span>
      </header>
      <hr />
      <p>{resume.summary}</p>
      <h5>Skills</h5>
      <p>{resume.skills.join(" · ")}</p>
      <h5>Selected work</h5>
      <ul>
        {resume.bullets.map((b, i) => (
          <li key={`${i}-${b.slice(0, 24)}`}>{b}</li>
        ))}
      </ul>
      <h5>Grounding</h5>
      <p style={{ color: "var(--faint)" }}>
        {resume.pending
          ? "Not tailored yet — this is the master profile as written. Tailoring runs when the job reaches Gate B."
          : "Every line above is drawn from the master profile. Nothing was invented to match the posting."}
      </p>
    </article>
  );
}
