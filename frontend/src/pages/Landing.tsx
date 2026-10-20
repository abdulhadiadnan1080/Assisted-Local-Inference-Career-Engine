import { Link } from "react-router-dom";
import HomeLab from "../components/HomeLab";

const weights = [
  { label: "Skills fit", value: 35 },
  { label: "Experience", value: 25 },
  { label: "Location / pay", value: 15 },
  { label: "Trajectory", value: 15 },
  { label: "Culture", value: 10 },
];

export default function Landing() {
  return (
    <>
      <section className="hero">
        <div className="hero-glow" />
        <div className="hero-glow two" />
        <div className="wrap hero-grid">
          <div>
            <span className="eyebrow">Assisted Local Inference Career Engine</span>
            <h1>
              She reads the boards. You keep the <em>click</em>.
            </h1>
            <p className="lead">
              Alice crawls the small remote teams that actually hire internationally, filters them against hard
              rules, scores what is left with local models, and hands you a tailored CV and a drafted letter for
              every single one. No cloud model calls. No autopilot applications.
            </p>
            <div className="hero-actions">
              <Link className="btn btn-primary" to="/app/briefing">
                Open today’s briefing
              </Link>
              <Link className="btn btn-outline" to="/lab">
                Open the lab
              </Link>
            </div>
            <div className="hero-facts">
              <div>
                <strong>15</strong>
                <span>released per day, no more</span>
              </div>
              <div>
                <strong>$0</strong>
                <span>inference cost per run</span>
              </div>
              <div>
                <strong>2</strong>
                <span>local models, one hot at a time</span>
              </div>
              <div>
                <strong>0</strong>
                <span>emails sent without your click</span>
              </div>
            </div>
          </div>

          <HomeLab />
        </div>
      </section>

      <section className="section rule-band">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">Why it exists</span>
            <h2>Job boards optimise for volume. Alice optimises for the fifteen you would actually take.</h2>
            <p>
              Applying is not the hard part. Reading three hundred listings to find the six that pay properly, hire
              across borders, and are small enough that your work shows — that is the hard part. Alice does the
              reading.
            </p>
          </div>
          <div className="cards-3">
            {[
              {
                mark: "01",
                title: "Runs on your laptop",
                body: "Hermes 3 and Gemma 2 through Ollama on Apple Silicon. One model hot at a time so a 16GB machine survives the day. Nothing leaves the device.",
              },
              {
                mark: "02",
                title: "Two gates, not one blob",
                body: "Hard parameters archive a listing outright. Only survivors reach the scoring rubric, so the model spends its time on jobs that already qualify.",
              },
              {
                mark: "03",
                title: "Paper, not links",
                body: "Each release ships a tailored CV compiled from your master profile and a letter grounded in the posting. No invented metrics, no borrowed tools.",
              },
              {
                mark: "04",
                title: "Human at both gates",
                body: "Apply opens the official posting in your browser. Send stays a button you press. Alice writes the draft into Gmail and stops there.",
              },
              {
                mark: "05",
                title: "Nothing repeats",
                body: "A seen ledger and a shown ledger mean a listing never takes a second slot, and the same company never floods a single morning.",
              },
              {
                mark: "06",
                title: "Polite by construction",
                body: "Per-source caps, jitter between requests, and a circuit breaker that parks a board for hours after a 429. Alice is a guest on these sites.",
              },
            ].map((f) => (
              <article className="feature" key={f.mark}>
                <span className="mark">{f.mark}</span>
                <h3>{f.title}</h3>
                <p>{f.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section rule-band">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">A day in four moves</span>
            <h2>Crawl, gate, score, paper.</h2>
          </div>
          <div className="steps">
            {[
              {
                n: "Step one",
                h: "Crawl",
                p: "Public boards, company ATS feeds, and the monthly hiring threads. Cached, jittered, capped.",
              },
              {
                n: "Step two",
                h: "Gate A",
                p: "Headcount, international hiring, pay band. Unknowns wait in Intake instead of guessing.",
              },
              {
                n: "Step three",
                h: "Gate B",
                p: "Five dimensions scored locally. Composite below your threshold never reaches the briefing.",
              },
              {
                n: "Step four",
                h: "Release",
                p: "Fifteen tiles, each with a tailored CV, a drafted letter, and the poster if one is findable.",
              },
            ].map((s) => (
              <div className="step" key={s.h}>
                <span className="n">{s.n}</span>
                <h4>{s.h}</h4>
                <p>{s.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section rule-band">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">The filters</span>
            <h2>What gets through, and what it costs a listing to fail.</h2>
          </div>
          <div className="gates">
            <div className="gate a">
              <span className="eyebrow">Gate A · hard parameters</span>
              <h3>Pass or archive. No negotiation.</h3>
              <ul>
                <li>Fewer than twenty people at the company.</li>
                <li>Hires internationally, or says worldwide outright.</li>
                <li>Pay lands between $40 and $60 an hour.</li>
                <li>Missing facts mean review, never a generous assumption.</li>
              </ul>
            </div>
            <div className="gate b">
              <span className="eyebrow">Gate B · scoring rubric</span>
              <h3>Five dimensions, one composite, your threshold.</h3>
              <div className="weightbars">
                {weights.map((w) => (
                  <div className="weightbar" key={w.label}>
                    <span>{w.label}</span>
                    <span className="track">
                      <span className="fill" style={{ width: `${w.value * 3.2}%` }} />
                    </span>
                    <b>{w.value}%</b>
                  </div>
                ))}
              </div>
              <p className="small" style={{ marginTop: 14 }}>
                Default release threshold is 3.5 of 5. Raise it on a good week, lower it when you want volume.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="cta-band">
            <div>
              <h2>Tell Alice who you are. She reads the rest.</h2>
              <p>
                Setup takes one pass: your resume, your email, the countries you can work from, the pay band you
                will accept, and how hard the rubric should judge. Then open the briefing tomorrow morning.
              </p>
            </div>
            <div className="hero-actions" style={{ marginTop: 0 }}>
              <Link className="btn btn-accent" to="/setup">
                Start setup
              </Link>
              <Link className="btn btn-outline" to="/manual">
                Try one listing first
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
