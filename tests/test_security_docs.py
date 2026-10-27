from pathlib import Path


def test_security_guide_warns_about_pickle_saves() -> None:
    guide = Path(__file__).parents[1] / "SECURITY.md"
    text = guide.read_text(encoding="utf-8")
    assert "pickle" in text.lower()
    assert "Only load roster files you trust" in text
    assert ".pqw" in text
