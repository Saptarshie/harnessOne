"""MCP server for Obsidian-style vault operations."""

import sys
import json
import logging
import argparse
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_server.vault import Vault
from mcp_server.graph import KnowledgeGraph
from mcp_server.embeddings import EmbeddingStore

logger = logging.getLogger(__name__)


def create_server(vault_path: str, embedding_model: str | None = None) -> Server:
    """Create and configure the MCP server."""
    vault = Vault(vault_path)
    graph = KnowledgeGraph(vault)

    chroma_path = str(Path(vault_path) / ".chromadb")
    embed_store = EmbeddingStore(
        persist_dir=chroma_path,
        model_name=embedding_model,
    )

    server = Server("cognitive-harness-vault")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="query_graph",
                description="Query the knowledge graph for triples (subject, relation, object).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "relation": {"type": "string"},
                        "object": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="get_derivation_tree",
                description="Get the derivation tree for a concept.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "concept": {"type": "string"},
                    },
                    "required": ["concept"],
                },
            ),
            Tool(
                name="write_note",
                description="Create or update a note in the vault.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "links": {"type": "array", "items": {"type": "string"}},
                        "note_type": {"type": "string", "enum": ["checkpoint", "concept", "derivation"]},
                        "relations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "subject": {"type": "string"},
                                    "relation": {"type": "string"},
                                    "object": {"type": "string"},
                                },
                            },
                        },
                    },
                    "required": ["title", "content", "note_type"],
                },
            ),
            Tool(
                name="add_relation",
                description="Add a relation triple to the knowledge graph.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "relation": {"type": "string"},
                        "object": {"type": "string"},
                    },
                    "required": ["subject", "relation", "object"],
                },
            ),
            Tool(
                name="search_vault",
                description="Search the vault using hybrid retrieval (keyword + embedding).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "query_graph":
            triples = graph.query(
                subject=arguments.get("subject"),
                relation=arguments.get("relation"),
                object=arguments.get("object"),
            )
            return [TextContent(type="text", text=json.dumps(triples))]

        elif name == "get_derivation_tree":
            tree = graph.get_derivation_tree(arguments["concept"])
            return [TextContent(type="text", text=json.dumps(tree))]

        elif name == "write_note":
            result = vault.write_note(
                title=arguments["title"],
                content=arguments["content"],
                tags=arguments.get("tags", []),
                links=arguments.get("links", []),
                note_type=arguments["note_type"],
                relations=arguments.get("relations"),
            )
            embed_store.add(
                doc_id=result["id"],
                text=arguments["content"],
                metadata={"type": arguments["note_type"], "title": arguments["title"]},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "add_relation":
            graph.add_relation(
                arguments["subject"],
                arguments["relation"],
                arguments["object"],
            )
            return [TextContent(type="text", text=json.dumps({"success": True}))]

        elif name == "search_vault":
            results = embed_store.search(
                query=arguments["query"],
                top_k=arguments.get("top_k", 5),
            )
            return [TextContent(type="text", text=json.dumps(results))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    return server


async def run_server(vault_path: str, embedding_model: str | None = None):
    """Run the MCP server on stdio."""
    server = create_server(vault_path, embedding_model)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    parser = argparse.ArgumentParser(description="Cognitive Harness Vault MCP Server")
    parser.add_argument("--vault", default="vault", help="Path to vault directory")
    parser.add_argument("--embedding-model", default=None, help="Embedding model name")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server(args.vault, args.embedding_model))


if __name__ == "__main__":
    import asyncio
    main()
