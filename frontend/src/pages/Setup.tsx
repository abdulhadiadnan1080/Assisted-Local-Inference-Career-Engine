import { useEffect, useMemo, useState } from "react";
import { Banner, Field, TagInput, Toast, Toggle } from "../components/ui";
import { useAlice } from "../lib/useAlice";
import { api } from "../lib/api";

type Weights = {
  skills: number;
  experience: number;
  location: number;
  trajectory: number;
  culture: number;
};

const SOURCE_OPTIONS = [
  ["remoteok", "RemoteOK"],
  ["remotive", "Remotive"],
  ["arbeitnow", "Arbeitnow"],
  ["himalayas", "Himalayas"],
  ["wwr", "We Work Remotely"],
  ["hnhiring", "HN Who's Hiring"],
  ["ats_boards", "Greenhouse / Lever / Ashby"],
  ["jobspy", "LinkedIn & Indeed (JobSpy)"],
] as const;

const sections = [
  ["identity", "You"],
  ["resume", "Master profile"],
  ["email", "Email & Gmail"],
  ["geography", "Geography"],
  ["role", "Role & pay"],
  ["scoring", "Scoring"],
  ["engine", "Models & boards"],
  ["prompts", "System prompts"],
  ["cadence", "Politeness cap"],
];

const weightLabels: Record<keyof Weights, string> = {
  skills: "Skills fit",
  experience: "Experience",
  location: "Location / pay",
  trajectory: "Trajectory",
  culture: "Culture",
};

