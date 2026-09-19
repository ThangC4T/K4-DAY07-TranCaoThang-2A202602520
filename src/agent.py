from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        contexts = [r["content"] for r in results if "content" in r]
        context_str = "\n\n".join(f"Context {i + 1}:\n{c}" for i, c in enumerate(contexts))
        prompt = (
            f"Based on the following context, answer the question.\n\n"
            f"{context_str}\n\n"
            f"Question: {question}\n"
            f"Answer:"
        )
        return self.llm_fn(prompt)
