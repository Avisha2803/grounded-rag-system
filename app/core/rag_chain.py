import re
import time
import logging
from app.core.prompts import SYSTEM_PROMPT, format_context
from app.core.vectorstore import VectorStoreManager
from app.config import Settings

logger = logging.getLogger(__name__)

CITATION_PATTERN = re.compile(
    r"\[Source:\s*(?P<org>[^,]+),\s*(?P<doc>[^,]+),\s*Section\s*(?P<section>[^,]+),\s*p\.(?P<page>\d+)\]"
)


def get_llm(settings: Settings):
    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            temperature=0,  # deterministic, low creative drift for clinical text
            max_tokens=1000,
        )
    elif settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model, api_key=settings.openai_api_key, temperature=0
        )
    elif settings.llm_provider == "groq":
        # Free tier, no credit card required — good default for demos/prototyping.
        # Get a key at https://console.groq.com/keys
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=settings.llm_model,  # e.g. "llama-3.3-70b-versatile"
            api_key=settings.groq_api_key,
            temperature=0,
            max_tokens=1000,
        )
    elif settings.llm_provider == "gemini":
        # Free tier, no credit card required — get a key at https://aistudio.google.com/apikey
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,  # e.g. "gemini-2.5-flash"
            google_api_key=settings.gemini_api_key,
            temperature=0,
            max_output_tokens=1000,
        )
    elif settings.llm_provider == "openrouter":
        # Free tier via OpenAI-compatible endpoint — use a model with the
        # ":free" suffix, e.g. "meta-llama/llama-3.3-70b-instruct:free"
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


class GroundedRAGChain:
    def __init__(self, vectorstore: VectorStoreManager, settings: Settings):
        self.vectorstore = vectorstore
        self.settings = settings
        self.llm = get_llm(settings)

    def _verify_grounding(self, answer: str, retrieved_docs) -> tuple[bool, float, list[dict]]:
        """
        Parses every citation the LLM produced and checks it against the actual
        set of retrieved (org, doc, section, page) tuples. This is the second
        line of defense against hallucinated citations — never trust the LLM
        to police itself.
        """
        valid_tuples = {
            (
                d.metadata.get("source_org", "").strip().lower(),
                d.metadata.get("doc_title", "").strip().lower(),
                str(d.metadata.get("section", "")).strip().lower(),
                str(d.metadata.get("page", "")).strip(),
            )
            for d, _ in retrieved_docs
        }

        found = CITATION_PATTERN.finditer(answer)
        total, matched = 0, 0
        citations = []
        for m in found:
            total += 1
            key = (
                m.group("org").strip().lower(),
                m.group("doc").strip().lower(),
                m.group("section").strip().lower(),
                m.group("page").strip(),
            )
            is_valid = key in valid_tuples
            if is_valid:
                matched += 1
            citations.append(
                {
                    "source_org": m.group("org").strip(),
                    "doc_title": m.group("doc").strip(),
                    "section": m.group("section").strip(),
                    "page": int(m.group("page")),
                    "verified": is_valid,
                }
            )

        if total == 0:
            return False, 0.0, citations
        score = matched / total
        return score == 1.0, score, citations

    def answer(
    self,
    question: str,
    source_filter: list[str] | None = None,
    doc_type_filter: str | None = None,
    top_k: int | None = None,
) -> dict:
        start = time.perf_counter()
        k = top_k or self.settings.top_k

        # -----------------------------
        # Retrieve documents
        # -----------------------------
        retrieved = self.vectorstore.search(
            question,
            top_k=k,
            source_filter=source_filter,
            doc_type_filter=doc_type_filter,
        )

        # -----------------------------
        # DEBUG OUTPUT
        # -----------------------------
        print("\n" + "=" * 80)
        print(f"QUESTION: {question}")
        print("=" * 80)

        if not retrieved:
            print("No documents returned from FAISS.")
        else:
            print(f"Retrieved {len(retrieved)} documents\n")

            for i, (doc, score) in enumerate(retrieved, start=1):
                print(f"[{i}] Score: {score:.4f}")
                print(f"Title: {doc.metadata.get('doc_title')}")
                print(f"Source: {doc.metadata.get('source_org')}")
                print(f"Page: {doc.metadata.get('page')}")
                print("Preview:")
                print(doc.page_content[:250].replace("\n", " "))
                print("-" * 80)

        print("=" * 80 + "\n")

        # -----------------------------
        # Apply threshold
        # -----------------------------
        filtered = [
            (doc, score)
            for doc, score in retrieved
            if score >= self.settings.score_threshold
        ]

        print(
            f"After threshold ({self.settings.score_threshold}) "
            f"-> {len(filtered)} documents remain."
        )

        retrieved = filtered

        if not retrieved:
            latency = (time.perf_counter() - start) * 1000

            return {
                "answer": "INSUFFICIENT_GROUNDED_INFORMATION",
                "citations": [],
                "grounding_verified": False,
                "grounding_score": 0.0,
                "latency_ms": latency,
                "retrieved_docs": [],
            }

        # -----------------------------
        # Build prompt
        # -----------------------------
        context = format_context(retrieved)

        prompt = SYSTEM_PROMPT.format(
            context=context,
            question=question,
        )

        # -----------------------------
        # LLM
        # -----------------------------
        raw_response = self.llm.invoke(prompt)

        raw_answer = (
            raw_response.content
            if hasattr(raw_response, "content")
            else str(raw_response)
        )

        verified, score, citations = self._verify_grounding(
            raw_answer,
            retrieved,
        )

        latency = (time.perf_counter() - start) * 1000

        return {
            "answer": raw_answer,
            "citations": citations,
            "grounding_verified": verified,
            "grounding_score": score,
            "latency_ms": latency,
            "retrieved_docs": retrieved,
        }