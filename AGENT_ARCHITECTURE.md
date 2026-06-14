# Multi-Agent Architecture for the Joyful Coding Platform

> Companion design document to the FastAPI backend in `src/`. This file proposes **three** end-to-end multi-agent architectures that orchestrate a `Mentor`, an `Analyzer`, and a `Teacher` agent (plus a few optional helpers) around the coding-problem experience. Each architecture is described with: agent responsibilities, memory layout, MCP tool usage, communication protocol, a sequence/flow diagram, and an honest pros/cons list. A recommendation closes the document.

---

## 0. Shared Foundations (used by all three architectures)

Before comparing architectures, these are the building blocks every option reuses.

### 0.1 Core Agents

| Agent | User-visible? | Primary Job | Inputs | Outputs |
|---|---|---|---|---|
| **Mentor** | Yes — chat panel beside the editor | Encourage, query the user when they are stuck, answer questions grounded in the current problem and their partial code | Current problem statement, live code buffer, chat history, "stuck signal" from Analyzer | Natural-language reply, optional hint cards, optional "ask me a clarifying question" prompt |
| **Analyzer** | No — background | Observe user behavior (typing cadence, dead-ends, repeated edits, repeated failed tests, frustration markers) and produce a structured `StuckReport` | Editor event stream, keystroke/telemetry stream, submission results, chat history | `StuckReport { stuckness_score, probable_bottleneck, code_signals, last_events[] }` |
| **Teacher** | Mostly no — surfaces periodic "Practice these" cards | Diagnose weak topics/concepts from long-term performance and prescribe next problems | Aggregated `StuckReport`s, submission history, problem tags, prior lesson memory | `LearningPlan { weak_topics[], next_problems[], concept_review[] }` |

Optional helpers introduced by some architectures:
- **Orchestrator / Router** — decides which agent acts next.
- **Reflection / Critic** — reviews Mentor output before showing it to the user.
- **Knowledge Curator** — maintains a vector index of problem statements, editorial, and prior mentor conversations.

### 0.2 Memory Tiers (shared vocabulary)

All three architectures partition memory into the same four tiers; they differ in **who writes/reads** them.

| Tier | Lifetime | Stored in | What lives here |
|---|---|---|---|
| **L1 — Working Memory** | Single chat turn / one editor session | In-process context of the agent invocation | Current problem, current code, last 10 events, scratchpad |
| **L2 — Session Memory** | One problem attempt (15–60 min) | Redis / Postgres `sessions` table | Full keystroke/edit timeline, full chat history, all `StuckReport`s for this attempt |
| **L3 — User Profile Memory** | Weeks–months | Postgres `user_learning_profile` + vector store | Per-topic mastery, common mistake patterns, preferred hint style, pace |
| **L4 — Platform / Curriculum Memory** | Permanent | Postgres + vector store | Problem bank metadata, editorial content, canonical solutions, concept graph |

### 0.3 MCP (Model Context Protocol) Servers

All agents interact with the world through MCP tool servers — this keeps the LLM prompts clean and makes each tool auditable.

| MCP Server | Tools exposed | Used by |
|---|---|---|
| `problems-mcp` | `get_problem(id)`, `get_examples(id)`, `get_constraints(id)`, `get_editorial(id)`, `list_similar_problems(id, k)` | Mentor, Teacher |
| `execution-mcp` | `run_against_tests(code, problem_id)`, `get_test_results(run_id)`, `explain_runtime_error(stderr)` | Analyzer (passively), Mentor (when explaining) |
| `user-mcp` | `get_user_profile(user_id)`, `update_mastery(user_id, topic, delta)`, `get_recent_stuck_reports(user_id, n)` | Analyzer, Teacher |
| `editor-mcp` *(custom)* | `get_current_code()`, `get_diff_since(t)`, `get_cursor_history()`, `subscribe_events()` | Analyzer (subscriber), Mentor (on demand) |
| `curriculum-mcp` | `recommend_problems(weak_topics)`, `lookup_concept_graph(topic)`, `fetch_lesson_card(concept)` | Teacher |
| `memory-mcp` | `session.append_event(...)`, `session.read(...)`, `profile.read/write(...)` | All agents |

