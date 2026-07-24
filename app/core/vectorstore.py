import os
import pickle
import logging

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from app.core.reranker import CrossEncoderReranker
from langchain_core.documents import Document

from app.core.bm25 import BM25Retriever

logger = logging.getLogger(__name__)


class VectorStoreManager:

    def __init__(self, index_dir: str, embedding_model: str):

        self.index_dir = index_dir

        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            encode_kwargs={"normalize_embeddings": True},
        )

        self.store = None

        self.bm25 = BM25Retriever()
        self.reranker = None

        self._load_if_exists()

    # ----------------------------------------------------
    # Load existing indices
    # ----------------------------------------------------

    def _load_if_exists(self):

        faiss_file = os.path.join(self.index_dir, "index.faiss")
        bm25_file = os.path.join(self.index_dir, "bm25.pkl")

        if os.path.exists(faiss_file):

            logger.info("Loading existing FAISS index...")

            self.store = FAISS.load_local(
                self.index_dir,
                self.embeddings,
                allow_dangerous_deserialization=True,
            )

        if os.path.exists(bm25_file):

            logger.info("Loading existing BM25 index...")

            with open(bm25_file, "rb") as f:

                self.bm25 = pickle.load(f)

    # ----------------------------------------------------
    # Build indices
    # ----------------------------------------------------

    def build_from_documents(self, documents: list[Document]):

        logger.info("Building FAISS index in batches...")

        batch_size = 500

        self.store = None

        total_batches = (len(documents) + batch_size - 1) // batch_size

        for batch_num, start in enumerate(
            range(0, len(documents), batch_size),
            start=1,
        ):

            batch = documents[start:start + batch_size]

            logger.info(
                "FAISS batch %d/%d (%d documents)",
                batch_num,
                total_batches,
                len(batch),
            )

            if self.store is None:

                self.store = FAISS.from_documents(
                    batch,
                    self.embeddings,
                )

            else:

                self.store.add_documents(batch)

        logger.info("Building BM25 index...")

        self.bm25.build(documents)

        logger.info("Saving indices...")

        self.persist()

        logger.info("Finished building indices.")

    # ----------------------------------------------------
    # Save
    # ----------------------------------------------------

    def persist(self):

        os.makedirs(self.index_dir, exist_ok=True)

        self.store.save_local(self.index_dir)

        with open(
            os.path.join(self.index_dir, "bm25.pkl"),
            "wb",
        ) as f:

            pickle.dump(self.bm25, f)

    # ----------------------------------------------------
    # Hybrid Search
    # ----------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_filter=None,
        doc_type_filter=None,
    ):

        faiss_results = []

        if self.store is not None:

            faiss_results = self.store.similarity_search_with_relevance_scores(
                query,
                k=20,
            )

        bm25_results = self.bm25.search(
            query,
            k=20,
        )

                # --------------------------------------------------
        # Reciprocal Rank Fusion (RRF)
        # --------------------------------------------------

        K = 60

        rrf_scores = {}
        documents = {}

        # FAISS contribution
        for rank, (doc, _) in enumerate(faiss_results, start=1):

            key = (
                doc.metadata.get("doc_title"),
                doc.metadata.get("page"),
                hash(doc.page_content),
            )

            documents[key] = doc

            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (K + rank)

        # BM25 contribution
        for rank, (doc, _) in enumerate(bm25_results, start=1):

            key = (
                doc.metadata.get("doc_title"),
                doc.metadata.get("page"),
                hash(doc.page_content),
            )

            documents[key] = doc

            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (K + rank)

        # Sort by RRF score
        ranked = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []

        for key, score in ranked:

            doc = documents[key]

            if source_filter:

                if doc.metadata.get("source_org") not in source_filter:
                    continue

            if doc_type_filter:

                if doc.metadata.get("doc_type") != doc_type_filter:
                    continue

            results.append((doc, score))

        # CrossEncoder re-ranking
        # Lazy-load CrossEncoder only when needed
        if self.reranker is None:
            logger.info("Loading CrossEncoder reranker...")
            self.reranker = CrossEncoderReranker()
            
        results = self.reranker.rerank(
            query,
            results[:20],
            top_k=top_k,
        )

        logger.info("=" * 60)
        logger.info("CrossEncoder Top Results")

        for rank, (doc, score) in enumerate(results, start=1):
            logger.info(
                "%d | %.3f | %s | Page %s",
                rank,
                score,
                doc.metadata.get("doc_title"),
                doc.metadata.get("page"),
            )

        logger.info("=" * 60)

        return results