# Your Joyful Coding Platform — Phased Build Plan

This document is the **build companion** to `WORKFLOW_ARCHITECTURE_C.md` and `AGENT_ARCHITECTURE.md`. It lists the exact scripts to create or update in each phase, and what each function does. Read the architecture docs first for *why*; this file tells you *what to type and where*.

> **Total estimate:** ~6 weeks, one phase per week. Don't skip ahead — each phase produces a runnable, testable slice.

---

## Status legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete

---

## Phase 0 — Foundation (Week 1)

**Goal:** Blackboard + Coordinator + a trivial echoing Mentor. End-to-end loop: user types → coordinator hands out token → mentor replies.

### Scripts to create / update

| File | Action | Purpose |
|---|---|---|
| `src/services/blackboard/sections.py` | **Create** | Catalog of blackboard section names and their write-permission matrix |
| `src/services/blackboard/store.py` | **Create** | Postgres JSONB-backed CRUD with optimistic concurrency |
| `src/services/blackboard/proposal.py` | **Create** | Pydantic model for the `Proposal` envelope |
| `src/services/blackboard/coordinator.py` | **Create** | The state machine (this is the heart of the system) |
| `src/services/agents/mentor.py` | **Create** | Trivial Mentor that echoes the user back |
| `src/services/blackboard/__init__.py` | **Create** | Module exports |
| `src/services/agents/__init__.py` | **Create** | Module exports |
| `src/db/models.py` | **Update** | Add `BlackboardSection` and `Session` tables |
| `src/api/sessions.py` | **Create** | REST endpoints to open / close a coding session |
| `src/main.py` | **Update** | Register the new sessions router |
| `tests/blackboard/test_store.py` | **Create** | Round-trip and version-conflict tests |
| `tests/blackboard/test_coordinator.py` | **Create** | State machine transitions and token grants |
| `requirements.txt` | **Update** | (No new deps expected for this phase) |

### Functions to write

#### `src/services/blackboard/sections.py`

| Function | What it does |
|---|---|
| `class SectionName(str, Enum)` | Enumerates the canonical section ids (`CODE_SNAPSHOT`, `TIMELINE`, `STUCK_HYPOTHESES`, `OPEN_QUESTIONS_FOR_USER`, `LEARNING_PLAN_DRAFT`, `PROBLEM_CONTEXT`, `USER_PROFILE`) |
| `WRITE_PERMISSIONS: dict[SectionName, set[str]]` | Static table mapping each section to the agent names that may write it (e.g. only `analyzer` writes `stuck_hypotheses`) |
| `READ_PERMISSIONS: dict[SectionName, set[str]]` | Who can read each section; defaults to "all" if absent |
| `get_writer(section) -> str` | Lookup helper used by the coordinator when validating a proposal |

#### `src/services/blackboard/proposal.py`

| Function | What it does |
|---|---|
| `class Proposal(BaseModel)` | Pydantic model: `proposal_id`, `session_id`, `from_agent`, `section`, `base_version`, `operation` (`upsert`/`append`/`delete`), `payload`, `rationale`, `requires_speaking` |
| `class ProposalOperation(str, Enum)` | Enumerates valid operations per section |
| `validate(proposal, write_perms) -> None` | Raises `PermissionError` if `from_agent` not in `write_perms[section]` |
| `to_envelope(proposal) -> dict` | Serializes for the event log |

#### `src/services/blackboard/store.py`

| Function | What it does |
|---|---|
| `class BlackboardStore` | Main class; takes a SQLAlchemy session in constructor |
| `async def read(self, session_id, section) -> tuple[Any, int]` | Returns `(payload, version)` tuple; `version` is the monotonic counter |
| `async def commit(self, session_id, section, expected_version, payload, agent) -> int` | Performs optimistic CAS in Postgres; bumps version; returns new version. Raises `VersionConflict` on mismatch |
| `async def append_event(self, event)` | Append-only insert into the timeline table for replay |
| `async def get_section_versions(self, session_id) -> dict` | Used by observability and tests |

#### `src/services/blackboard/coordinator.py`

| Function | What it does |
|---|---|
| `class Coordinator` | Holds `BlackboardStore` + active proposals queue + speaking-token state |
| `async def submit(self, proposal) -> Decision` | Validates write permission → checks version → commits (or rejects with reason) |
| `async def request_speaking_token(self, agent, priority) -> Token` | Hands out a token honoring P0–P5 ordering and the 90-second throttling rule |
| `async def on_event(self, event)` | Central event hook (called by the WS endpoint) that wakes up the right agents |
| `def _decide_priority(self, proposal) -> int` | Maps a section + payload to a P0–P5 priority |
| `def _should_suppress_p3(self) -> bool` | Implements the P3 suppression rules from `WORKFLOW_ARCHITECTURE_C.md` §3.5 |