> **Why MCP here?** It cleanly separates the agent's "brain" (the LLM) from the platform's "hands" (running code, fetching problems, reading telemetry). The same agent code can be unit-tested with mock MCP servers and run in production against the real ones.

### 0.4 Communication Protocol Primitives

Regardless of architecture, every inter-agent message is a typed envelope:

```json
{
  "trace_id": "uuid",
  "from": "analyzer",
  "to": "mentor",
  "intent": "STUCK_DETECTED",
  "payload": { "score": 0.82, "bottleneck": "off-by-one in two-pointer loop" },
  "memory_refs": ["session:abc#stuck_report_3", "profile:user_42#two_pointer_mastery"],
  "ts": "2026-06-14T15:30:00Z"
}
```

Standardized `intent` values: `STUCK_DETECTED`, `USER_ASKED`, `SUBMIT_RESULT`, `REQUEST_HINT`, `REQUEST_PLAN`, `NEW_PROBLEM_LOADED`, `SESSION_ENDED`, `BROADCAST_INSIGHT`.

---

## 1. Architecture A — Hub-and-Spoke (Mentor as Orchestrator)

> **Mental model:** The `Mentor` is the only agent that talks to the user. The `Analyzer` and `Teacher` are "back-room" specialists it calls on demand, like a senior dev who pulls in an SRE and a learning designer as needed.

### 1.1 Diagram

```
                       ┌────────────────────────────────────┐
                       │            USER (browser)          │
                       │  [ Editor ]            [ Chat ]    │
                       └──────────────┬──────────────┬──────┘
                                      │ events       │ messages
                                      ▼              ▲
                            ┌──────────────────────────┐
                            │  FastAPI WebSocket / SSE │
                            └──────────────┬───────────┘
                                           │
                                           ▼
                       ╔════════════════════════════════════╗
                       ║           MENTOR (Hub)             ║
                       ║  • owns the conversation           ║
                       ║  • decides when to call helpers    ║
                       ║  • formats final reply to user     ║
                       ╚════╤══════════════════╤════════════╝
                            │ invokes          │ invokes
                ┌───────────┘                  └────────────┐
                ▼                                          ▼
        ┌──────────────┐                            ┌──────────────┐
        │   ANALYZER   │                            │   TEACHER    │
        │ (specialist) │                            │ (specialist) │
        └──────┬───────┘                            └──────┬───────┘
               │ reads/writes                              │ reads/writes
               ▼                                           ▼
        ┌──────────────────────────────────────────────────────────┐
        │            MCP Tool Layer (problems/execution/user/     │
        │            editor/curriculum/memory)                     │
        └──────────────────────────────────────────────────────────┘
```

### 1.2 Communication Protocol — Synchronous Tool-Calls

The Mentor runs a ReAct-style loop and treats Analyzer/Teacher as **function tools**:

1. The Mentor is the only LLM in the hot path.
2. It receives user input + L2 session memory as context.
3. Its tool list includes `ask_analyzer(...)`, `ask_teacher(...)`, plus the standard MCP tools.
4. The Analyzer and Teacher are *stateless per call* — they get a payload, return a structured result, and forget.

Example Mentor turn:

```text
[System] You are the Mentor. You may call ask_analyzer or ask_teacher if needed.
[User] "I'm stuck on this for 20 minutes."
[Tools available] ask_analyzer, ask_teacher, run_against_tests, get_problem, …

[Assistant reasoning]
  - User is asking for help; I should understand *why* they're stuck.
  → call ask_analyzer(session_id="abc")
  → result: {stuckness: 0.9, bottleneck: "edge cases in recursion base case"}
  - I should ground my hint in the problem.
  → call get_problem(id=42)
  - I'll also pull the user's mastery on recursion to calibrate difficulty.
  → call ask_teacher(topic="recursion")
[Assistant → User] "It looks like you've been wrestling with the base
  case — what happens when the input is empty?"
```

### 1.3 Memory Access Pattern

