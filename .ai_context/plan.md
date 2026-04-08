# AI Tribal Knowledge Mapper — Revised Architecture Plan

## Overview

A Python system that indexes codebases into structured context files (`.ai_context/`) and routes the right context to developers at query time. The design prioritises long-term maintainability over tooling trends, with a strict DDD layering strategy that isolates AI infrastructure from core business logic.

---

## 1. Bounded Contexts

Rather than three separate contexts, the system is split into two: one for **indexing** (building knowledge) and one for **routing** (serving knowledge). These are genuinely independent — they have different triggers, different consumers, and could eventually be owned by different teams.

### 1.1 Indexing Context
Responsible for traversing a repository, extracting tribal knowledge, and persisting structured context files.

- Triggered manually (CLI) or on a schedule/webhook
- Consumers: developers running `mapper index`
- Output: `.ai_context/<module>.json`

### 1.2 Routing Context
Responsible for accepting a developer's natural-language query, selecting the most relevant context files, and returning an enriched prompt payload.

- Triggered on every developer query
- Consumers: IDE plugins, chat interfaces, API clients
- Output: a `RoutedPrompt` containing the original query + injected context

These two contexts share no runtime state. They communicate only through the persisted `.ai_context/` artefacts — one writes, one reads.

---

## 2. Domain Layer

Zero external dependencies. No LangChain, no OpenAI SDK, no file system imports. Pure Python and Pydantic.

### 2.1 Entities

**`CodeModule`**
- Identity: absolute file path within the repository
- Carries: raw source text, detected language, last-modified timestamp
- Responsible for nothing beyond its own identity and data

**`CompassDraft`**
- An intermediate, mutable entity produced during extraction
- Can be in an incomplete state — missing sections are allowed
- Holds: quick commands, key files, non-obvious patterns, gotchas, see-also links
- Has no validity constraints itself; it is just a container

**`ContextCompass`**
- The final, immutable output of the Indexing Context
- Promoted from a `CompassDraft` only after passing domain validation
- Carries: all five sections, a `TokenCount` value object, a `FreshnessPolicy` value object
- Owns the `is_stale()` method — the Routing Context calls this, not a separate use case

### 2.2 Value Objects

**`TokenCount`**
- Immutable integer
- Construction raises `ContextTooLarge` if count exceeds the configured ceiling (default: 1,000 tokens / 35 lines)

**`FreshnessPolicy`**
- Immutable rule set: stale after N days OR after M commits since last index
- Owned by `ContextCompass`, evaluated via `is_stale(current_date, commit_count)`
- Default: stale after 7 days or 10 commits

**`AgentMessage`**
- The typed payload passed between agents in the extraction pipeline
- Fields: `source_module`, `stage` (enum: EXPLORE | ANALYSE | WRITE | CRITIQUE), `content`, `confidence_score`
- Defined in the domain layer so the contract is tooling-agnostic

### 2.3 Domain Policies

**`CompassPromotionPolicy`**
- Takes a `CompassDraft` and a set of rules
- Raises `IncompleteDraft` if required sections (quick commands, key files) are missing
- Raises `ContextTooLarge` if the assembled token count exceeds ceiling
- On success, constructs and returns an immutable `ContextCompass`

### 2.4 Domain Exceptions

```
DomainError
├── ContextTooLarge
├── IncompleteDraft
├── StaleCompass
└── UnroutableQuery
```

---

## 3. Application Layer

Coordinates domain objects and infrastructure. Contains no business logic of its own — it delegates everything to the domain or infrastructure.

### 3.1 Interfaces (for Dependency Injection)

Defined here so the application layer depends on abstractions, not implementations.

```python
class ExtractionPipelineInterface(ABC):
    def run(self, module: CodeModule) -> CompassDraft: ...

class CompassRepositoryInterface(ABC):
    def save(self, compass: ContextCompass, module: CodeModule) -> None: ...
    def load(self, module_path: str) -> ContextCompass | None: ...
    def list_all(self) -> list[ContextCompass]: ...

class CodeRepositoryInterface(ABC):
    def list_modules(self, root: str) -> list[CodeModule]: ...
    def get_commit_count_since(self, module: CodeModule, since: datetime) -> int: ...
```

### 3.2 Use Cases

**`IndexModuleUseCase`**
1. Accepts a `CodeModule`
2. Calls `ExtractionPipelineInterface.run()` → `CompassDraft`
3. Passes draft to `CompassPromotionPolicy` → `ContextCompass`
4. Calls `CompassRepositoryInterface.save()`
5. On domain error, logs and skips (does not crash the indexing run)

**`IndexCodebaseUseCase`**
1. Calls `CodeRepositoryInterface.list_modules()`
2. Dispatches each to `IndexModuleUseCase` (parallelised with `asyncio`)
3. Returns an `IndexingReport` (counts: succeeded, skipped, failed)

**`RouteQueryUseCase`**
1. Accepts a raw developer query string
2. Loads all `ContextCompass` objects via `CompassRepositoryInterface.list_all()`
3. Filters out stale compasses using `compass.is_stale()`
4. Scores compasses against the query via `RelevanceScorerInterface`
5. Assembles and returns a `RoutedPrompt` (query + top-N context blocks)

**Note:** `ValidateFreshnessUseCase` from the original plan is eliminated. Freshness is a domain concern evaluated inline inside `RouteQueryUseCase`. There is no separate use case for it.

### 3.3 The Builder — `CompassDraftBuilder`

Used exclusively inside the `ExtractionPipelineInterface` implementations. Not used in the application layer itself.

The builder assembles a `CompassDraft` section by section as agent messages arrive. It does not validate; it only constructs. Validation is strictly the job of `CompassPromotionPolicy`.