export default function Setup() {
  const { online, state } = useAlice();
  const [name, setName] = useState("Hadi Adnan");
  const [email, setEmail] = useState("hadi@example.com");
  const [title, setTitle] = useState("Python & local inference engineer");
  const [links, setLinks] = useState<string[]>(["github.com/hadiadnan", "linkedin.com/in/hadiadnan"]);

  const [resumeName, setResumeName] = useState("Hadi-Adnan-master.pdf");
  const [profile, setProfile] = useState(
    "Python, FastAPI, SQLite, TypeScript, MLX. Shipped a local inference control plane on Apple Silicon. Built operator dashboards and Typst-compiled PDF pipelines for small remote teams.",
  );
  const [skills, setSkills] = useState<string[]>(["Python", "FastAPI", "SQLite", "TypeScript", "MLX", "Ollama"]);
  const [neverClaim, setNeverClaim] = useState<string[]>(["Kubernetes", "Salesforce"]);

  const [gmailAddress, setGmailAddress] = useState("hadi@example.com");
  const [credsPath, setCredsPath] = useState("~/.alice/credentials.json");
  const [signature, setSignature] = useState("Hadi Adnan");
  const [draftOnly, setDraftOnly] = useState(true);
  const [ccSelf, setCcSelf] = useState(false);

  const [basedIn, setBasedIn] = useState("Pakistan");
  const [allowed, setAllowed] = useState<string[]>(["Worldwide", "Remote (EU)", "Remote (US)"]);
  const [blocked, setBlocked] = useState<string[]>(["US only", "Onsite"]);
  const [needsVisa, setNeedsVisa] = useState(true);
  const [tzOverlap, setTzOverlap] = useState(4);

  const [titles, setTitles] = useState<string[]>(["Backend engineer", "Python engineer", "Inference engineer"]);
  const [payMin, setPayMin] = useState(40);
  const [payMax, setPayMax] = useState(60);
  const [currency, setCurrency] = useState("USD / hour");
  const [maxHeadcount, setMaxHeadcount] = useState(20);
  const [seniority, setSeniority] = useState<string[]>(["Mid", "Senior", "Founding"]);
  const [excludeCompanies, setExcludeCompanies] = useState<string[]>(["Google", "Meta", "Amazon"]);

  const [weights, setWeights] = useState<Weights>({
    skills: 35,
    experience: 25,
    location: 15,
    trajectory: 15,
    culture: 10,
  });
  const [threshold, setThreshold] = useState(3.5);
  const [dailyRelease, setDailyRelease] = useState(15);
  const [perCompany, setPerCompany] = useState(2);

  const [ollamaHost, setOllamaHost] = useState("http://127.0.0.1:11434");
  const [scoreModel, setScoreModel] = useState("hermes3:8b");
  const [writeModel, setWriteModel] = useState("gemma2:9b");
  const [jobspyKey, setJobspyKey] = useState("");
  const [sources, setSources] = useState<string[]>(SOURCE_OPTIONS.map(([id]) => id));

  const [jdCap, setJdCap] = useState(80);
  const [cvSystem, setCvSystem] = useState("");
  const [emailSystem, setEmailSystem] = useState("");
  const [toast, setToast] = useState("");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const weightTotal = Object.values(weights).reduce((a, b) => a + b, 0);

  const completeness = useMemo(() => {
    const checks = [
      Boolean(name),
      Boolean(email),
      Boolean(profile.length > 40),
      skills.length > 2,
      Boolean(gmailAddress),
      allowed.length > 0,
      titles.length > 0,
      weightTotal === 100,
      Boolean(scoreModel && writeModel),
      Boolean(jdCap),
    ];
    return Math.round((checks.filter(Boolean).length / checks.length) * 100);
  }, [name, email, profile, skills, gmailAddress, allowed, titles, weightTotal, scoreModel, writeModel, jdCap]);

  function setWeight(key: keyof Weights, value: number) {
    setWeights((w) => ({ ...w, [key]: value }));
  }

  function normalize() {
    const total = weightTotal || 1;
    const scaled = Object.fromEntries(
      Object.entries(weights).map(([k, v]) => [k, Math.round((v / total) * 100)]),
    ) as Weights;
    const drift = 100 - Object.values(scaled).reduce((a, b) => a + b, 0);
    scaled.skills += drift;
    setWeights(scaled);
  }

  const config = useMemo(
    () => ({
      identity: { name, email, title, links },
      profile: { resumeName, profile, skills, neverClaim },
      email: { gmailAddress, credsPath, signature, draftOnly, ccSelf },
      geography: { basedIn, allowed, blocked, needsVisa, tzOverlap },
      role: { titles, payMin, payMax, currency, maxHeadcount, seniority, excludeCompanies },
      scoring: { weights, threshold, dailyRelease, perCompany },
      engine: { ollamaHost, scoreModel, writeModel, jobspyKey, sources },
      cadence: { jdCap },
      prompts: { cvSystem, emailSystem },
    }),
    [
      name, email, title, links,
      resumeName, profile, skills, neverClaim,
      gmailAddress, credsPath, signature, draftOnly, ccSelf,
      basedIn, allowed, blocked, needsVisa, tzOverlap,
      titles, payMin, payMax, currency, maxHeadcount, seniority, excludeCompanies,
      weights, threshold, dailyRelease, perCompany,
      ollamaHost, scoreModel, writeModel, jobspyKey, sources,
      jdCap, cvSystem, emailSystem,
    ],
  );

  useEffect(() => {
    if (!online || loaded) return;
    api
      .config()
      .then((res) => {
        const saved = res.config as typeof config;
        if (!saved) return;
        if (saved.identity) {
          setName(saved.identity.name ?? name);
          setEmail(saved.identity.email ?? email);
          setTitle(saved.identity.title ?? title);
          setLinks(saved.identity.links ?? links);
        }
        if (saved.profile) {
          setResumeName(saved.profile.resumeName ?? resumeName);
          setProfile(saved.profile.profile ?? profile);
          setSkills(saved.profile.skills ?? skills);
          setNeverClaim(saved.profile.neverClaim ?? neverClaim);
        }
        if (saved.email) {
          setGmailAddress(saved.email.gmailAddress ?? gmailAddress);
          setCredsPath(saved.email.credsPath ?? credsPath);
          setSignature(saved.email.signature ?? signature);
          setCcSelf(Boolean(saved.email.ccSelf));
        }
        if (saved.geography) {
          setBasedIn(saved.geography.basedIn ?? basedIn);
          setAllowed(saved.geography.allowed ?? allowed);
          setBlocked(saved.geography.blocked ?? blocked);
          setNeedsVisa(Boolean(saved.geography.needsVisa));
          setTzOverlap(saved.geography.tzOverlap ?? tzOverlap);
        }
        if (saved.role) {
          setTitles(saved.role.titles ?? titles);
          setPayMin(saved.role.payMin ?? payMin);
          setPayMax(saved.role.payMax ?? payMax);
          setCurrency(saved.role.currency ?? currency);
          setMaxHeadcount(saved.role.maxHeadcount ?? maxHeadcount);
          setSeniority(saved.role.seniority ?? seniority);
          setExcludeCompanies(saved.role.excludeCompanies ?? excludeCompanies);
        }
        if (saved.scoring) {
          setWeights(saved.scoring.weights ?? weights);
          setThreshold(saved.scoring.threshold ?? threshold);
          setDailyRelease(saved.scoring.dailyRelease ?? dailyRelease);
          setPerCompany(saved.scoring.perCompany ?? perCompany);
        }
        if (saved.engine) {
          setOllamaHost(saved.engine.ollamaHost ?? ollamaHost);
          setScoreModel(saved.engine.scoreModel ?? scoreModel);
          setWriteModel(saved.engine.writeModel ?? writeModel);
          setSources(saved.engine.sources ?? sources);
        }
        if (saved.cadence) {
          setJdCap(saved.cadence.jdCap ?? jdCap);
        }
        if (saved.prompts) {
          setCvSystem(saved.prompts.cvSystem ?? cvSystem);
          setEmailSystem(saved.prompts.emailSystem ?? emailSystem);
        }
        setToast("Loaded your saved configuration");
        setTimeout(() => setToast(""), 2400);
      })
      .catch(() => undefined)
      .finally(() => setLoaded(true));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [online, loaded]);

  async function save() {
    if (!online) {
      setToast("Backend offline — configuration not saved");
      setTimeout(() => setToast(""), 2600);
      return;
    }
    setSaving(true);
    try {
      await api.saveConfig(config);
      setToast(`Saved to SQLite · profile ${completeness}% complete`);
    } catch (err) {
      setToast((err as Error).message);
    } finally {
      setSaving(false);
      setTimeout(() => setToast(""), 2800);
    }
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json" });
    const href = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = href;
    a.download = "alice.config.json";
    a.click();
    URL.revokeObjectURL(href);
    setToast("Exported alice.config.json");
    setTimeout(() => setToast(""), 2400);
  }

  return (
    <div className="wrap section" style={{ paddingTop: 40 }}>
      <div className="ws-head">
        <div>
          <span className="eyebrow">Setup</span>
          <h2>Tell Alice who you are and what counts</h2>
          <p>
            Everything here lives in the local SQLite file next to the app. Nothing is uploaded, and the fields
            below are the only inputs the pipeline reads.
          </p>
        </div>
        <div className="chips">
          <span className={online ? "chip live" : "chip off"}>{online ? "Saving to SQLite" : "Backend offline"}</span>
          <span className={draftOnly ? "chip live" : "chip off"}>{draftOnly ? "Draft-only mode" : "Send enabled"}</span>
        </div>
      </div>

      {!online ? (
        <Banner tone="warn">
          <b>Backend offline.</b> You can still fill this in and export it as JSON, but nothing will persist until
          the API on 8471 is running.
        </Banner>
      ) : state && !state.gmail ? (
        <Banner>
          <b>Gmail is not connected yet.</b> Drop your OAuth credentials at the path below, then Alice can write
          drafts into your account instead of keeping them in SQLite only.
        </Banner>
      ) : null}

      <div className="setup">
        <nav className="setup-rail">
          {sections.map(([id, label]) => (
            <a href={`#${id}`} key={id}>
              {label}
            </a>
          ))}
        </nav>

        <div>
          <section className="setup-card" id="identity">
            <header>
              <h3>You</h3>
              <p>The name on the paperwork and the address a founder replies to.</p>
            </header>
            <div className="fields two">
              <Field label="Full name">
                <input className="inp" value={name} onChange={(e) => setName(e.target.value)} />
              </Field>
              <Field label="Contact email">
                <input className="inp" value={email} onChange={(e) => setEmail(e.target.value)} />
              </Field>
              <Field label="Headline" hint="Used as the CV subtitle when a job does not suggest a better one.">
                <input className="inp" value={title} onChange={(e) => setTitle(e.target.value)} />
              </Field>
              <Field label="Links" hint="Enter to add.">
                <TagInput values={links} onChange={setLinks} placeholder="github.com/…" />
              </Field>
            </div>
          </section>

          <section className="setup-card" id="resume">
            <header>
              <h3>Master profile</h3>
              <p>
                Tailoring can only rearrange what lives here. If a tool is not on this page, it never reaches a
                tailored CV.
              </p>
            </header>
            <div className="fields">
              <label className="drop">
                <strong>{resumeName}</strong>
                Drop a PDF or DOCX, or click to replace
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={(e) => setResumeName(e.target.files?.[0]?.name ?? resumeName)}
                />
              </label>
              <Field label="Profile text" hint="Plain sentences beat bullet salad — the writing model reads this literally.">
                <textarea className="ta" style={{ minHeight: 140 }} value={profile} onChange={(e) => setProfile(e.target.value)} />
              </Field>
              <div className="fields two">
                <Field label="Skills you can claim">
                  <TagInput values={skills} onChange={setSkills} placeholder="Add a skill" />
                </Field>
                <Field label="Never claim" hint="Hard block, even if a posting begs for it.">
                  <TagInput values={neverClaim} onChange={setNeverClaim} placeholder="Add a forbidden term" />
                </Field>
              </div>
            </div>
          </section>

          <section className="setup-card" id="email">
            <header>
              <h3>Email & Gmail</h3>
              <p>Alice writes drafts into your Gmail account. The send call is not wired to any automation.</p>
            </header>
            <div className="fields two">
              <Field label="Gmail address">
                <input className="inp" value={gmailAddress} onChange={(e) => setGmailAddress(e.target.value)} />
              </Field>
              <Field label="OAuth credentials path" hint="Downloaded from Google Cloud Console.">
                <input className="inp" value={credsPath} onChange={(e) => setCredsPath(e.target.value)} />
              </Field>
              <Field label="Signature">
                <input className="inp" value={signature} onChange={(e) => setSignature(e.target.value)} />
              </Field>
              <div className="fields">
                <Toggle
                  title="Draft-only mode"
                  note="Locked on. Sending is a human click in Letters."
                  on={draftOnly}
                  onChange={setDraftOnly}
                  locked
                />
                <Toggle title="Copy myself on sends" note="Adds your address to Bcc." on={ccSelf} onChange={setCcSelf} />
              </div>
            </div>
          </section>

          <section className="setup-card" id="geography">
            <header>
              <h3>Geography</h3>
              <p>Where you can legally work and which phrasings should archive a listing on sight.</p>
            </header>
            <div className="fields two">
              <Field label="Based in">
                <input className="inp" value={basedIn} onChange={(e) => setBasedIn(e.target.value)} />
              </Field>
              <Field label="Timezone overlap required" hint={`${tzOverlap} hours with the team`}>
                <input
                  className="slider"
                  type="range"
                  min={0}
                  max={8}
                  value={tzOverlap}
                  onChange={(e) => setTzOverlap(Number(e.target.value))}
                />
              </Field>
              <Field label="Allowed locations">
                <TagInput values={allowed} onChange={setAllowed} placeholder="Worldwide, Remote (EU)…" />
              </Field>
              <Field label="Blocked phrases" hint="Matched against the listing text.">
                <TagInput values={blocked} onChange={setBlocked} placeholder="US only, onsite…" />
              </Field>
            </div>
            <div style={{ marginTop: 14 }}>
              <Toggle
                title="I need visa or contractor sponsorship"
                note="Listings that rule out international contractors get archived at Gate A."
                on={needsVisa}
                onChange={setNeedsVisa}
              />
            </div>
          </section>

          <section className="setup-card" id="role">
            <header>
              <h3>Role & pay</h3>
              <p>The hard band. A listing outside it is archived rather than scored.</p>
            </header>
            <div className="fields two">
              <Field label="Target titles">
                <TagInput values={titles} onChange={setTitles} placeholder="Backend engineer…" />
              </Field>
              <Field label="Seniority">
                <TagInput values={seniority} onChange={setSeniority} placeholder="Senior, Founding…" />
              </Field>
              <Field label={`Pay floor · ${payMin}`}>
                <input className="slider" type="range" min={10} max={120} value={payMin} onChange={(e) => setPayMin(Math.min(Number(e.target.value), payMax - 1))} />
              </Field>
              <Field label={`Pay ceiling · ${payMax}`}>
                <input className="slider" type="range" min={20} max={200} value={payMax} onChange={(e) => setPayMax(Math.max(Number(e.target.value), payMin + 1))} />
              </Field>
              <Field label="Unit">
                <select className="sel" value={currency} onChange={(e) => setCurrency(e.target.value)}>
                  <option>USD / hour</option>
                  <option>USD / year</option>
                  <option>EUR / hour</option>
                  <option>GBP / day</option>
                </select>
              </Field>
              <Field label={`Max headcount · under ${maxHeadcount}`} hint="Small teams are the whole point.">
                <input className="slider" type="range" min={2} max={200} value={maxHeadcount} onChange={(e) => setMaxHeadcount(Number(e.target.value))} />
              </Field>
            </div>
            <div style={{ marginTop: 14 }}>
              <Field label="Companies to exclude">
                <TagInput values={excludeCompanies} onChange={setExcludeCompanies} placeholder="Add a company" />
              </Field>
            </div>
          </section>

          <section className="setup-card" id="scoring">
            <header>
              <h3>Scoring</h3>
              <p>How Gate B weighs a surviving listing, and how good it has to be to take a slot.</p>
            </header>
            {(Object.keys(weightLabels) as (keyof Weights)[]).map((key) => (
              <div className="weightrow" key={key}>
                <span>{weightLabels[key]}</span>
                <input
                  className="slider"
                  type="range"
                  min={0}
                  max={60}
                  value={weights[key]}
                  onChange={(e) => setWeight(key, Number(e.target.value))}
                />
                <b>{weights[key]}%</b>
              </div>
            ))}
            <div className="weight-total">
              <span className={weightTotal === 100 ? "good" : "bad"}>
                Total {weightTotal}% {weightTotal === 100 ? "· balanced" : "· must equal 100"}
              </span>
              <button className="btn btn-outline btn-sm" type="button" onClick={normalize}>
                Normalize to 100
              </button>
            </div>
            <div className="fields three" style={{ marginTop: 20 }}>
              <Field label={`Release threshold · ${threshold.toFixed(1)}`} hint="Composite score out of 5.">
                <input className="slider" type="range" min={2} max={5} step={0.1} value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} />
              </Field>
              <Field label={`Jobs released per day · ${dailyRelease}`}>
                <input className="slider" type="range" min={5} max={40} value={dailyRelease} onChange={(e) => setDailyRelease(Number(e.target.value))} />
              </Field>
              <Field label={`Max per company · ${perCompany}`} hint="Stops one studio owning a morning.">
                <input className="slider" type="range" min={1} max={6} value={perCompany} onChange={(e) => setPerCompany(Number(e.target.value))} />
              </Field>
            </div>
          </section>

          <section className="setup-card" id="engine">
            <header>
              <h3>Models & keys</h3>
              <p>
                Both models run through Ollama on this machine. There is no field here for a hosted model provider,
                and the build fails if one appears in the source.
              </p>
            </header>
            <div className="fields two">
              <Field label="Ollama host">
                <input className="inp" value={ollamaHost} onChange={(e) => setOllamaHost(e.target.value)} />
              </Field>
              <Field label="Scoring model">
                <select className="sel" value={scoreModel} onChange={(e) => setScoreModel(e.target.value)}>
                  <option>hermes3:8b</option>
                  <option>llama3.1:8b</option>
                  <option>qwen2.5:7b</option>
                </select>
              </Field>
              <Field label="Writing model">
                <select className="sel" value={writeModel} onChange={(e) => setWriteModel(e.target.value)}>
                  <option>gemma2:9b</option>
                  <option>mistral-nemo:12b</option>
                  <option>hermes3:8b</option>
                </select>
              </Field>
              <Field label="JobSpy key" hint="Optional. Only needed for LinkedIn and Indeed pulls.">
                <input className="inp" type="password" placeholder="optional" value={jobspyKey} onChange={(e) => setJobspyKey(e.target.value)} />
              </Field>
            </div>
            <div style={{ marginTop: 14 }}>
              <Field label="Sources to crawl" hint="These are the boards the Run now button will hit when live crawl is on.">
                <div className="source-grid">
                  {SOURCE_OPTIONS.map(([id, label]) => (
                    <label key={id} className={`source-opt${sources.includes(id) ? " on" : ""}`}>
                      <input
                        type="checkbox"
                        checked={sources.includes(id)}
                        onChange={() =>
                          setSources((cur) => (cur.includes(id) ? cur.filter((s) => s !== id) : [...cur, id]))
                        }
                      />
                      <span>{label}</span>
                    </label>
                  ))}
                </div>
              </Field>
            </div>
          </section>

          <section className="setup-card" id="prompts">
            <header>
              <h3>System prompts</h3>
              <p>
                Extra instructions appended to Alice’s locked rules. They cannot invent employers, tools, or metrics
                that are not in the master profile, and they cannot restore banned email openers.
              </p>
            </header>
            <div className="fields">
              <Field
                label="CV tailor (Gemma) and audit (Hermes)"
                hint="Tone, length, what to emphasize. Grounding still wins if this conflicts."
              >
                <textarea
                  className="ta"
                  style={{ minHeight: 120 }}
                  value={cvSystem}
                  onChange={(e) => setCvSystem(e.target.value)}
                  placeholder="Example: Prefer short bullets. Lead with FastAPI and local inference. British English."
                />
              </Field>
              <Field
                label="Outreach email (Gemma) and audit (Hermes)"
                hint="Voice and ask. Still 5–8 sentences, no ‘hope this finds you well’."
              >
                <textarea
                  className="ta"
                  style={{ minHeight: 120 }}
                  value={emailSystem}
                  onChange={(e) => setEmailSystem(e.target.value)}
                  placeholder="Example: Direct, no flattery. Sign off with just the first name. Ask for a 15-minute call."
                />
              </Field>
            </div>
          </section>

          <section className="setup-card" id="cadence">
            <header>
              <h3>Politeness cap</h3>
              <p>There is no clock. You press Run now. This only limits how many full descriptions Alice fetches in a day.</p>
            </header>
            <Field label={`Full descriptions per day · ${jdCap}`} hint="The politeness cap across all sources.">
              <input className="slider" type="range" min={20} max={400} step={10} value={jdCap} onChange={(e) => setJdCap(Number(e.target.value))} />
            </Field>
          </section>

          <div className="savebar">
            <div>
              <b>{completeness}% configured</b>
              <div className="meter" style={{ marginTop: 8 }}>
                <i style={{ width: `${completeness}%` }} />
              </div>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-outline btn-sm" type="button" onClick={exportJson}>
                Export JSON
              </button>
              <button className="btn btn-accent btn-sm" type="button" onClick={save} disabled={saving}>
                {saving ? "Saving…" : "Save configuration"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {toast ? <Toast message={toast} /> : null}
    </div>
  );
}
