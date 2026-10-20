import { Link } from "react-router-dom";

export default function About() {
  return (
    <>
      <section className="about-hero">
        <div className="wrap">
          <span className="eyebrow">About</span>
          <h1>Alice stands for Assisted Local Inference Career Engine. Every word in that name is load-bearing.</h1>
        </div>
      </section>

      <section className="section">
        <div className="wrap split">
          <div className="prose">
            <p>
              <b>Assisted</b>, because the job search stays yours. Alice reads, ranks, and drafts. You decide what
              gets applied to and what gets sent. There is no version of this product where a machine emails a
              founder in your name while you sleep.
            </p>
            <p>
              <b>Local</b>, because the alternative is paying a per-token bill to have your own resume rewritten
              three hundred times. The models run on the machine in front of you. Your resume, your salary
              expectations, and the companies you are quietly interested in never leave it.
            </p>
            <p>
              <b>Inference</b>, because the useful part is judgement, not scraping. Anyone can pull a thousand
              listings. The work is deciding which nine of them are worth a morning, and writing something to each
              one that sounds like a person who read the posting.
            </p>
            <div className="pull">
              A job search fails from volume, not from difficulty. Fifteen good listings with real paper beats two
              hundred tabs every time.
            </div>
            <p>
              <b>Career Engine</b>, because this is meant to run for months. The ledgers remember what you have
              seen, what you applied to, and which companies already had their turn. Day sixty should feel like day
              one, minus the listings you already handled.
            </p>
            <p>
              I built Alice for my own search first — the constraints in the default config are literally mine:
              teams under twenty, hiring internationally, forty to sixty an hour. They are all editable, and the
              engine underneath does not care what you set them to.
            </p>
          </div>

          <div>
            <div className="panel">
              <span className="eyebrow">Built by</span>
              <h3>Hadi Adnan</h3>
              <p className="small" style={{ marginTop: 8 }}>
                Python and local inference. FastAPI control planes over SQLite, on-device model serving on Apple
                Silicon, and interfaces that stay quiet enough to use every morning.
              </p>
              <div className="actions">
                <Link className="btn btn-outline btn-sm" to="/product">
                  How it works
                </Link>
                <Link className="btn btn-primary btn-sm" to="/setup">
                  Set it up
                </Link>
              </div>
            </div>
            <div className="panel">
              <span className="eyebrow">Principles</span>
              <h3>Four rules the code enforces</h3>
              <dl className="kv" style={{ marginTop: 14 }}>
                <dt>No cloud models</dt>
                <dd>A test fails the build if a hosted endpoint appears in the source.</dd>
                <dt>No unattended sends</dt>
                <dd>Drafts only. The send path needs a human click.</dd>
                <dt>No invented facts</dt>
                <dd>Tailoring is limited to what your master profile already claims.</dd>
                <dt>No fixed port 8000</dt>
                <dd>Alice binds 8471 and refuses to start on 8000.</dd>
              </dl>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
