from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    """
    Re-ranks retrieved chunks using a CrossEncoder.

    Unlike embeddings (bi-encoder), the CrossEncoder jointly
    encodes the query and document and gives a much more
    accurate relevance score.
    """

    def __init__(
        self,
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query,
        docs_with_scores,
        top_k=5,
    ):
        if not docs_with_scores:
            return []

        pairs = [
            (query, doc.page_content)
            for doc, _ in docs_with_scores
        ]

        scores = self.model.predict(pairs)

        reranked = []

        for (doc, _), score in zip(
            docs_with_scores,
            scores,
        ):
            reranked.append(
                (
                    doc,
                    float(score),
                )
            )

        reranked.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        return reranked[:top_k]