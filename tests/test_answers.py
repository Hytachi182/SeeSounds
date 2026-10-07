from src.utils.answers import compare_answer, normalize_answer


def test_normalizes_accents_punctuation_and_spaces() -> None:
    assert normalize_answer("  Grivé,   musicienne! ") == "grive musicienne"


def test_typo_can_be_almost_correct() -> None:
    result = compare_answer("grive musiciene", "Grive musicienne", [], 90, 75)
    assert result.result in {"correct", "almost"}
    assert result.similarity >= 75


def test_alias_is_accepted() -> None:
    assert compare_answer("merle noir", "Turdus merula", ["Merle noir"]).result == "correct"
