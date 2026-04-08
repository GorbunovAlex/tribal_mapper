# Tribal Mapper

AI-powered tool that indexes codebases into structured context files (`.ai_context/`) and routes the right context to developers at query time.

Inspired by [How Meta Used AI to Map Tribal Knowledge in Large-Scale Data Pipelines](https://engineering.fb.com/2026/04/06/developer-tools/how-meta-used-ai-to-map-tribal-knowledge-in-large-scale-data-pipelines/).

## How It Works

Tribal Mapper has two bounded contexts:

**Indexing** — traverses a repository, runs each module through a multi-agent extraction pipeline (Explorer → Analyst → Writer → Critic), and persists a structured `ContextCompass` to `.ai_context/<module>.json`.

**Routing** — accepts a natural-language query, scores available compasses for relevance, filters out stale ones, and returns an enriched prompt with the top-N context blocks injected.

Each `ContextCompass` contains:

1. **Quick Commands** — copy-paste operations for common tasks
2. **Key Files** — the 3–5 files you actually need
3. **Non-Obvious Patterns** — tribal knowledge buried in the code
4. **Gotchas** — common pitfalls and surprises
5. **See Also** — cross-references to related modules

## Project Structure

```
tribal_mapper/
├── domain/
│   ├── entities/          # CodeModule, CompassDraft, ContextCompass
│   ├── value_objects/     # TokenCount, FreshnessPolicy, AgentMessage
│   ├── policies/          # CompassPromotionPolicy
│   └── exceptions.py
├── application/
│   ├── interfaces/        # ExtractionPipeline, CompassRepository, CodeRepository, RelevanceScorer
│   ├── use_cases/         # IndexModule, IndexCodebase, RouteQuery
│   └── builders/          # CompassDraftBuilder
├── infrastructure/
│   ├── ai/                # LangGraph pipeline, AgentFactory, EmbeddingScorer
│   ├── storage/           # LocalFileCompassRepository (.ai_context/ JSON)
│   ├── vcs/               # GitRepoTraversal (.mapperignore support)
│   └── di_container.py    # Wires everything together
├── presentation/
│   └── cli.py             # `mapper index ./repo`
├── config/
│   ├── mapper.yaml        # All settings: API key, freshness, agents, etc.
│   ├── example.yaml       # Template — copy to mapper.yaml
│   └── loader.py          # Singleton config loader
└── main.py
```

## Requirements

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

## Installation

```bash
uv sync
```

For development (includes pre-commit, pytest):

```bash
uv sync --group dev
uv run pre-commit install
```

Copy the example config and add your API key:

```bash
cp config/example.yaml config/mapper.yaml
# Edit config/mapper.yaml and set openai_api_key
```

## Usage

### Index a codebase

```bash
python main.py index ./my-project
```

### Index a single module

```bash
python main.py index ./my-project --module src/auth.py
```

## Configuration

All config lives in `config/mapper.yaml`. Copy `config/example.yaml` to get started:

| Setting | Default | Description |
|---|---|---|
| `openai_api_key` | `$OPENAI_API_KEY` | OpenAI API key (falls back to env var) |
| `freshness.max_days_old` | 7 | Days before a compass is considered stale |
| `freshness.max_commits_old` | 10 | Commits before a compass is considered stale |
| `token_ceiling` | 1000 | Max estimated tokens per compass |
| `extensions` | `.py`, `.js`, `.ts`, … | File extensions to index |
| `embedding_model` | `text-embedding-3-small` | OpenAI embedding model |
| `agents.*` | see example.yaml | Agent models, temperatures, system prompts |

`mapper.yaml` is gitignored — your API key stays local.

## Dependencies

- [pydantic](https://pypi.org/project/pydantic/) — data validation and domain models
- [langchain-openai](https://pypi.org/project/langchain-openai/) — LLM and embedding clients
- [langgraph](https://pypi.org/project/langgraph/) — multi-agent pipeline orchestration
- [numpy](https://pypi.org/project/numpy/) — cosine similarity for embedding scoring
- [pyyaml](https://pypi.org/project/pyyaml/) — config loading
