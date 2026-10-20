# ALICE

Assisted Local Inference Career Engine. Spoken as Alice.

Local, **$0-inference** career engine for Apple Silicon. Hermes 3 (8B) and Gemma 2 (9B) via Ollama. Public boards plus JobSpy for LinkedIn and Indeed. You review cards and click **Apply** and/or **Send**. Nothing applies or emails unattended.

## Runbook

1. Copy `config/master_profile.example.yaml` to `config/master_profile.yaml` and fill it with sourced facts only.
2. `brew install typst ollama` then `ollama serve` and `ollama pull hermes3:8b && ollama pull gemma2:9b`.
3. `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
4. Optional Gmail: put OAuth client JSON at `credentials.json`, copy `.env.example` to `.env`. Missing token means drafts stay local and Send says connect Gmail.
5. `python app.py` → [http://127.0.0.1:8471](http://127.0.0.1:8471)
   React UI: `cd frontend && npm install && npm run dev` → [http://127.0.0.1:8472](http://127.0.0.1:8472)
6. Live crawl starts **off**. Turn **Live crawl** on in the sidebar only when you want real boards, then **Run pipeline**. **Load sample deck** is fake cards and does not crawl.
7. Edit the note if needed. **Apply** opens the official posting (Greenhouse, Lever, Ashby, LinkedIn, Indeed). You submit. **Send** sends the existing Gmail draft for that one job.
8. Next run: new listings only. Yesterday’s 15 stay gone (`shown_on`).

`python scripts/doctor.py` checks Typst, both models, **≥ 35 tok/s**, and estimated model RAM. On 16GB load one model at a time. Together they should stay **≤ 11GB**.

## What is on

- RemoteOK, Remotive, Arbeitnow, Himalayas, WWR RSS, HN Who’s Hiring, allowlisted Greenhouse/Lever/Ashby JSON
- **JobSpy LinkedIn + Indeed** (`JOBSPY_SITES` defaults to `linkedin,indeed`)
- Apply still only `window.open(apply_url)`

## What stays off

- Glassdoor, Wellfound HTML, Twitter
- Apollo, Hunter, guessed `jobs@` / `contact@`
- Unattended Easy Apply / Workday form bots
- Cloud LLMs

## Layout

SQLite at `data/alice.db` is the source of truth. No in-memory pipeline list.
