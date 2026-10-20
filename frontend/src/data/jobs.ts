export type JobStatus = "ready" | "applied" | "sent" | "draft" | "review" | "new" | "archived" | "skipped";

export type Scorecard = {
  skills: number;
  experience: number;
  location: number;
  trajectory: number;
  culture: number;
  composite: number;
};

export type Resume = {
  fileName: string;
  headline: string;
  summary: string;
  skills: string[];
  bullets: string[];
  /** True when the packet is the untailored master profile, not a compiled artifact. */
  pending?: boolean;
};

export type Letter = {
  to: string | null;
  toName: string | null;
  subject: string;
  body: string;
  gmailDraft: boolean;
  sent: boolean;
};

export type Job = {
  id: string;
  company: string;
  title: string;
  location: string;
  source: string;
  pay: string;
  size: string;
  international: boolean;
  applyUrl: string;
  status: JobStatus;
  posted: string;
  snippet: string;
  description: string;
  need: string[];
  scores: Scorecard;
  resume: Resume;
  letter: Letter;
  briefing: boolean;
  sourceUrl?: string;
  rawStatus?: string;
  pdfUrl?: string | null;
};

const hadiBase: Omit<Resume, "headline" | "summary" | "bullets"> = {
  fileName: "Hadi-Adnan.pdf",
  skills: ["Python", "FastAPI", "SQLite", "TypeScript", "MLX", "local inference"],
};

function resume(headline: string, summary: string, bullets: string[]): Resume {
  return { ...hadiBase, headline, summary, bullets };
}

function scores(partial: Partial<Scorecard> & { composite: number }): Scorecard {
  return {
    skills: 4.4,
    experience: 4.1,
    location: 4.6,
    trajectory: 4.2,
    culture: 3.9,
    ...partial,
  };
}

