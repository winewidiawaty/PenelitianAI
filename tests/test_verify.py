from src.models import Paper
from src.verify import CitationVerifier

def test_citation_verifier_valid_and_invalid():
    sample_paper = Paper(
        paper_id="paper_123",
        title="Sample AI Research",
        authors=["Alice Doe", "Bob Smith"],
        year=2024,
        source="arxiv"
    )
    pool = {"paper_123": sample_paper}

    text = "Model ini terbukti sangat cepat [paper_123], namun klaim lain belum tentu [phantom_456]."
    verified_text, logs = CitationVerifier.verify_and_replace(text, pool)

    assert "(Alice Doe, 2024)" in verified_text
    assert "[SITASI TIDAK TERVERIFIKASI]" in verified_text
    assert len(logs) == 2