# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

An educational LangGraph repository with 6 progressive learning modules and 4 practical challenges, implemented in both TypeScript and Python. The content is in Portuguese.

## Commands

### TypeScript Samples

```bash
cd typescript-samples
npm install
npm run 01:basic-graph
npm run 02:state-management
npm run 03:conditional-edges
npm run 04:tool-calling        # requires ANTHROPIC_API_KEY
npm run 05:multi-agent         # requires ANTHROPIC_API_KEY
npm run 06:human-in-the-loop   # requires ANTHROPIC_API_KEY
```

### TypeScript Challenges

```bash
cd challenges/typescript
npm install
npm test                  # run all challenge tests
npm run test:watch        # watch mode
npx vitest run challenge-01  # run a single challenge test
```

### Python Samples

```bash
cd python-samples
pip install -r requirements.txt
python src/m01_basic_graph.py
# ... through m06_human_in_the_loop.py
```

### Python Challenges

```bash
cd challenges/python
pip install -r requirements.txt
pytest                          # run all tests
pytest tests/test_challenge_01.py  # run single challenge test
```

### Environment Setup

Copy `.env.example` to `.env` in the repo root and set `ANTHROPIC_API_KEY`.

## Architecture

### Module Progression

Modules 01–03 require no API key (pure graph logic). Modules 04–06 require `ANTHROPIC_API_KEY` and demonstrate LLM integration.

| Module | Topic | Key Pattern |
|--------|-------|-------------|
| 01 | Basic Graph | nodes, edges, `invoke()` |
| 02 | State Management | custom reducers, dict/list merge |
| 03 | Conditional Edges | `addConditionalEdges()` / `add_conditional_edges()` |
| 04 | Tool Calling | ReAct loop, Zod/Pydantic tool schemas |
| 05 | Multi-Agent | Supervisor pattern, `withStructuredOutput()` |
| 06 | Human-in-the-Loop | `interrupt()`, `MemorySaver`, `Command({ resume })` |

### State Definition

**TypeScript:**
```typescript
const MyState = Annotation.Root({
  items: Annotation<string[]>({ reducer: (a, b) => [...a, ...b], default: () => [] }),
  meta: Annotation<Record<string, unknown>>({ reducer: (a, b) => ({ ...a, ...b }), default: () => ({}) }),
});
```

**Python:**
```python
class MyState(TypedDict):
    items: Annotated[list[str], operator.add]
    meta: Annotated[dict, lambda a, b: {**a, **b}]
```

### Challenges Structure

Each challenge is a skeleton file with TODO markers. The automated tests drive implementation — fill in the nodes and graph wiring until `npm test` / `pytest` passes.

```
challenges/
  typescript/
    challenges/challenge-01.ts  ← implement here
    tests/challenge-01.test.ts  ← validates your implementation
  python/
    challenges/challenge_01.py  ← implement here
    tests/test_challenge_01.py  ← validates your implementation
```

### TypeScript vs Python API Differences

| Concept | TypeScript | Python |
|---------|-----------|--------|
| State | `Annotation.Root()` | `TypedDict` + `Annotated` |
| Add node | `graph.addNode("name", fn)` | `graph.add_node("name", fn)` |
| Conditional edges | `graph.addConditionalEdges()` | `graph.add_conditional_edges()` |
| Tool decorator | `tool()` from `@langchain/core/tools` + Zod | `@tool` decorator + Pydantic |
| Compile | `graph.compile()` | `graph.compile()` |
| Invoke | `await graph.invoke(state)` | `await graph.ainvoke(state)` (async) |