export const briefingJobs: Job[] = [
  {
    id: "b1",
    company: "Lumen Thread",
    title: "Founding inference engineer",
    location: "Worldwide",
    source: "Greenhouse",
    pay: "$52/hr",
    size: "8 people",
    international: true,
    applyUrl: "https://boards.greenhouse.io/lumenthread",
    status: "ready",
    posted: "Today, 08:12",
    snippet: "Own on-device serving for a six-person studio. No cloud LLM fallback.",
    description:
      "Lumen Thread is eight people, fully remote, worldwide. Pay is $52/hr. They need someone who will own the local-model serving path, keep the stack tiny, and ship weekly. Visa-friendly. Seed founding energy. Python and MLX are the daily tools.",
    need: ["Own the local-model serving path", "Keep the stack tiny", "Ship weekly with a 6-person team"],
    scores: scores({ skills: 4.8, composite: 4.42 }),
    resume: resume(
      "Inference engineer for tiny remote teams",
      "I ship production Python services and local inference for small distributed teams, with a bias toward inspectable stacks and no cloud fallback.",
      [
        "Ran Hermes and Gemma locally on Apple Silicon without a hosted LLM.",
        "Built a FastAPI control plane over SQLite for a 6-person product team.",
        "Owned weekly shipping of an on-device serving path.",
      ],
    ),
    letter: {
      to: "maya@lumenthread.dev",
      toName: "Maya Chen",
      subject: "Local serving for Lumen Thread",
      body: "Maya, Lumen Thread needs someone to own the local-model serving path without a large platform org. I ship production Python services for small distributed teams. Recent work centers on Hermes and Gemma on Apple Silicon, FastAPI, and SQLite. I can take that slice and keep the stack tiny. Happy to walk through a relevant project if useful. Hadi Adnan",
      gmailDraft: true,
      sent: false,
    },
    briefing: true,
  },
  {
    id: "b2",
    company: "Paperkite",
    title: "Senior Python engineer",
    location: "Worldwide",
    source: "Lever",
    pay: "$48/hr",
    size: "9 people",
    international: true,
    applyUrl: "https://jobs.lever.co/paperkite",
    status: "ready",
    posted: "Today, 09:04",
    snippet: "FastAPI services and SQLite-backed products. Written comms expected.",
    description:
      "Paperkite is a nine-person studio. Remote worldwide. $48/hr. They want FastAPI services, SQLite-backed products, and people who write things down. Seed-stage, visa-friendly.",
    need: ["FastAPI services", "SQLite-backed products", "Clear written comms"],
    scores: scores({ composite: 4.16 }),
    resume: resume(
      "Python engineer, small-team products",
      "I build FastAPI services over SQLite for operators who need a quiet, local control plane.",
      [
        "Shipped FastAPI + SQLite products used daily by a small remote team.",
        "Wrote operator-facing copy and runbooks instead of slide decks.",
        "Kept dependencies boring so a nine-person studio can own the stack.",
      ],
    ),
    letter: {
      to: "jon@paperkite.io",
      toName: "Jon Hale",
      subject: "FastAPI and SQLite at Paperkite",
      body: "Jon, Paperkite needs FastAPI services on a tiny remote team. I ship production Python for small distributed groups. Recent work is SQLite-backed products and written operator tooling. I can own a slice without a platform org. Happy to walk through a project. Hadi Adnan",
      gmailDraft: true,
      sent: false,
    },
    briefing: true,
  },
  {
    id: "b3",
    company: "Northwisp",
    title: "On-device / MLX engineer",
    location: "Worldwide",
    source: "Ashby",
    pay: "$55/hr",
    size: "7 people",
    international: true,
    applyUrl: "https://jobs.ashbyhq.com/northwisp",
    status: "ready",
    posted: "Today, 09:40",
    snippet: "Apple Silicon inference. Quantization tradeoffs. No cloud fallback.",
    description:
      "Northwisp is seven people. Worldwide remote. $55/hr. They care about Apple Silicon inference, quantization, and never falling back to a hosted model. No poster email on the listing.",
    need: ["Apple Silicon inference", "Quantization tradeoffs", "No cloud fallback"],
    scores: scores({ skills: 4.9, composite: 4.51 }),
    resume: resume(
      "On-device inference, Apple Silicon",
      "I run local models on M-series machines and treat hosted LLMs as out of scope.",
      [
        "Quantized and served 8B/9B models locally with a hard cap on RAM.",
        "Built swap logic so only one model is hot on 16GB machines.",
        "Refused cloud fallbacks in production paths.",
      ],
    ),
    letter: {
      to: null,
      toName: null,
      subject: "On-device inference at Northwisp",
      body: "Northwisp needs Apple Silicon inference with no cloud fallback. I ship local Hermes and Gemma serving on M-series hardware. I can take quantization and RAM tradeoffs as the job, not a side quest. Apply is the path until a poster email appears. Hadi Adnan",
      gmailDraft: false,
      sent: false,
    },
    briefing: true,
  },
  {
    id: "b4",
    company: "Harborline",
    title: "Full-stack for a 9-person studio",
    location: "Worldwide",
    source: "Remotive",
    pay: "$45/hr",
    size: "9 people",
    international: true,
    applyUrl: "https://remotive.com/remote-jobs/harborline",
    status: "ready",
    posted: "Today, 10:11",
    snippet: "Operator dashboards, Typst PDFs, remote worldwide.",
    description:
      "Harborline is nine people making tools for operators. $45/hr, worldwide. They want dashboards, PDF pipelines, and someone who likes a quiet UI.",
    need: ["Operator dashboards", "PDF pipelines", "Remote worldwide"],
    scores: scores({ culture: 4.2, composite: 4.08 }),
    resume: resume(
      "Full-stack for operator tools",
      "I design light interfaces over local data, then compile grounded PDFs.",
      [
        "Shipped operator dashboards on FastAPI and SQLite.",
        "Compiled tailored resumes with Typst from a master profile.",
        "Kept the UI editorial instead of generic dashboard chrome.",
      ],
    ),
    letter: {
      to: "ada@harborline.co",
      toName: "Ada Voss",
      subject: "Dashboards for Harborline",
      body: "Ada, Harborline needs operator dashboards on a nine-person worldwide team. I ship FastAPI control planes and Typst PDFs from sourced facts. I can own a slice of the product UI and the paper it produces. Happy to walk through a build. Hadi Adnan",
      gmailDraft: true,
      sent: false,
    },
    briefing: true,
  },
  {
    id: "b5",
    company: "Saltbox Labs",
    title: "Agent runtime engineer",
    location: "Worldwide",
    source: "HN Who's Hiring",
    pay: "$50/hr",
    size: "6 people",
    international: true,
    applyUrl: "https://news.ycombinator.com/item?id=saltbox",
    status: "ready",
    posted: "Today, 10:28",
    snippet: "Tool-calling without SaaS. Human gates. Eval harnesses.",
    description:
      "Saltbox Labs is six people. $50/hr worldwide. They want an agent runtime that never submits unattended, with evals and a human click for Apply and Send.",
    need: ["Tool-calling without SaaS", "Eval harnesses", "Human-in-the-loop gates"],
    scores: scores({ trajectory: 4.6, composite: 4.33 }),
    resume: resume(
      "Runtime engineer, human-gated agents",
      "I build agent loops that stop at the human. Nothing applies or emails unattended.",
      [
        "Designed pipelines that draft Gmail messages and never call send.",
        "Put Apply behind window.open of the official posting.",
        "Recorded seen and shown ledgers so work is not repeated.",
      ],
    ),
    letter: {
      to: "priya@saltbox.labs",
      toName: "Priya Shah",
      subject: "Human-gated runtime",
      body: "Priya, Saltbox needs a runtime that tool-calls without a SaaS brain and still stops for a human. I ship local inference loops with Apply and Send as clicks, not bots. Happy to walk through the gate design. Hadi Adnan",
      gmailDraft: true,
      sent: false,
    },
    briefing: true,
  },
];