#### `src/services/agents/mentor.py`

| Function | What it does |
|---|---|
| `class Mentor` | Holds a handle to `Coordinator` |
| `async def on_token_granted(self, token)` | Called when the coordinator gives this Mentor the floor |
| `async def _echo(self, user_message)` | **Phase 0 placeholder:** returns the user text wrapped in "Echo: ..." |
| `async def draft(self, proposal) -> MentorMessage` | Builds a `MentorMessage` proposal for the coordinator to commit to `open_questions_for_user` |

#### `src/db/models.py` (additions)

| Class | What it does |
|---|---|
| `class BlackboardSection(Base)` | `id`, `session_id` (FK), `section_name`, `payload` (JSONB), `version` (int, indexed), `updated_at` |
| `class Session(Base)` | `id`, `user_id` (FK), `problem_id`, `started_at`, `ended_at`, `status` |
| `class TimelineEvent(Base)` | `id`, `session_id` (FK), `ts`, `kind` (enum), `payload` (JSONB), `agent`, `proposal_id` |

#### `src/api/sessions.py`

| Endpoint | What it does |
|---|---|
| `POST /sessions` | Creates a new coding session, returns session_id |
| `GET /sessions/{id}` | Returns the session and its blackboard snapshot |
| `POST /sessions/{id}/close` | Marks the session ended; triggers Planner in Phase 3 |

#### `tests/blackboard/test_store.py`

| Test | What it asserts |
|---|---|
| `test_round_trip` | `commit` then `read` returns the same payload and version=1 |
| `test_version_conflict` | Two concurrent `commit`s with the same `expected_version` — exactly one wins |
| `test_event_log_appended` | Every commit produces a `TimelineEvent` row |

### Phase 0 done-when

- [ ] `uvicorn src.main:app --reload` boots
- [ ] `POST /sessions` → opens session, returns id
- [ ] User sends a message → coordinator grants token → mentor echoes → user sees reply
- [ ] All Phase 0 tests pass

---

## Phase 1 — Single agent loop (Week 2)

**Goal:** Real `Analyzer` writes `stuck_hypotheses`. Real `Mentor` turns a hypothesis into a question. End-to-end proactive help works (P3 path).

### Scripts to create / update

| File | Action | Purpose |
|---|---|---|
| `src/services/agents/analyzer.py` | **Create** | LLM-powered analyzer |
| `src/services/llm/client.py` | **Create** | Thin LLM client wrapper (provider-agnostic) |
| `src/services/agents/mentor.py` | **Update** | Replace echo with real drafting from hypotheses |
| `src/services/agents/reflection.py` | **Create** | Stub that always approves |
| `src/services/blackboard/coordinator.py` | **Update** | Wire up the P3 path: idle-tick → analyzer → mentor → reflection |
| `src/api/ws.py` | **Create** | WebSocket endpoint for the editor |
| `src/main.py` | **Update** | Register WS router and idle-tick scheduler |
| `src/services/idle.py` | **Create** | Per-session idle tracker (60s threshold) |
| `requirements.txt` | **Update** | Add `httpx`, `anthropic` or `openai`, `pydantic-settings` |
| `tests/agents/test_analyzer.py` | **Create** | Deterministic stub-LLM tests |
| `tests/e2e/test_proactive_help.py` | **Create** | One-minute idle → user sees mentor message |

### Functions to write

#### `src/services/llm/client.py`

| Function | What it does |
|---|---|
| `class LLMClient` | Wraps the chosen provider; takes API key from `core/config.py` |
| `async def complete(self, prompt, *, model, json_schema=None, temperature=0) -> str` | Single-shot completion |
| `async def stream(self, prompt, *, model) -> AsyncIterator[str]` | Streaming completion for the chat panel |
| `def with_json_schema(self, schema: dict)` | Helper to set `response_format` for the analyzer |

#### `src/services/agents/analyzer.py`

| Function | What it does |
|---|---|
| `class Analyzer` | Owns its `LLMClient`; subscribes to events from coordinator |
| `async def on_code_change(self, snapshot)` | Triggered on every keystroke (debounced) |
| `async def on_idle_tick(self, session_id)` | Triggered every 60s of user inactivity |
| `async def _infer_hypotheses(self, snapshot, timeline) -> list[Hypothesis]` | Calls LLM with JSON schema; returns 0–3 hypotheses each with `{claim, confidence, evidence}` |
| `async def _commit(self, hypotheses)` | Wraps in `Proposal(operation="upsert", section=STUCK_HYPOTHESES)` and submits to coordinator |

