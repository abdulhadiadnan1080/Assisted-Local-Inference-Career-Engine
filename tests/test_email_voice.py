from alice_core.schemas import OutreachDraft
from alice_core.tailor import FORBIDDEN_OPENERS, audit_email, write_email
from tests.conftest import good_listing


def test_forbidden_openers_stripped():
    profile = {
        "candidate": {"full_name": "Jordan Hale"},
        "summary_foundation": {"summary": "I ship production Python services."},
        "skills": {"languages": ["Python"]},
    }
    dirty = OutreachDraft(
        subject="Hello there from me today extra words",
        body_text=(
            "I hope this email finds you well. I came across your posting. "
            "I am writing to express interest. We should talk. "
            "I ship production Python services. Happy to walk through a project. Jordan Hale."
        ),
    )
    clean = audit_email(dirty, profile)
    low = clean.body_text.lower()
    for phrase in FORBIDDEN_OPENERS:
        assert phrase not in low
    sentences = [s for s in clean.body_text.replace("!", ".").split(".") if s.strip()]
    assert 5 <= len(sentences) <= 8
    assert len(clean.subject.split()) <= 8


def test_write_email_stores_without_address():
    listing = good_listing(30)
    draft = write_email(listing, None, ["Keep the stack tiny"], {
        "candidate": {"full_name": "Jordan Hale"},
        "summary_foundation": {"summary": "I ship production Python services."},
        "skills": {"languages": ["Python", "TypeScript"]},
    })
    assert draft.body_text
    assert "i hope this email finds you well" not in draft.body_text.lower()
