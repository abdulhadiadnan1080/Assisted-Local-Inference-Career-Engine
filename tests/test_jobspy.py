from alice_core.sources.jobspy import DEFAULT_SITES, jobspy_sites, parse_rows


def test_default_sites_linkedin_indeed(monkeypatch):
    monkeypatch.delenv("JOBSPY_SITES", raising=False)
    assert DEFAULT_SITES == ["linkedin", "indeed"]
    assert jobspy_sites() == ["linkedin", "indeed"]


def test_glassdoor_stripped(monkeypatch):
    monkeypatch.setenv("JOBSPY_SITES", "linkedin,indeed,glassdoor")
    assert "glassdoor" not in jobspy_sites()


def test_parse_rows_normalize():
    rows = parse_rows(
        [
            {
                "title": "Backend",
                "company": "Acme",
                "location": "Remote",
                "job_url": "https://www.linkedin.com/jobs/view/1",
                "description": "8 people worldwide $50/hr",
                "is_remote": True,
                "site": "linkedin",
            }
        ]
    )
    assert rows[0].source == "jobspy"
    assert rows[0].apply_url.startswith("https://www.linkedin.com")
    assert rows[0].extra["source_site"] == "linkedin"
