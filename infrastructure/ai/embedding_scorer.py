import numpy as np
from langchain_openai import OpenAIEmbeddings

from application.interfaces.relevance_scorer import RelevanceScorerInterface
from domain.entities.context_compass import ContextCompass


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a)
    vb = np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def _compass_text(compass: ContextCompass) -> str:
    parts = [
        compass.quick_commands,
        " ".join(compass.key_files),
        compass.non_obvious_patterns,
        compass.gotchas,
    ]
    return " ".join(p for p in parts if p)


class EmbeddingRelevanceScorer(RelevanceScorerInterface):
    def __init__(
        self, model: str = "text-embedding-3-small", api_key: str = ""
    ) -> None:
        self._embeddings = OpenAIEmbeddings(model=model, api_key=api_key or None)

    def score(
        self, query: str, compasses: list[ContextCompass]
    ) -> list[tuple[ContextCompass, float]]:
        if not compasses:
            return []

        if not query.strip():
            return [(c, 0.0) for c in compasses]

        texts = [_compass_text(c) for c in compasses]
        all_texts = [query] + texts
        all_vectors = self._embeddings.embed_documents(all_texts)

        query_vec = all_vectors[0]
        compass_vecs = all_vectors[1:]

        return [
            (compass, _cosine_similarity(query_vec, cvec))
            for compass, cvec in zip(compasses, compass_vecs, strict=False)
        ]
