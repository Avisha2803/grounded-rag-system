"""
Streamlit demo UI for the Healthcare Clinical Guideline RAG API.

Talks to the FastAPI backend over HTTP — this file has zero business logic
of its own (no direct FAISS/LLM calls), which mirrors how a real front-end
team would consume this backend as a thin client over a documented API.

Run standalone:
    streamlit run streamlit_app/app.py

Or via docker-compose (see docker-compose.yml) alongside the API container.
"""
import os
import time
import requests
import streamlit as st
import pandas as pd

API_BASE_URL = os.environ.get("RAG_API_BASE_URL", "http://localhost:8000/api/v1")
DEFAULT_API_KEY = os.environ.get("RAG_API_KEY", "demo-key-123")

st.set_page_config(
    page_title="Clinical Guideline RAG — Demo",
    page_icon="🩺",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar: connection + auth + filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🩺 Clinical Guideline RAG")
    st.caption("Citation-grounded retrieval over WHO / ICMR guidelines")

    st.divider()
    st.subheader("Connection")
    api_base_url = st.text_input("API base URL", value=API_BASE_URL)
    api_key = st.text_input("API key", value=DEFAULT_API_KEY, type="password")

    st.divider()
    st.subheader("Retrieval filters")
    source_filter = st.multiselect(
        "Source organization", options=["WHO", "ICMR"], default=[]
    )
    doc_type_filter = st.selectbox(
        "Document type", options=["(any)", "guideline", "protocol"], index=0
    )
    top_k = st.slider("Top-K chunks retrieved", min_value=1, max_value=15, value=5)

    st.divider()
    if st.button("Check API health", use_container_width=True):
        try:
            resp = requests.get(f"{api_base_url}/health", timeout=10)
            if resp.ok:
                data = resp.json()
                if data.get("index_loaded"):
                    st.success("API reachable — FAISS index loaded ✅")
                else:
                    st.warning("API reachable, but no FAISS index found yet. Run ingestion first.")
            else:
                st.error(f"API returned status {resp.status_code}")
        except requests.RequestException as e:
            st.error(f"Could not reach API: {e}")

tab_query, tab_ingest, tab_audit = st.tabs(
    ["🔎 Ask a question", "📄 Ingest a guideline", "🧾 Audit trail"]
)

# ---------------------------------------------------------------------------
# Tab 1: Query
# ---------------------------------------------------------------------------
with tab_query:
    st.markdown(
        "Ask a question in natural language. The answer is generated **only** "
        "from indexed guideline text, with every claim tied to an exact "
        "document, section, and page number."
    )

    question = st.text_area(
        "Your question",
        placeholder="e.g. What is the first-line pharmacotherapy for hypertension?",
        height=90,
    )

    col_ask, col_clear = st.columns([1, 5])
    ask_clicked = col_ask.button("Ask", type="primary", use_container_width=True)

    if ask_clicked:
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            payload = {
                "question": question.strip(),
                "top_k": top_k,
            }
            if source_filter:
                payload["source_filter"] = source_filter
            if doc_type_filter != "(any)":
                payload["doc_type_filter"] = doc_type_filter

            with st.spinner("Retrieving guideline context and generating grounded answer..."):
                try:
                    start = time.time()
                    resp = requests.post(
                        f"{api_base_url}/query",
                        json=payload,
                        headers={"X-API-Key": api_key},
                        timeout=60,
                    )
                    elapsed = time.time() - start
                except requests.RequestException as e:
                    st.error(f"Request failed: {e}")
                    resp = None

            if resp is not None:
                if resp.status_code == 401:
                    st.error("Invalid API key.")
                elif resp.status_code == 429:
                    st.error("Rate limit exceeded — please wait a moment and try again.")
                elif not resp.ok:
                    st.error(f"API error {resp.status_code}: {resp.text}")
                else:
                    data = resp.json()

                    if data["answer"] == "INSUFFICIENT_GROUNDED_INFORMATION":
                        st.warning(
                            "⚠️ No sufficiently relevant guideline content was found for "
                            "this question. The system is refusing to guess rather than "
                            "risk an ungrounded clinical claim."
                        )
                    else:
                        st.markdown("### Answer")
                        st.write(data["answer"])

                        badge_col1, badge_col2, badge_col3 = st.columns(3)
                        with badge_col1:
                            if data["grounding_verified"]:
                                st.success("Grounding: ✅ fully verified")
                            else:
                                st.error("Grounding: ⚠️ one or more citations unverified")
                        with badge_col2:
                            st.metric("Grounding score", f"{data['grounding_score']*100:.0f}%")
                        with badge_col3:
                            st.metric("Latency", f"{data['latency_ms']:.0f} ms")

                        if data["citations"]:
                            st.markdown("### Citations")
                            df = pd.DataFrame(data["citations"])
                            st.dataframe(df, use_container_width=True, hide_index=True)

                        with st.expander("Clinical disclaimer"):
                            st.caption(data["disclaimer"])

# ---------------------------------------------------------------------------
# Tab 2: Ingest
# ---------------------------------------------------------------------------
with tab_ingest:
    st.markdown(
        "Upload a guideline PDF to add it to the searchable index. In "
        "production this would be an admin-only, access-controlled workflow."
    )

    uploaded_file = st.file_uploader("Guideline PDF", type=["pdf"])
    c1, c2 = st.columns(2)
    with c1:
        source_org_in = st.text_input("Source organization", placeholder="WHO")
        doc_title_in = st.text_input("Document title", placeholder="Guideline for ...")
    with c2:
        doc_type_in = st.selectbox("Document type", ["guideline", "protocol"], index=0)
        version_in = st.text_input("Version / year", placeholder="2023")

    if st.button("Ingest document", type="primary"):
        if not uploaded_file or not source_org_in or not doc_title_in:
            st.warning("Please provide a PDF file, source organization, and document title.")
        else:
            with st.spinner("Parsing, chunking, and indexing document..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    params = {
                        "source_org": source_org_in,
                        "doc_title": doc_title_in,
                        "doc_type": doc_type_in,
                        "version": version_in or None,
                    }
                    resp = requests.post(
                        f"{api_base_url}/ingest",
                        files=files,
                        params=params,
                        headers={"X-API-Key": api_key},
                        timeout=120,
                    )
                except requests.RequestException as e:
                    st.error(f"Request failed: {e}")
                    resp = None

            if resp is not None:
                if resp.ok:
                    data = resp.json()
                    st.success(
                        f"Ingested successfully — {data['chunks_created']} chunks created "
                        f"and added to the FAISS index."
                    )
                else:
                    st.error(f"Ingestion failed ({resp.status_code}): {resp.text}")

# ---------------------------------------------------------------------------
# Tab 3: Audit trail
# ---------------------------------------------------------------------------
with tab_audit:
    st.markdown(
        "Every query is logged for compliance and traceability. This view "
        "would be restricted to an admin role in a real deployment."
    )

    limit = st.slider("Number of recent entries", min_value=5, max_value=200, value=25)

    if st.button("Refresh audit log"):
        try:
            resp = requests.get(
                f"{api_base_url}/audit/recent",
                params={"limit": limit},
                headers={"X-API-Key": api_key},
                timeout=30,
            )
        except requests.RequestException as e:
            st.error(f"Request failed: {e}")
            resp = None

        if resp is not None:
            if resp.ok:
                logs = resp.json()["logs"]
                if not logs:
                    st.info("No audit entries yet — ask a question first.")
                else:
                    df = pd.DataFrame(logs)
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
                    df["grounding_verified"] = df["grounding_verified"].astype(bool)
                    st.dataframe(
                        df[
                            [
                                "timestamp",
                                "api_key_hash",
                                "query",
                                "grounding_verified",
                                "grounding_score",
                                "latency_ms",
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.error(f"Could not fetch audit log ({resp.status_code}): {resp.text}")
