from datetime import datetime
from src.models import AgentState

class ReportRenderer:
    @staticmethod
    def render(state: AgentState, verification_log: list[dict]) -> str:
        total_citations = len(verification_log)
        valid_citations = sum(1 for v in verification_log if v["status"] == "valid")
        invalid_citations = total_citations - valid_citations

        lines = [
            f"# Tinjauan Pustaka: {state.topic}",
            f"**Tanggal:** {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
            f"**Paper Dikaji:** {len(state.extractions)} | "
            f"**Total Putaran Refleksi:** {state.iteration}",
            "",
            "## 1. Ringkasan Eksekutif",
            state.synthesis.executive_summary if state.synthesis else "-",
            "",
            "## 2. Tema Utama",
            state.synthesis.main_themes if state.synthesis else "-",
            "",
            "## 3. Tabel Perbandingan",
            "| Paper | Tahun | Masalah | Metode | Temuan Utama | Keterbatasan |",
            "|---|---|---|---|---|---|"
        ]

        for pid, ext in state.extractions.items():
            p = state.papers[pid]
            title = p.title.replace("|", "/")
            lines.append(
                f"| {title} | {p.year or '-'} | {ext.problem} | {ext.method} | {ext.key_findings} | {ext.limitations or '-'} |"
            )

        lines.extend([
            "",
            "## 4. Research Gap dan Ide Penelitian",
            state.synthesis.research_gaps if state.synthesis else "-",
            "",
            "## 5. Keterbatasan Tinjauan Ini",
            state.synthesis.limitations_of_review if state.synthesis else "-",
            "",
            "## 6. Catatan Verifikasi Sitasi",
            f"- **Total Sitasi Ditulis:** {total_citations}",
            f"- **Sitasi Valid:** {valid_citations}",
            f"- **Sitasi Tidak Valid (Dibersihkan):** {invalid_citations}",
            "",
            "## 7. Daftar Pustaka"
        ])

        idx = 1
        for pid in state.extractions.keys():
            p = state.papers[pid]
            authors = ", ".join(p.authors[:3]) + (" et al." if len(p.authors) > 3 else "")
            venue = f", *{p.venue}*" if p.venue else ""
            url = f" [Link]({p.url})" if p.url else ""
            lines.append(f"{idx}. {authors} ({p.year or 'n.d.'}). **{p.title}**{venue}.{url}")
            idx += 1

        lines.extend([
            "",
            "## Lampiran: Jejak Langkah Agen",
            f"- Panggilan Model LLM: {state.llm_calls}",
            f"- Jumlah Paper Tersaring: {len(state.screenings)}"
        ])

        return "\n".join(lines)