#### `src/services/agents/mentor.py` (update)

| Function | What it does |
|---|---|
| `async def draft_from_hypothesis(self, h: Hypothesis) -> MentorMessage` | Calls LLM to turn a hypothesis into a single Socratic question |
| `async def on_token_granted(self, token)` | Reads current top-confidence hypothesis, drafts, submits proposal to `open_questions_for_user` |

#### `src/services/agents/reflection.py`

| Function | What it does |
|---|---|
| `class Reflection` | Phase 1: stub |
| `async def review(self, message) -> Verdict` | Returns `Verdict.APPROVE` unconditionally with a `{"reason": "phase-1-stub"}` trace |

#### `src/services/idle.py`

| Function | What it does |
|---|---|
| `class IdleTracker` | In-memory map `session_id -> last_event_ts` |
| `def touch(self, session_id)` | Called from the WS endpoint on every event |
| `def is_idle(self, session_id, threshold_s=60) -> bool` | Used by the periodic ticker |

#### `src/api/ws.py`

| Function | What it does |
|---|---|
| `@app.websocket("/ws/sessions/{id}")` | Auth → accept → loop: receive event → forward to coordinator → push mentor messages back |
| `async def _on_client_event(ws, event)` | Touch idle tracker; forward to coordinator |
| `async def _push_to_client(ws, message)` | Single outbound channel for mentor messages |

### Phase 1 done-when

- [ ] User is idle for 60 s → mentor message appears in their panel
- [ ] User passes a test → next mentor message is suppressed (if within 15 s)
- [ ] Two consecutive mentor messages are at least 90 s apart
- [ ] `tests/e2e/test_proactive_help.py` passes

---

## Phase 2 — Real Reflection (Week 3)

**Goal:** Replace the stub `Reflection` with a real LLM check. Wire the two-phase commit for `open_questions_for_user`.

### Scripts to create / update

| File | Action | Purpose |
|---|---|---|
| `src/services/agents/reflection.py` | **Update** | Real LLM-based review |
| `src/services/blackboard/coordinator.py` | **Update** | Two-phase commit for `open_questions_for_user` (draft → review → publish) |
| `src/services/agents/mentor.py` | **Update** | Handle veto (re-draft) |
| `src/services/blackboard/proposal.py` | **Update** | Add `parent_proposal_id` for the draft phase |
| `tests/agents/test_reflection.py` | **Create** | Cover approve / modify / veto paths |
| `tests/e2e/test_veto_loop.py` | **Create** | Spoiler detection → re-draft → approve |

### Functions to write / update

#### `src/services/agents/reflection.py`

| Function | What it does |
|---|---|
| `async def review(self, message, *, problem_context) -> Verdict` | Calls LLM with the problem's expected solution hidden; checks for (a) spoiler phrases, (b) harsh tone, (c) safety issues |
| `def _is_spoiler(self, msg, expected_solution) -> bool` | Substring / embedding-similarity check (cheap) |
| `def _verdict_to_dict(self, v) -> dict` | Structured output: `{decision, reason, suggested_edit?}` |
| `Verdict` enum | `APPROVE` / `MODIFY` / `VETO` |

#### `src/services/blackboard/coordinator.py` (update)

| Function | What it does |
|---|---|
| `async def _commit_question(self, proposal)` | Two-phase: if `section == OPEN_QUESTIONS_FOR_USER` and `not proposal.parent_proposal_id`, hold in `pending_questions`; else publish |
| `async def on_reflection_verdict(self, proposal_id, verdict)` | If `VETO`, mark proposal rejected and re-emit a re-draft event to the mentor |

### Phase 2 done-when

- [ ] A hand-crafted spoiler mentor message is vetoed automatically
- [ ] Vetoed messages do **not** reach the user
- [ ] Mentor receives the veto and re-drafts once (with the `reason` attached)
- [ ] No message has > 1.5 s p95 latency from token grant to push

---

## Phase 3 — Planner in the loop (Week 4)

**Goal:** `Planner` reads `timeline` after session end and writes `learning_plan_draft`. The "Practice these" card surfaces on session close.

### Scripts to create / update

| File | Action | Purpose |
|---|---|---|
| `src/services/agents/planner.py` | **Create** | Reads timeline, generates practice set |
| `src/api/sessions.py` | **Update** | Trigger planner on close, return plan |
| `src/services/blackboard/coordinator.py` | **Update** | Lower-priority path (P4) for planner |
| `tests/agents/test_planner.py` | **Create** | Unit tests for plan generation |