```python
builder = CompassDraftBuilder()
builder.add_quick_commands(agent_message.content)
builder.add_key_files(agent_message.content)
builder.add_patterns(agent_message.content)
draft = builder.build()  # Returns CompassDraft, never raises
```

---

## 4. Infrastructure Layer

### 4.1 Agent Pipeline — `LangGraphExtractionPipeline`

Implements `ExtractionPipelineInterface`. This is the only place LangGraph is known to exist.

**Agent sequence:** `Explorer → Analyst → Writer → Critic`

Each agent receives and returns a typed `AgentMessage`. The pipeline does not use shared mutable state — each agent's output is the next agent's explicit input. This makes partial failure recoverable: if the Critic rejects the Writer's output, the pipeline retries the Writer stage only, up to a configured retry limit.

**`AgentFactory`** (Factory Pattern + GRASP Creator)
- Creates each agent with its system prompt, model config, temperature, and bound tools
- Returns `IAgent` — the rest of the pipeline never sees a LangGraph node directly
- Configuration loaded from `agents.yaml`, not hardcoded

```python
class AgentFactory:
    def create_explorer(self) -> IAgent: ...
    def create_analyst(self) -> IAgent: ...
    def create_writer(self) -> IAgent: ...
    def create_critic(self) -> IAgent: ...
```

### 4.2 Storage — `LocalFileCompassRepository`

Implements `CompassRepositoryInterface`. Persists `ContextCompass` as JSON to `.ai_context/<module_path>.json`. Path sanitisation is handled here, not in the domain.

### 4.3 Code Traversal — `GitRepoTraversal`

Implements `CodeRepositoryInterface`. Walks the file tree, respects `.mapperignore`, and queries git for commit counts. Returns `CodeModule` objects.

### 4.4 Relevance Scoring — `EmbeddingRelevanceScorer`

Implements `RelevanceScorerInterface`. Uses embeddings to score each `ContextCompass` against a query. Swappable with a keyword-based scorer for offline/testing environments.

### 4.5 Dependency Injection Container — `di_container.py`

Wires everything together at startup. No business logic here — only binding.

```python
container.bind(ExtractionPipelineInterface, LangGraphExtractionPipeline)
container.bind(CompassRepositoryInterface, LocalFileCompassRepository)
container.bind(CodeRepositoryInterface, GitRepoTraversal)
container.bind(RelevanceScorerInterface, EmbeddingRelevanceScorer)
```

Swapping LangGraph for CrewAI means changing one line in this file.

---

## 5. Presentation Layer

### `cli.py`
Entry point for indexing. Accepts a repo path, invokes `IndexCodebaseUseCase`, prints the `IndexingReport`.

```bash
mapper index ./my-project
mapper index ./my-project --module src/auth/
```

### `api.py`
Entry point for routing. A lightweight FastAPI app with one meaningful endpoint.

```
POST /route
Body: { "query": "how does auth token refresh work?" }
Response: { "context_blocks": [...], "enriched_prompt": "..." }
```

The routing logic — selecting which context files to inject — lives in `RouteQueryUseCase`, not here. This file is only HTTP plumbing.

---

## 6. Directory Structure

```
tribal_mapper/
├── domain/
│   ├── entities/
│   │   ├── code_module.py
│   │   ├── compass_draft.py
│   │   └── context_compass.py
│   ├── value_objects/
│   │   ├── token_count.py
│   │   ├── freshness_policy.py
│   │   └── agent_message.py          # Inter-agent contract
│   ├── policies/
│   │   └── compass_promotion.py      # CompassPromotionPolicy
│   └── exceptions.py
│
├── application/
│   ├── interfaces/
│   │   ├── extraction_pipeline.py
│   │   ├── compass_repository.py
│   │   ├── code_repository.py
│   │   └── relevance_scorer.py
│   ├── use_cases/
│   │   ├── index_module.py
│   │   ├── index_codebase.py
│   │   └── route_query.py
│   └── builders/
│       └── compass_draft_builder.py  # Assembly only, no validation
│
├── infrastructure/
│   ├── ai/
│   │   ├── langgraph_pipeline.py     # Implements ExtractionPipelineInterface
│   │   ├── agent_factory.py          # Factory Pattern
│   │   └── embedding_scorer.py       # Implements RelevanceScorerInterface
│   ├── storage/
│   │   └── local_fs_repository.py    # Implements CompassRepositoryInterface
│   ├── vcs/
│   │   └── git_repo_traversal.py     # Implements CodeRepositoryInterface
│   └── di_container.py
│
├── presentation/
│   ├── cli.py
│   └── api.py
│
├── agents.yaml                       # Agent configs (prompts, models, temperature)
└── mapper.yaml                       # Freshness policy defaults, token ceilings
```

---

## 7. Key Design Decisions — Summary

| Decision | Rationale |
|---|---|
| Two bounded contexts, not three | Discovery and extraction are too coupled at runtime to warrant independent contexts in phase one |
| `CompassDraft` as intermediate entity | Separates the concerns of assembly (Builder) and validation (Policy) cleanly |
| `FreshnessPolicy` as value object | Makes staleness rules explicit and testable without a dedicated use case |
| `AgentMessage` defined in domain layer | The inter-agent contract is business logic, not infrastructure |
| Builder never raises | Construction and validation are different responsibilities; mixing them hides intent |
| Agent pipeline uses explicit message passing | Avoids shared mutable state; enables per-stage retry without restarting the full pipeline |
| `RouteQueryUseCase` owns context selection | This is the core product value; it must live in the application layer, not the presentation layer |