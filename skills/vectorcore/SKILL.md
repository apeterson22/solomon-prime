# Skill: VectorCore Memory

## Description

An integrated, tiered memory management system designed for optimal performance and cost-efficiency. It replaces the legacy flat-file `MEMORY.md` system with a structured, searchable architecture.

## Architecture

- **Tier 1 (Working):** In-session buffer for immediate context.
- **Tier 2 (Episodic):** Vector database on `jarvis3` for semantic search of conversation summaries.
- **Tier 3 (Archive):** Raw markdown logs in `~/memory` for permanent storage.

## Tools

- `memory_add(text)`: Adds a new memory/fact to the episodic store.
- `memory_search(query)`: Performs a semantic search on the episodic store.
- `memory_summarize()`: Summarizes the current working memory and commits it to the episodic store.

## Configuration

- **Vector DB Host:** `jarvis3`
- **Vector DB Port:** `8000` (Default for ChromaDB)
- **Collection Name:** `solomon_core_v1`