### Functions to write

#### `src/services/agents/planner.py`

| Function | What it does |
|---|---|
| `class Planner` | Owns `LLMClient` |
| `async def build_plan(self, session_id) -> LearningPlan` | Reads timeline; identifies weakest patterns; picks 3–5 follow-up problems |
| `async def _identify_weak_patterns(self, timeline) -> list[str]` | Heuristic: aggregate hypothesis categories by frequency and recency |
| `async def _select_practice_problems(self, weak, user_profile) -> list[Problem]` | Calls the problem-bank MCP server |

#### `src/api/sessions.py` (update)

| Endpoint | What it does |
|---|---|
| `POST /sessions/{id}/close` | After marking session ended, enqueues a planner job; returns plan in payload once ready |

### Phase 3 done-when

- [ ] Closing a session returns a `learning_plan_draft` with 3+ problems
- [ ] The plan reflects what the user actually struggled with (verified manually for 3 sessions)

---

## Phase 4 — Replay + Observability (Week 5)

**Goal:** You can replay any past session through the agents and see whether the output matches what the user actually saw. You can see what's slow and what's failing.

### Scripts to create / update

| File | Action | Purpose |
|---|---|---|
| `src/services/replay/simulator.py` | **Create** | Replays timeline events through the agent stack |
| `src/services/replay/diff.py` | **Create** | Compares replay output to recorded output |
| `src/observability/metrics.py` | **Create** | All metrics from `WORKFLOW_ARCHITECTURE_C.md` §10 |
| `src/observability/tracing.py` | **Create** | OpenTelemetry setup |
| `src/api/health.py` | **Create** | `/health` and `/health/deep` |
| `src/main.py` | **Update** | Mount observability |
| `src/services/blackboard/coordinator.py` | **Update** | Emit metrics on every decision |
| `tests/replay/test_deterministic.py` | **Create** | Same timeline → same output |
| `requirements.txt` | **Update** | Add `opentelemetry-api`, `opentelemetry-sdk`, `prometheus-client` |

### Functions to write

#### `src/services/replay/simulator.py`

| Function | What it does |
|---|---|
| `class ReplaySimulator` | Reads `TimelineEvent` rows; reconstructs the blackboard step by step |
| `async def replay(self, session_id, *, model_override=None) -> ReplayResult` | Returns the sequence of mentor messages the original session produced |
| `async def _replay_event(self, event)` | Feeds each event back into the coordinator in order |

#### `src/services/replay/diff.py`

| Function | What it does |
|---|---|
| `def diff(actual: list[MentorMessage], expected: list[MentorMessage]) -> DiffReport` | Per-message: match / mismatch / extra / missing |

#### `src/observability/metrics.py`

| Function | What it does |
|---|---|
| `proposal_latency_ms = Histogram(...)` | Per `(from_agent, section)` |
| `proposal_accept_rate = Counter(...)` | Per `(from_agent, section)` |
| `mentor_token_wait_ms = Histogram(...)` | Per `priority` |
| `reflection_veto_rate = Counter(...)` | Per `reason` |
| `blackboard_section_versions = Gauge(...)` | Per `session_id` |
| `def emit(name, **labels)` | Helper used by the coordinator |

#### `src/api/health.py`

| Endpoint | What it does |
|---|---|
| `GET /health` | Liveness only — process up? |
| `GET /health/deep` | DB reachable? LLM provider reachable? Last commit < N s ago? |

### Phase 4 done-when

- [ ] Replaying any of 3 past sessions reproduces the same mentor messages
- [ ] `/metrics` (Prometheus) shows all 5 metric families
- [ ] One OpenTelemetry trace covers `proposal → commit → token → push`
- [ ] `/health/deep` correctly returns 503 if Postgres is down

---

## Phase 5 — Degraded modes (Week 6)

**Goal:** When the LLM provider fails, the user still gets a usable experience. When latency spikes, the system falls back to lighter paths.

### Scripts to create / update

| File | Action | Purpose |
|---|---|---|
| `src/services/llm/client.py` | **Update** | Add circuit breaker + retry budget |
| `src/services/blackboard/coordinator.py` | **Update** | Implement the graceful-degradation ladder |
| `src/services/agents/mentor.py` | **Update** | Add a rule-based fallback Mentor (no LLM) |
| `src/services/agents/analyzer.py` | **Update** | Add a heuristic-only analyzer path |
| `src/api/health.py` | **Update** | Surface current degradation tier in `/health/deep` |
| `tests/blackboard/test_degradation.py` | **Create** | Force LLM failures, verify fallbacks kick in |