| Tier | Read by | Write by |
|---|---|---|
| L1 (working) | Mentor | Mentor |
| L2 (session) | Mentor, Analyzer, Teacher | Analyzer (events), Mentor (chat), Teacher (plan snapshots) |
| L3 (profile) | Mentor (to calibrate tone/difficulty), Teacher | Teacher (mastery deltas) |
| L4 (curriculum) | Mentor, Teacher | Curators / admins |

### 1.4 Why this fits the existing FastAPI skeleton

- `src/services/ai_agent.py` becomes the **Mentor** module.
- Two thin sibling modules — `analyzer.py` and `teacher.py` — implement the specialist functions.
- All three share one `memory/` adapter that talks to the `memory-mcp` server.
- WebSocket route in FastAPI owns the session lifecycle and pushes Mentor replies to the browser.

### 1.5 Pros

- **Lowest implementation cost.** One main agent, two helper functions; no inter-agent negotiation, no shared state machine.
- **Predictable UX.** Every word the user sees passes through one model, so tone, persona, and safety filtering are centralized.
- **Easy to debug.** You can replay a session by re-running the Mentor's tool-call trace.
- **Cheapest latency in the common case.** Simple Q&A never touches the Analyzer/Teacher.
- **Natural place for a guardrail layer** (a single point to filter Mentor output before it reaches the user).

### 1.6 Cons

- **Single point of failure (the Mentor).** If the Mentor hallucinates a `StuckReport` summary or misroutes a question, the user sees it directly.
- **Mentor context window pressure.** It has to carry enough L2 memory to call helpers intelligently, which can balloon prompts.
- **Analyzer/Teacher can feel "dumb".** Because they have no persistent agency, they can't proactively nudge the Mentor — they only answer when asked.
- **Hard to evolve roles independently.** Adding a new specialist (e.g., a `CodeReviewer` agent) means retraining the Mentor's tool-selection prompt.
- **No peer learning.** Analyzer never knows what Teacher recommended, so insights are siloed per call.

---

## 2. Architecture B — Event-Driven Pipeline (Analyzer as the Spine)

> **Mental model:** A central **event bus** is the source of truth. The `Analyzer` listens to the bus, the `Teacher` listens to the Analyzer, and the `Mentor` listens to *both*. Agents are autonomous, stateless-per-event, and react to messages rather than to direct RPC calls. This is the most "distributed" of the three.

### 2.1 Diagram

```
  ┌──────────────┐    publishes     ┌──────────────────┐
  │  Editor /    │ ───────────────▶ │                  │
  │  Test runner │                  │   EVENT BUS      │
  └──────────────┘                  │ (Redis Streams / │
                                    │  Kafka / NATS)   │
                                    │                  │
                                    │  Topics:         │
                                    │  • code.events   │
                                    │  • test.results  │
                                    │  • chat.message  │
                                    │  • stuck.alerts  │
                                    │  • lesson.plans  │
                                    └────┬──────┬──────┘
                       subscribes       │      │      subscribes
                                         ▼      ▼
                                  ┌──────────┐ ┌──────────┐
                                  │ ANALYZER │ │ TEACHER  │
                                  │ (worker) │ │ (worker) │
                                  └────┬─────┘ └────┬─────┘
                                       │ publishes   │ publishes
                                       ▼             ▼
                                  topics: stuck.alerts, code.signals
                                                     │
                                  ┌──────────────────┘
                                  ▼
                          ┌──────────────────┐
                          │  MENTOR          │  subscribes to:
                          │  (chat agent)    │   • stuck.alerts
                          │  • user-facing   │   • lesson.plans
                          │  • proactive     │   • chat.message
                          └────┬─────────────┘
                               │ WebSocket
                               ▼
                          ┌──────────────┐
                          │    USER      │
                          └──────────────┘
```

### 2.2 Communication Protocol — Async Pub/Sub

There are **no direct agent-to-agent calls.** Agents emit and consume typed events on named topics.

Topic catalog:

| Topic | Producer | Consumers | Payload |
|---|---|---|---|
| `code.events` | Editor MCP / front-end | Analyzer | `{event_type: "keystroke"|"paste"|"delete", ts, range}` |
| `test.results` | Execution MCP | Analyzer, Mentor | `{run_id, passed, failed_tests[], runtime_ms}` |
| `chat.message` | Front-end (user) and Mentor (assistant) | Analyzer, Teacher (L2) | `{role, text, ts}` |
| `stuck.alerts` | Analyzer | Mentor, Teacher | `StuckReport` envelope |
| `code.signals` | Analyzer | Teacher, Mentor | `{smell: "redundant_loop", "missing_base_case", ...}` |
| `lesson.plans` | Teacher | Mentor, Front-end "Practice" UI | `LearningPlan` envelope |
| `session.lifecycle` | Backend | All | `STARTED`, `ENDED` |

Mentor's proactive behavior example:

```text
# Backend emits:
test.results  → {passed: false, failed: ["case 7/10: empty input"]}
# Analyzer (running on a worker) detects:
  - 3 failed test runs in a row
  - last 4 minutes of edits all near the same line
  → publishes stuck.alerts  {score: 0.88, bottleneck: "empty-input handling"}

# Mentor (subscriber) decides proactively:
  - score > 0.8 for > 30 s
  - user hasn't typed in 90 s
  → emits chat.message  "Want a nudge? Think about what your function
     should return when the input is empty."
```

### 2.3 Memory Access Pattern

- The **event bus itself acts as L2 (session) memory** for the live timeline — every event is append-only and replayable.
- Each agent keeps a **projection** of L2 it cares about (e.g., Analyzer maintains a rolling window of edit deltas; Teacher maintains a daily aggregation).
- L3 / L4 still live in Postgres + vector store, accessed via MCP.

### 2.4 Why this fits the existing FastAPI skeleton

- The FastAPI app becomes a thin publisher: it pushes editor/test events to the bus and serves a WebSocket to the user.
- Analyzer and Teacher become **worker processes** (`celery`, `arq`, or plain `asyncio` consumers) — easy to scale horizontally.
- The Mentor becomes a single process that subscribes to `stuck.alerts` and `lesson.plans` *and* receives the user's chat WebSocket.
- All three workers are stateless and idempotent — replay-safe.

### 2.5 Pros

- **Decoupled and independently scalable.** Analyzer can run 10 workers; Teacher 2; Mentor 4. No agent blocks another.
- **Naturally asynchronous → low perceived latency.** The user keeps typing while the Analyzer chews on telemetry.
- **Replayable sessions.** The event log is the ground truth; you can re-run the Analyzer with a new model to compare signals.
- **Easy to add specialists.** A new `CodeReviewer` agent just subscribes to `test.results` and `code.events` — no Mentor prompt surgery.
- **Surfaces non-obvious insights** because agents see events they weren't explicitly told about (e.g., Teacher sees the same edit loop the Analyzer flagged).

### 2.6 Cons

- **Operational complexity.** You now run a broker, multiple workers, and a WebSocket tier. More things to monitor, retry, and backpressure.
- **Eventual consistency is uncomfortable for UX.** The user may type the answer *while* the Analyzer is still publishing a `stuck.alerts` — you need suppression logic ("if user just submitted successfully, drop pending alert").
- **Harder to enforce persona consistency.** Three LLMs may produce three different tones; the user-facing Mentor has to harmonize.
- **Schema governance burden.** Every event is a contract; adding a field to `StuckReport` is a multi-agent migration.
- **Debugging spans processes.** Tracing one user question across bus + 3 workers needs distributed tracing (OpenTelemetry).

---

## 3. Architecture C — Blackboard + Lightweight Coordinator

> **Mental model:** A **shared blackboard** (a structured, queryable document per session) holds the current best understanding of the user's state. All three agents read and write to it; a small **Coordinator** decides *whose turn* it is next and arbitrates conflicts. This is the most "AI-research-flavored" of the three.

### 3.1 Diagram

