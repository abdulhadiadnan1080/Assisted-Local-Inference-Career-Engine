from alice_core.evaluator import composite_score, recommendation
from alice_core.schemas import JobEvaluation


def _eval(**kwargs) -> JobEvaluation:
    base = dict(
        score_skills=3.0,
        score_experience=3.0,
        score_location=3.0,
        score_trajectory=3.0,
        score_culture=3.0,
    )
    base.update(kwargs)
    return JobEvaluation(**base)


def test_weights_known_fixture():
    e = _eval(
        score_skills=5.0,
        score_experience=4.0,
        score_location=3.0,
        score_trajectory=2.0,
        score_culture=1.0,
    )
    # 5*.35 + 4*.25 + 3*.15 + 2*.15 + 1*.10 = 1.75+1.00+0.45+0.30+0.10 = 3.60
    assert composite_score(e) == 3.60


def test_threshold():
    assert recommendation(3.49) == "ARCHIVE"
    assert recommendation(3.50) == "PROCEED"
    assert recommendation(3.5) == "PROCEED"


def test_composite_is_pure_python():
    import inspect

    from alice_core import evaluator

    src = inspect.getsource(evaluator.composite_score)
    assert "structured" not in src
    assert "ollama" not in src.lower()
    assert "openai" not in src.lower()