### Functions to write / update

#### Degradation ladder (in `coordinator.py`)

| Tier | Trigger | Behavior |
|---|---|---|
| 0 — full | All healthy | Normal LLM-powered path |
| 1 — slower | LLM p95 > 2 s | Drop Reflection; allow longer P3 interval |
| 2 — analyzer only | Mentor LLM failing | Heuristic Mentor (rule-based hints) |
| 3 — read-only | All LLMs failing | Stop pushing proactive messages; keep chat echo |

#### `src/services/agents/mentor.py` (update)

| Function | What it does |
|---|---|
| `class HeuristicMentor` | Rule-based; no LLM |
| `def hint_for(self, code, failing_tests) -> str` | If no LLM: returns a static hint like "Try tracing through the failing test with a small input." |

#### `src/services/llm/client.py` (update)

| Function | What it does |
|---|---|
| `class CircuitBreaker` | Tracks consecutive failures; opens after N; half-opens after cool-down |
| `async def complete_with_breaker(self, ...) -> str` | Raises `LLMUnavailable` if breaker is open |
| `def current_tier(self) -> int` | Exposed to coordinator for the ladder decision |

### Phase 5 done-when

- [ ] Injecting 100% LLM failures → system falls to tier 3 within 30 s
- [ ] User still sees echoes, no crashes, no infinite retries
- [ ] When LLM recovers, system climbs back to tier 0 within 60 s
- [ ] `/health/deep` reports the current tier

---

## Cross-cutting tests (write as you go)

| Test file | Covers |
|---|---|
| `tests/blackboard/test_store.py` | Phase 0 |
| `tests/blackboard/test_coordinator.py` | Phase 0 |
| `tests/agents/test_analyzer.py` | Phase 1 |
| `tests/agents/test_reflection.py` | Phase 2 |
| `tests/agents/test_planner.py` | Phase 3 |
| `tests/e2e/test_proactive_help.py` | Phase 1 |
| `tests/e2e/test_veto_loop.py` | Phase 2 |
| `tests/replay/test_deterministic.py` | Phase 4 |
| `tests/blackboard/test_degradation.py` | Phase 5 |

All tests use a **deterministic LLM stub** (fixture in `tests/conftest.py`) so CI doesn't hit the real provider.

---

## File map at a glance

```
Your-Joyful-Coding-Platform-/
├── src/
│   ├── main.py                       (existing — updated each phase)
│   ├── api/
│   │   ├── auth.py                   (existing)
│   │   ├── sessions.py               (Phase 0)
│   │   ├── ws.py                     (Phase 1)
│   │   └── health.py                 (Phase 4)
│   ├── core/                         (existing)
│   ├── crud/                         (existing)
│   ├── db/
│   │   ├── database.py               (existing)
│   │   └── models.py                 (existing — extended Phase 0)
│   ├── schemas/                      (existing)
│   └── services/
│       ├── ai_agent.py               (legacy — to be deprecated)
│       ├── blackboard/
│       │   ├── sections.py           (Phase 0)
│       │   ├── store.py              (Phase 0)
│       │   ├── proposal.py           (Phase 0)
│       │   └── coordinator.py        (Phase 0, extended every phase)
│       ├── agents/
│       │   ├── mentor.py             (Phase 0)
│       │   ├── analyzer.py           (Phase 1)
│       │   ├── reflection.py         (Phase 1 stub → Phase 2 real)
│       │   └── planner.py            (Phase 3)
│       ├── llm/
│       │   └── client.py             (Phase 1, hardened Phase 5)
│       ├── idle.py                   (Phase 1)
│       ├── replay/
│       │   ├── simulator.py          (Phase 4)
│       │   └── diff.py               (Phase 4)
│       └── observability/
│           ├── metrics.py            (Phase 4)
│           └── tracing.py            (Phase 4)
├── tests/
│   ├── conftest.py                   (Phase 0 — LLM stub fixture)
│   ├── blackboard/
│   ├── agents/
│   ├── e2e/
│   └── replay/
├── WORKFLOW_ARCHITECTURE_C.md        (read first)
├── WORKFLOW_ARCHITECTURE_C_中文版.md
├── AGENT_ARCHITECTURE.md
├── BUILD_PLAN.md                     (this file)
└── README.md                         (project root readme)
```

---

## Definition of "done" for the whole project

- [ ] All five phases complete
- [ ] Replay reproduces 95% of historical mentor messages exactly
- [ ] p95 proactive-message latency ≤ 1.5 s
- [ ] Zero LLM-related crashes in 24-hour soak test
- [ ] `/health/deep` accurately reports current tier at all times
