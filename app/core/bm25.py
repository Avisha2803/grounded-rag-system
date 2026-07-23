from rank_bm25 import BM25Okapi
from langchain_core.documents import Document


class BM25Retriever:

    def __init__(self):
        self.documents = []
        self.tokenized_corpus = []
        self.bm25 = None

    def build(self, documents: list[Document]):
        """
        Build BM25 index from LangChain Documents.
        """

        self.documents = documents

        self.tokenized_corpus = [
            doc.page_content.lower().split()
            for doc in documents
        ]

        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search(
        self,
        query: str,
        k: int = 5,
    ):

        if self.bm25 is None:
            return []

        tokenized_query = query.lower().split()

        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(self.documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked[:k]