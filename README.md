# Tribal Mapper

A tool that uses AI to automatically extract and document tribal knowledge from codebases, producing concise "compass" context files for each module.

Inspired by [How Meta Used AI to Map Tribal Knowledge in Large-Scale Data Pipelines](https://engineering.fb.com/2026/04/06/developer-tools/how-meta-used-ai-to-map-tribal-knowledge-in-large-scale-data-pipelines/).

## How It Works

Tribal Mapper reads source files from a codebase module, sends them to an LLM (OpenAI GPT-4o via [Instructor](https://github.com/jxnl/instructor)), and produces a structured `ContextCompass` — a short, actionable reference following the "compass, not encyclopedia" principle:

1. **Quick Commands** — copy-paste operations for common tasks
2. **Key Files** — the 3–5 files you actually need
3. **Non-Obvious Patterns** — tribal knowledge buried in the code
4. **See Also** — cross-references to related modules

## Project Structure

```
tribal_mapper/
├── domain/           # Core domain model (ContextCompass)
├── application/      # Use cases and port interfaces
├── infrastructure/   # Adapters (LLM client, file system, storage)
├── presentation/     # CLI / API layer
└── main.py           # Entry point
```

## Requirements

- Python >= 3.13
- OpenAI API key

## Installation

```bash
pip install -e .
```

## Dependencies

- [instructor](https://pypi.org/project/instructor/) — structured LLM outputs
- [pydantic](https://pypi.org/project/pydantic/) — data validation and domain models