const extraBriefing: Job[] = [
  ["Cedar & Co", "Founding backend", "LinkedIn", "$49/hr"],
  ["Mothlight", "Platform engineer", "Indeed", "$46/hr"],
  ["Kite Room", "Python / MLX", "RemoteOK", "$53/hr"],
  ["Glassvine", "Product engineer", "WWR", "$47/hr"],
  ["Fieldnote", "Full-stack", "Himalayas", "$44/hr"],
  ["Orchard Mill", "Inference tooling", "Greenhouse", "$51/hr"],
  ["Redthread", "Senior backend", "Lever", "$50/hr"],
  ["Lowtide", "Founding full-stack", "Ashby", "$54/hr"],
  ["Nim", "Agent evals", "HN Who's Hiring", "$48/hr"],
  ["Sable Yard", "On-device ML", "Remotive", "$56/hr"],
].map(([company, title, source, pay], i) => ({
  id: `b${i + 6}`,
  company,
  title,
  location: "Worldwide",
  source,
  pay,
  size: `${6 + (i % 5)} people`,
  international: true,
  applyUrl: `https://jobs.example.com/${company.toLowerCase().replace(/\s+/g, "-")}`,
  status: "ready" as const,
  posted: `Today, ${10 + i}:${(12 + i * 3).toString().padStart(2, "0")}`,
  snippet: `${company} is a tiny remote team. ${pay}. Worldwide. They need ${title.toLowerCase()} who can ship without a platform org.`,
  description: `${company} is under 20 people, hires internationally, and pays ${pay}. Fully remote. They need ${title.toLowerCase()} with Python, FastAPI, and a calm written style. Seed energy, no FAANG process.`,
  need: ["Ship in a small remote team", "Own a slice of the stack", "Write things down"],
  scores: scores({ composite: Number((3.9 + (i % 5) * 0.08).toFixed(2)) }),
  resume: resume(
    `${title} · ${company}`,
    `Tailored for ${company}: I ship production Python for small distributed teams.`,
    [
      `Mapped my FastAPI and SQLite work onto what ${company} listed.`,
      "Kept every metric sourced from the master profile.",
      "Left tools I do not have off the page.",
    ],
  ),
  letter: {
    to: i % 3 === 0 ? null : `hiring@${company.toLowerCase().replace(/[^a-z]/g, "")}.dev`,
    toName: i % 3 === 0 ? null : "Hiring",
    subject: `${title.split(" ")[0]} at ${company}`,
    body: `${company} needs ${title.toLowerCase()} on a tiny worldwide team. I ship production Python services. Recent work is local inference and operator tools. Happy to walk through a project. Hadi Adnan`,
    gmailDraft: i % 3 !== 0,
    sent: false,
  },
  briefing: true,
}));

export const todayFifteen: Job[] = [...briefingJobs, ...extraBriefing];