```
                        ┌──────────────────────────────────┐
                        │      BLACKBOARD (per session)    │
                        │  ┌────────────────────────────┐ │
                        │  │  • problem_context         │ │
                        │  │  • code_snapshot           │ │
                        │  │  • timeline[]              │ │
                        │  │  • stuck_hypotheses[]      │ │
                        │  │  • learning_plan_draft     │ │
                        │  │  • open_questions_for_user │ │
                        │  └────────────────────────────┘ │
                        └──────────┬───────────┬──────────┘
              reads / writes       │           │  reads / writes
              ┌────────────────────┤           ├────────────────────┐
              ▼                    ▼           ▼                    ▼
      ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
      │   MENTOR     │    │   COORDINATOR    │    │    TEACHER       │
      │  (writer +   │◀──▶│  • turn-taking   │◀──▶│  (writer +       │
      │   reader)    │    │  • conflict      │    │   reader)        │
      └──────┬───────┘    │    resolution    │    └────────┬─────────┘
             │            │  • throttle      │             │
             │            └─────────┬────────┘             │
             ▼                      │                      ▼
   ┌──────────────────┐             │            ┌──────────────────┐
   │   ANALYZER       │─────────────┘            │  REFLECTION /    │
   │  (writer +       │   (coordinator decides   │  CRITIC          │
   │   reader)        │    which agent may       │  (read-only then │
   └──────────────────┘    edit which section)   │   veto/suggest)  │
                                                └──────────────────┘
```

The blackboard is divided into **named sections** with a write-lock policy:

| Blackboard Section | Writers | Readers |
|---|---|---|
| `problem_context` | Backend on session start | All |
| `code_snapshot` | Editor MCP (push) | All |
| `timeline[]` | All (append-only) | All |
| `stuck_hypotheses[]` | Analyzer | Mentor, Coordinator |
| `learning_plan_draft` | Teacher | Coordinator, Mentor |
| `open_questions_for_user` | Mentor (writes), Reflection (vetoes) | Front-end |

### 3.2 Communication Protocol — Blackboard + Tokens

1. Any agent may **read** any section at any time.
2. To **write**, an agent sends a *proposal* to the Coordinator: `{section, change, rationale, confidence}`.
3. Coordinator applies a policy (e.g., last-writer-wins for `code_snapshot`, priority-based for `stuck_hypotheses`, reflection-veto for `open_questions_for_user`).
4. Coordinator broadcasts `{section, version}` so all agents can update their L1 working memory.
5. Mentor may only **emit to the user** when the Coordinator grants it a *speaking token* (prevents three agents from pinging the chat at once).

Example flow — user has been idle 2 minutes:

```text
1. Analyzer proposes to blackboard.stuck_hypotheses:
     {claim: "stuck on base case", confidence: 0.78, evidence: [...]}
2. Coordinator accepts → version bumps to v3.
3. Coordinator schedules Mentor turn (highest priority) and grants speaking token.
4. Mentor reads stuck_hypotheses v3 + learning_plan_draft, drafts a hint.
5. Reflection reviews the hint for safety / non-spoiler rule, approves.
6. Coordinator pushes to user via WebSocket.
```

### 3.3 Memory Access Pattern

