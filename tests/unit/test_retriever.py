import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.memory.retriever import Retriever


@pytest.fixture
def mock_mcp():
    mcp = MagicMock()
    mcp.call_tool = AsyncMock()
    return mcp


class TestRetriever:
    @pytest.mark.asyncio
    async def test_retrieve_merges_results(self, mock_mcp):
        async def side_effect(name, args):
            if name == "search_vault":
                return [
                    {"id": "n1", "text": "DDP memory leak fix", "metadata": {"type": "checkpoint"}, "distance": 0.1},
                    {"id": "n2", "text": "GPU memory management", "metadata": {"type": "concept"}, "distance": 0.3},
                ]
            elif name == "query_graph":
                return [
                    {"subject": "DDP", "relation": "implies", "object": "Memory_Leak"},
                ]
            return []

        mock_mcp.call_tool = AsyncMock(side_effect=side_effect)

        retriever = Retriever(mock_mcp, top_k=3, keyword_weight=0.4, embedding_weight=0.6)
        results = await retriever.retrieve("Fix DDP memory leak")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_retrieve_empty(self, mock_mcp):
        mock_mcp.call_tool = AsyncMock(return_value=[])

        retriever = Retriever(mock_mcp, top_k=3)
        results = await retriever.retrieve("nonexistent query")
        assert results == []