export const intakeJobs: Job[] = [
  {
    id: "i1",
    company: "Brightlane",
    title: "Backend engineer",
    location: "Worldwide",
    source: "RemoteOK",
    pay: "Unknown",
    size: "Unknown",
    international: true,
    applyUrl: "https://remoteok.com/remote-jobs/brightlane",
    status: "review",
    posted: "Today, 11:02",
    snippet: "Remote Python role. Size and pay not stated on the snippet.",
    description:
      "Brightlane is hiring a backend engineer, remote, work from anywhere. Headcount and pay are not on the posting. Needs review before it can occupy a daily slot.",
    need: ["Confirm headcount < 20", "Confirm $40–60/hr", "Python services"],
    scores: scores({ composite: 3.4 }),
    resume: resume(
      "Backend engineer (held)",
      "Drafted against Brightlane but not released to Briefing until size and pay are known.",
      ["Python and FastAPI from the master profile.", "No invented headcount.", "No invented pay."],
    ),
    letter: {
      to: null,
      toName: null,
      subject: "Held until size and pay are known",
      body: "Brightlane is in review. Size or pay is unknown, so this job cannot take a Briefing slot. Hadi Adnan",
      gmailDraft: false,
      sent: false,
    },
    briefing: false,
  },
  {
    id: "i2",
    company: "Nimbus Freight",
    title: "Staff platform engineer",
    location: "US only",
    source: "Indeed",
    pay: "$85/hr",
    size: "200+ people",
    international: false,
    applyUrl: "https://indeed.com/nimbus-freight",
    status: "new",
    posted: "Today, 11:18",
    snippet: "US only, onsite language, well outside the pay band.",
    description: "Archived on Gate A: US-only, large org language, $85/hr. Kept in Intake so you can see what was dropped today.",
    need: ["Would have needed US residency", "Enterprise platform org"],
    scores: scores({ composite: 2.1 }),
    resume: resume(
      "Not submitted",
      "No CV is sent for archived listings. A grounded draft is still attached for the record.",
      ["Master profile unchanged.", "No application packet generated for send."],
    ),
    letter: {
      to: null,
      toName: null,
      subject: "Archived · Gate A",
      body: "This listing failed hard parameters. No letter goes out. Hadi Adnan",
      gmailDraft: false,
      sent: false,
    },
    briefing: false,
  },
];

const moreIntake: Job[] = [
  ["Quilt", "Founding engineer", "Arbeitnow", "review"],
  ["Plover", "ML engineer", "Himalayas", "new"],
  ["Tanager", "Full-stack", "WWR", "review"],
  ["Ivyroom", "Python", "LinkedIn", "new"],
  ["Sora Desk", "Backend", "Indeed", "review"],
  ["Copperline", "Inference", "RemoteOK", "new"],
  ["Vellum", "Agent engineer", "HN Who's Hiring", "review"],
  ["Dune & Co", "Product engineer", "Remotive", "new"],
].map(([company, title, source, status], i) => ({
  id: `i${i + 3}`,
  company,
  title,
  location: "Worldwide",
  source,
  pay: i % 2 ? "Unknown" : "$42–58/hr",
  size: i % 2 ? "Unknown" : `${11 + i} people`,
  international: true,
  applyUrl: `https://boards.example.com/${company.toLowerCase()}`,
  status: status as JobStatus,
  posted: `Today, 12:${(10 + i).toString().padStart(2, "0")}`,
  snippet: `${company} posted ${title}. ${status === "review" ? "Size or pay still unknown." : "New scrape, not yet in Briefing."}`,
  description: `${company} was pulled today from ${source}. ${status === "review" ? "Unknown size or pay, so it stays out of the daily fifteen." : "Passed snippet scan; waiting for a later rank."}`,
  need: ["Confirm Gate A", "Score Gate B", "Attach tailored CV"],
  scores: scores({ composite: 3.55 }),
  resume: resume(
    `${title} · ${company}`,
    `CV packet staged for ${company}. Not in today’s fifteen.`,
    [
      "Grounded in Hadi Adnan’s master profile.",
      "Keywords only where they already exist.",
      "Ready if this job is promoted.",
    ],
  ),
  letter: {
    to: null,
    toName: null,
    subject: `Draft for ${company}`,
    body: `${company} is on Intake, not Briefing. Letter stays unsent. Hadi Adnan`,
    gmailDraft: false,
    sent: false,
  },
  briefing: false,
}));

export const allIntake = [...intakeJobs, ...moreIntake];

export const allJobs = [...todayFifteen, ...allIntake];

export function jobById(id: string) {
  return allJobs.find((j) => j.id === id);
}
