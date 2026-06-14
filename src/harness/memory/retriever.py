"""Hybrid retrieval: keyword extraction + embedding search with RRF fusion."""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieves relevant context from the vault using hybrid search."""

    def __init__(
        self,
        mcp_client: Any,
        top_k: int = 5,
        keyword_weight: float = 0.4,
        embedding_weight: float = 0.6,
    ):
        self._mcp = mcp_client
        self._top_k = top_k
        self._kw_weight = keyword_weight
        self._emb_weight = embedding_weight

    async def retrieve(self, query: str) -> list[dict]:
        """Retrieve relevant context for a query using RRF fusion."""
        embedding_task = asyncio.create_task(
            self._mcp.call_tool("search_vault", {"query": query, "top_k": self._top_k})
        )
        keyword_task = asyncio.create_task(
            self._extract_and_query_graph(query)
        )

        embedding_results, keyword_results = await asyncio.gather(
            embedding_task, keyword_task
        )

        if not embedding_results and not keyword_results:
            return []

        scores: dict[str, float] = {}
        items: dict[str, dict] = {}

        if embedding_results:
            for rank, result in enumerate(embedding_results):
                item_id = result.get("id", f"emb_{rank}")
                scores[item_id] = scores.get(item_id, 0) + self._emb_weight / (60 + rank)
                items[item_id] = {
                    "text": result.get("text", ""),
                    "type": result.get("metadata", {}).get("type", "unknown"),
                    "id": item_id,
                }

        if keyword_results:
            for rank, triple in enumerate(keyword_results):
                item_id = f"graph_{triple.get('subject', '')}_{triple.get('relation', '')}"
                scores[item_id] = scores.get(item_id, 0) + self._kw_weight / (60 + rank)
                items[item_id] = {
                    "text": f"{triple['subject']} --{triple['relation']}--> {triple['object']}",
                    "type": "graph_triple",
                    "subject": triple.get("subject"),
                    "relation": triple.get("relation"),
                    "object": triple.get("object"),
                }

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[: self._top_k]
        return [items[item_id] for item_id, _ in ranked]

    async def _extract_and_query_graph(self, query: str) -> list[dict]:
        """Extract keywords and query the graph."""
        keywords = self._extract_keywords(query)

        all_triples = []
        for keyword in keywords:
            triples = await self._mcp.call_tool("query_graph", {"subject": keyword})
            if triples:
                all_triples.extend(triples)
            triples = await self._mcp.call_tool("query_graph", {"object": keyword})
            if triples:
                all_triples.extend(triples)

        return all_triples

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract keywords from a query."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "out", "off", "over", "under", "again",
            "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "both", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "just", "because", "but",
            "and", "or", "if", "while", "about", "up", "it", "its", "this",
            "that", "these", "those", "i", "me", "my", "we", "our", "you",
            "your", "he", "him", "his", "she", "her", "they", "them", "their",
            "fix", "help", "want", "need", "use", "make", "get",
        }
        words = query.lower().split()
        keywords = [w.strip(".,!?;:") for w in words if w.lower() not in stop_words and len(w) > 2]
        return keywords[:5]
