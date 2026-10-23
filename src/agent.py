import uuid
from src.models import AgentState, SearchPlan, Screening, Extraction, Synthesis
from src.llm import LLMClient
from src.tools import search_papers
from src.prompts import (
    PLAN_SYSTEM_PROMPT, SCREEN_SYSTEM_PROMPT,
    EXTRACT_SYSTEM_PROMPT, SYNTHESIZE_SYSTEM_PROMPT
)
from src.logger import RunLogger
from src.verify import CitationVerifier
from src.report import ReportRenderer

class ResearchAgent:
    def __init__(self, target_papers: int = 4, max_loops: int = 3):
        self.llm = LLMClient()
        self.target_papers = target_papers
        self.max_loops = max_loops
        self.run_id = str(uuid.uuid4())[:8]
        self.logger = RunLogger(self.run_id)

    def run(self, topic: str, source: str = "both") -> tuple[AgentState, str]:
        state = AgentState(topic=topic)
        self.logger.log("PLAN", f"Merancang rencana pencarian topik: {topic}")

        # 1. PLAN
        plan_prompt = f"Topik Riset: {topic}\nBuatkan 3-5 query penelusuran beserta kriteria relevansinya."
        state.plan = self.llm.generate_structured(PLAN_SYSTEM_PROMPT, plan_prompt, SearchPlan)
        
        # 2. LOOP (SEARCH - SCREEN - REFLECT)
        while state.iteration < self.max_loops:
            state.iteration += 1
            self.logger.log("LOOP", f"Siklus pencarian ke-{state.iteration}")

            for q in state.plan.queries:
                self.logger.log("SEARCH", f"Mengeksekusi kueri: {q}")
                results = search_papers(q, limit=5, source=source)
                for paper in results:
                    if paper.paper_id not in state.papers:
                        state.papers[paper.paper_id] = paper

            # SCREENING
            for pid, paper in state.papers.items():
                if pid in state.screenings:
                    continue
                screen_prompt = (
                    f"Topik: {state.topic}\nJudul: {paper.title}\n"
                    f"Abstrak: {paper.abstract}\nBeri skor 0-10 kelayakan inklusi."
                )
                screening = self.llm.generate_structured(SCREEN_SYSTEM_PROMPT, screen_prompt, Screening)
                screening.paper_id = pid
                state.screenings[pid] = screening

            # REFLECTION
            relevant_papers = [pid for pid, s in state.screenings.items() if s.relevance >= 7]
            self.logger.log("REFLECT", f"Ditemukan {len(relevant_papers)}/{self.target_papers} paper relevan.")
            
            if len(relevant_papers) >= self.target_papers:
                break
            
            # Buat query baru untuk iterasi berikutnya
            refine_prompt = (
                f"Topik: {state.topic}. Baru diperoleh {len(relevant_papers)} paper relevan. "
                "Hasilkan variasi query pencarian baru yang lebih spesifik atau menggunakan terminologi sinonim."
            )
            state.plan = self.llm.generate_structured(PLAN_SYSTEM_PROMPT, refine_prompt, SearchPlan)

        # 3. EXTRACT
        selected_pids = [pid for pid, s in state.screenings.items() if s.relevance >= 7][:self.target_papers]
        self.logger.log("EXTRACT", f"Mengekstrak data dari {len(selected_pids)} paper pilihan.")
        for pid in selected_pids:
            p = state.papers[pid]
            ext_prompt = f"Judul: {p.title}\nAbstrak: {p.abstract}\nEkstrak poin penting."
            extraction = self.llm.generate_structured(EXTRACT_SYSTEM_PROMPT, ext_prompt, Extraction)
            extraction.paper_id = pid
            state.extractions[pid] = extraction

        # 4. SYNTHESIZE
        self.logger.log("SYNTHESIZE", "Menyusun draf laporan komparasi dan research gap.")
        context_items = []
        for pid in selected_pids:
            p = state.papers[pid]
            ext = state.extractions[pid]
            context_items.append(
                f"ID: [{pid}]\nJudul: {p.title}\nMetode: {ext.method}\nTemuan: {ext.key_findings}"
            )
        synth_prompt = (
            f"Topik: {state.topic}\nKoleksi Paper:\n" + "\n---\n".join(context_items) +
            "\n\nSusun laporan sintesis. Setiap klaim WAJIB disertai penanda sitasi [ID]."
        )
        state.synthesis = self.llm.generate_structured(SYNTHESIZE_SYSTEM_PROMPT, synth_prompt, Synthesis)

        # 5. VERIFY & REPORT
        self.logger.log("VERIFY", "Memverifikasi integritas sitasi.")
        verified_themes, v_log = CitationVerifier.verify_and_replace(state.synthesis.main_themes, state.papers)
        state.synthesis.main_themes = verified_themes
        
        state.llm_calls = self.llm.call_count
        final_markdown = ReportRenderer.render(state, v_log)
        return state, final_markdown