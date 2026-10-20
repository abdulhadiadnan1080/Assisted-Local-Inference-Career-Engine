"""JobSpy LinkedIn + Indeed. Apply still only opens the posting."""

from __future__ import annotations

import os

from alice_core.schemas import Listing

# Glassdoor stays off until ALICE-61.
DEFAULT_SITES = ["linkedin", "indeed"]


def jobspy_sites() -> list[str]:
    raw = os.environ.get("JOBSPY_SITES", "linkedin,indeed")
    sites = [s.strip().lower() for s in raw.split(",") if s.strip()]
    return [s for s in sites if s not in {"glassdoor", "zip_recruiter", "google"}] or list(DEFAULT_SITES)


def parse_rows(rows: list[dict]) -> list[Listing]:
    out: list[Listing] = []
    for row in rows:
        title = str(row.get("title") or "")
        url = str(row.get("job_url") or row.get("job_url_direct") or "")
        if not title or not url:
            continue
        sal_min = row.get("min_amount")
        sal_max = row.get("max_amount")
        currency = row.get("currency") or ""
        interval = row.get("interval") or ""
        pay = ""
        if sal_min or sal_max:
            pay = f"{currency} {sal_min or '?'}–{sal_max or '?'} {interval}".strip()
        desc = str(row.get("description") or "")
        site = str(row.get("site") or "jobspy")
        out.append(
            Listing(
                source="jobspy",
                title=title,
                company=str(row.get("company") or ""),
                location=str(row.get("location") or ""),
                apply_url=url,
                source_url=url,
                snippet=desc[:400],
                description=desc,
                pay_text=pay,
                is_remote=bool(row.get("is_remote") or False),
                extra={"source_site": site},
            )
        )
    return out


def pull() -> list[Listing]:
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return []
    sites = jobspy_sites()
    try:
        df = scrape_jobs(
            site_name=sites,
            search_term=os.environ.get("ALICE_JOBSPY_QUERY", "software engineer remote"),
            results_wanted=int(os.environ.get("JOBSPY_RESULTS", "25")),
            country_indeed=os.environ.get("JOBSPY_COUNTRY", "USA"),
            is_remote=True,
        )
    except Exception:
        return []
    if df is None or getattr(df, "empty", True):
        return []
    records = df.fillna("").to_dict(orient="records")
    return parse_rows(records)
