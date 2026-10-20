import { Link } from "react-router-dom";

const stages = [
  ["Discover", "Public boards, ATS feeds, hiring threads. Cached per source with jitter between calls."],
  ["Snippet scan", "A cheap regex pass drops the obviously wrong before anything expensive runs."],
  ["Fetch JD", "Only survivors get their full description pulled, and only within the daily fetch cap."],
  ["Gate A", "Headcount, international hiring, pay band. Fails are archived with a reason attached."],
  ["Gate B", "Hermes scores five dimensions against your profile and returns a composite."],
  ["Poster", "Looks for a named human and a public address. Absent is fine — Apply still works."],
  ["Tailor", "Gemma rewrites the CV from your master profile. Facts only, no invented tools."],
  ["Draft", "A short letter lands in Gmail as a draft. Send is never called by the machine."],
];

export default function Product() {
  return (
    <>
      <section className="about-hero">
        <div className="wrap">
          <span className="eyebrow">How it works</span>
          <h1>Eight stages, each one cheap enough to run every morning.</h1>
          <p className="lead" style={{ marginTop: 18, maxWidth: "40em" }}>
            Alice is deliberately staged so the expensive work happens last. A listing has to earn its way to the
            model, and the model has to earn the listing a slot.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="wrap split">
          <div className="pipeline">
            {stages.map(([name, body], i) => (
              <div className="stage done" key={name}>
                <span className="bead">{i + 1}</span>
                <div>
                  <b>{name}</b>
                  <span>{body}</span>
                </div>
              </div>
            ))}
          </div>
          <div>
            <div className="panel">
              <span className="eyebrow">Cost model</span>
              <h3>Why this stays free</h3>
              <p className="small" style={{ marginTop: 8 }}>
                Every model call happens on your hardware through Ollama. There is no metered API in the loop, so a
                heavy day costs you electricity and nothing else. The two models never sit in memory together —
                Alice unloads one before loading the other, which is what makes a 16GB machine viable.
              </p>
              <dl className="kv" style={{ marginTop: 16 }}>
                <dt>Scoring model</dt>
                <dd>Hermes 3 · 8B</dd>
                <dt>Writing model</dt>
                <dd>Gemma 2 · 9B</dd>
                <dt>Runtime</dt>
                <dd>Ollama on Apple Silicon</dd>
                <dt>Storage</dt>
                <dd>Local SQLite</dd>
                <dt>Cloud calls</dt>
                <dd>None, enforced by test</dd>
              </dl>
            </div>
            <div className="panel">
              <span className="eyebrow">Guardrails</span>
              <h3>What Alice refuses to do</h3>
              <ul style={{ marginTop: 10, color: "var(--muted)", fontSize: 14 }}>
                <li>Submit an application on your behalf.</li>
                <li>Send an email without a click.</li>
                <li>Guess a headcount or a salary to make a listing pass.</li>
                <li>Put a skill on your CV that is not in your master profile.</li>
                <li>Keep hammering a board that returned 429.</li>
              </ul>
              <div className="actions">
                <Link className="btn btn-primary btn-sm" to="/manual">
                  Watch it run on one listing
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
