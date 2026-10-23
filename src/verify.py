import re
from src.models import Paper

class CitationVerifier:
    @staticmethod
    def verify_and_replace(text: str, papers_pool: dict[str, Paper]) -> tuple[str, list[dict]]:
        citations_found = re.findall(r"\[([a-zA-Z0-9_-]+)\]", text)
        verification_log = []
        verified_text = text

        for pid in set(citations_found):
            if pid in papers_pool:
                paper = papers_pool[pid]
                first_author = paper.authors[0] if paper.authors else "Anon"
                year_str = str(paper.year) if paper.year else "n.d."
                rendered = f"({first_author}, {year_str})"
                verified_text = verified_text.replace(f"[{pid}]", rendered)
                verification_log.append({"paper_id": pid, "status": "valid", "replacement": rendered})
            else:
                verified_text = verified_text.replace(f"[{pid}]", "[SITASI TIDAK TERVERIFIKASI]")
                verification_log.append({"paper_id": pid, "status": "invalid", "replacement": "[SITASI TIDAK TERVERIFIKASI]"})

        return verified_text, verification_log