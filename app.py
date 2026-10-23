import streamlit as st
from src.agent import ResearchAgent
from src.config import OUTPUT_DIR

st.set_page_config(page_title="Research Literature Review Agent", layout="wide", page_icon="🔬")

st.title("🔬 Research Literature Review Agent")
st.caption("Agentic AI untuk pencarian, screening, ekstraksi, dan verifikasi tinjauan pustaka secara otonom.")

with st.sidebar:
    st.header("Konfigurasi Parameter")
    topic_input = st.text_area("Topik / Hipotesis Riset", value="Direct Preference Optimization for LLMs Alignment")
    target_papers = st.slider("Target Paper Relevan", min_value=2, max_value=8, value=4)
    sources = st.selectbox("Sumber Paper", options=["both", "arxiv", "semantic_scholar"], index=0)
    start_btn = st.button("Jalankan Agen Riset", type="primary")

if start_btn and topic_input.strip():
    agent = ResearchAgent(target_papers=target_papers)
    
    with st.status("Pipeline agen sedang berjalan...", expanded=True) as status:
        st.write("🔄 Menginisialisasi perencana riset (Planning)...")
        state, report_md = agent.run(topic=topic_input.strip(), source=sources)
        status.update(label="Tinjauan Pustaka Selesai Dibuat!", state="complete", expanded=False)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Laporan Akhir")
        st.markdown(report_md)
        
        # Simpan ke folder output
        filename = f"Review_{agent.run_id}.md"
        out_path = OUTPUT_DIR / filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        st.download_button("Unduh Laporan Markdown", data=report_md, file_name=filename, mime="text/markdown")

    with col2:
        st.subheader("Statistik Orkestrasi")
        st.metric("Total Pemanggilan LLM", state.llm_calls)
        st.metric("Iterasi Refleksi", state.iteration)
        st.metric("Total Paper Ditemukan", len(state.papers))
        st.metric("Paper Terpilih", len(state.extractions))

        st.subheader("Paper Terpilih")
        for pid, ext in state.extractions.items():
            p = state.papers[pid]
            with st.expander(f"📄 {p.title[:45]}..."):
                st.write(f"**Metode:** {ext.method}")
                st.write(f"**Temuan:** {ext.key_findings}")
                st.write(f"**Skor Screening:** {state.screenings[pid].relevance}/10")