- The **blackboard IS L2 memory** (richer than a flat event log — it's structured, queryable, and conflict-resolved).
- L3 / L4 remain the same Postgres + vector store.
- Each agent's L1 working memory is a *subscription view* of blackboard sections, kept in sync via Coordinator broadcasts.

### 3.4 Why this fits the existing FastAPI skeleton

- `src/services/blackboard/` module owns the section store (can be Postgres JSONB for v1, Redis for low-latency reads).
- `src/services/coordinator.py` is a small state machine — no LLM needed for most of its logic, which keeps it cheap and deterministic.
- Each agent is an async task that loops: *read blackboard → think → propose → wait for token* — very testable.

### 3.5 Pros

- **Rich shared state.** Every agent sees the same structured picture; insights from one agent immediately become context for another.
- **Conflict resolution is explicit.** No "last writer wins silently" bugs; the Coordinator is the place to encode policy.
- **Natural place for a Reflection / Critic agent** that doesn't write to the blackboard but can veto Mentor output (great for safety / non-spoiler rules).
- **Explainable.** You can show the user *why* the Mentor said something: "The Mentor suggested X because the Analyzer's hypothesis v3 (confidence 0.78) pointed to Y and the Teacher's plan v1 had not yet covered Z."
- **Agents stay simple.** Each one only knows its own proposals; coordination complexity lives in one place.

### 3.6 Cons

- **Coordinator is a new component to get right.** A buggy turn-scheduler creates chat storms or dead silences.
- **Locking and versioning can become a research project** if you over-design (CRDTs, vector clocks, etc.). Start with section-level last-writer-wins and only add complexity when measured.
- **Higher upfront design cost.** Defining sections, policies, and token rules is real work before the first user sees value.
- **Latency budget is tightest here.** Blackboard round-trip + Coordinator + Reflection + Mentor + push can exceed the user's "feels instant" window (~1.5 s) if not cached.
- **Harder to scale horizontally** because the blackboard is per-session and hot; you can shard by session_id but lose cross-session analytics unless you mirror to L3.

---

## 4. Side-by-Side Comparison

| Dimension | A. Hub-and-Spoke | B. Event-Driven Pipeline | C. Blackboard + Coordinator |
|---|---|---|---|
| Number of moving parts in v1 | 1 agent + 2 functions | 1 agent + 2 workers + broker | 3 agents + 1 coordinator + 1 (optional) critic |
| Time-to-first-helpful-message | Lowest | Low | Medium (turn-taking overhead) |
| Latency under load | Good (one LLM) | Best (async, scalable) | Medium (multi-step) |
| Replayability of a session | Replay Mentor's tool trace | Replay event log | Replay blackboard versions |
| Adding a 4th agent | Mentor prompt surgery | Subscribe to a topic | Read/write a new section |
| Explainability to user | Medium (Mentor's reasoning) | Low (events are opaque) | Highest (traceable to blackboard versions) |
| Safety / non-spoiler enforcement | Single chokepoint | Distributed (harder) | Single chokepoint (Reflection) |
| Operational complexity | Low | High | Medium-High |
| Best when | Small team, MVP, <10k MAU | Large scale, telemetry-rich | Research product, regulated UX |
| Risk if one agent misbehaves | User sees it (Mentor) | Localized to topic | Blocked by Coordinator/Reflection |

---

## 5. Recommendation

**Start with Architecture A (Hub-and-Spoke) for v1, and design the data model so you can graduate to Architecture B without a rewrite.**

Concrete path:

1. **v1 (weeks 1–4):** Implement Mentor in `src/services/ai_agent.py`, with `ask_analyzer()` and `ask_teacher()` as in-process Python functions. Use the `memory-mcp` for L2 and L3. Get user feedback on tone, hint quality, and "stuck detection" accuracy.
2. **v2 (weeks 5–8):** Introduce the event bus. Move the `code.events` and `test.results` streams to Redis Streams; the Analyzer becomes a worker that *also* pushes `stuck.alerts`. The Mentor subscribes to `stuck.alerts` but is still the only user-facing surface. This is Architecture B with a vestigial Hub — the cheapest possible migration.
3. **v3 (months 3+):** Add a Reflection/Critic in front of Mentor output and, if you ever need three agents to write coordinated state, lift session state into a blackboard (Architecture C) — the event log from v2 becomes your replay source of truth, so the migration is data-only, not behavioral.

The reason to bias toward A first is that your existing FastAPI skeleton (`src/main.py`, the planned `src/api/submissions.py`, the empty `src/services/ai_agent.py`) is naturally a single-process, request/response shape. Hub-and-Spoke maximizes the value of what you've already built, while the data-layer choices (typed envelopes, MCP, four memory tiers) are forward-compatible with B and C.

---

## 6. Concrete Next Steps

If you want, the next deliverables I can produce against whichever architecture you pick:

- A `pyproject.toml` / `requirements.txt` diff adding `fastapi`, `uvicorn`, `redis` (or `aiokafka`), `pydantic`, an MCP client SDK, and your LLM provider.
- Skeleton modules under `src/services/`:
  - `ai_agent.py` (Mentor), `analyzer.py`, `teacher.py`
  - `blackboard.py` (if Architecture C)
  - `event_bus.py` (if Architecture B)
  - `mcp_clients/` directory with one client per MCP server
- A `docker-compose.yml` with Postgres, Redis, and a stub MCP server.
- A `tests/` folder with replayable session fixtures.

Just tell me which architecture (A, B, or C) you'd like to build first, and I'll start with the directory layout and a runnable Mentor scaffold.
