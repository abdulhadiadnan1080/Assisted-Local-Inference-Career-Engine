from alice_core.poster import emails_in, extract_regex, literal_only
from tests.conftest import good_listing


def test_literal_email_only():
    listing = good_listing(
        20,
        description="Posted by Maya Chen. Email maya@lumenthread.dev for the role. 8 people worldwide $50/hr.",
    )
    poster = extract_regex(listing)
    assert poster.poster_email == "maya@lumenthread.dev"
    assert "maya@lumenthread.dev" in emails_in(listing.description)


def test_never_guess_domain():
    listing = good_listing(21, company="Acme", description="No contact listed. 8 people worldwide $50/hr.")
    poster = extract_regex(listing)
    assert poster.poster_email is None
    assert literal_only("jobs@acme.com", listing.description) is None
    assert literal_only("contact@acme.com", listing.description) is None


def test_guessed_address_rejected_even_if_model_returns_it():
    listing = good_listing(22, description="Talk to us. 8 people worldwide.")
    assert literal_only("contact@tinyco.com", listing.description) is None
