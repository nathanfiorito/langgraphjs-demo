# LangGraph — Estudo de Orquestração de Agentes de IA

Repositório de estudo didático sobre **LangGraph**, cobrindo **TypeScript** e **Python**. Os exemplos usam **Claude** (Anthropic) como LLM.

## O que é LangGraph?

LangGraph é uma biblioteca que permite construir aplicações de IA como **grafos de estado**, onde:

- **Nodes (Nós)** são funções que processam e transformam dados
- **Edges (Arestas)** definem o fluxo entre os nós (podendo ser condicionais)
- **State (Estado)** é um objeto compartilhado que trafega por todo o grafo

## Estrutura do Repositório

```
langgraphjs-demo/
├── typescript-samples/   # 6 módulos progressivos em TypeScript
├── python-samples/       # 6 módulos equivalentes em Python
└── challenges/           # Desafios práticos com testes automatizados
    ├── typescript/
    └── python/
```

## Pré-requisitos

- **Node.js 18+** (para TypeScript)
- **Python 3.11+** (para Python)
- **Chave de API da Anthropic** (módulos 04–06 e challenges bônus)

## Configuração

```bash
# 1. Configure o .env na raiz do repositório
cp .env.example .env
# Edite o .env e adicione: ANTHROPIC_API_KEY=sk-ant-...
```

### TypeScript

```bash
cd typescript-samples
npm install
npm run 01:basic-graph        # Sem API key
npm run 02:state-management   # Sem API key
npm run 03:conditional-edges  # Sem API key
npm run 04:tool-calling       # Requer API key
npm run 05:multi-agent        # Requer API key
npm run 06:human-in-the-loop  # Requer API key (interativo)
```

### Python

```bash
cd python-samples
pip install -r requirements.txt
python src/m01_basic_graph.py        # Sem API key
python src/m02_state_management.py   # Sem API key
python src/m03_conditional_edges.py  # Sem API key
python src/m04_tool_calling.py       # Requer API key
python src/m05_multi_agent.py        # Requer API key
python src/m06_human_in_the_loop.py  # Requer API key (interativo)
```

---

## Módulos

| # | Conceito | LLM? | TypeScript | Python |
|---|----------|------|-----------|--------|
| 01 | Grafo básico — nodes, edges, state | Não | `src/01-basic-graph/` | `src/m01_basic_graph.py` |
| 02 | State management — reducers | Não | `src/02-state-management/` | `src/m02_state_management.py` |
| 03 | Conditional edges — roteamento | Não | `src/03-conditional-edges/` | `src/m03_conditional_edges.py` |
| 04 | Tool calling — padrão ReAct | Sim | `src/04-tool-calling/` | `src/m04_tool_calling.py` |
| 05 | Multi-agent — supervisor pattern | Sim | `src/05-multi-agent/` | `src/m05_multi_agent.py` |
| 06 | Human-in-the-loop — interrupt/resume | Sim | `src/06-human-in-the-loop/` | `src/m06_human_in_the_loop.py` |

### Diferenças entre TypeScript e Python

| Conceito | TypeScript | Python |
|----------|-----------|--------|
| Estado | `Annotation.Root({})` | `TypedDict` + `Annotated[tipo, reducer]` |
| Reducer de lista | `Annotation<T[]>({ reducer: (a,b) => [...a,...b] })` | `Annotated[list, operator.add]` |
| Reducer de dict | `Annotation<Record>({ reducer: (a,b) => ({...a,...b}) })` | `Annotated[dict, merge_dict]` |
| Nomes dos métodos | `addNode`, `addEdge`, `addConditionalEdges` | `add_node`, `add_edge`, `add_conditional_edges` |
| Ferramentas | `tool(fn, { schema: z.object({...}) })` | `@tool` decorator + type hints |
| LLM bind | `.bindTools(tools)` | `.bind_tools(tools)` |
| Saída estruturada | `.withStructuredOutput(zodSchema)` | `.with_structured_output(PydanticModel)` |
| Interrupt/resume | `interrupt()` / `new Command({ resume })` | `interrupt()` / `Command(resume=)` |
| Checkpointer | `MemorySaver` (compile arg) | `MemorySaver` (compile arg) |

---

## Challenges

Desafios práticos para consolidar o aprendizado. Cada desafio tem:
- Um **esqueleto** com `TODO`s para implementar
- **Testes automatizados** para validar a solução
- **Exercícios bônus** com LLM real (challenges 03 e 04)

```bash
# TypeScript
cd challenges/typescript
npm install
npm test              # Roda todos os testes

# Python
cd challenges/python
pip install -r requirements.txt
pytest                # Roda todos os testes
```

Veja [challenges/README.md](challenges/README.md) para detalhes de cada desafio.

---

## Diagrama de Complexidade

```
Módulo 01 ── Grafo puro (sem LLM)
    │
Módulo 02 ── + Estado avançado (reducers)
    │
Módulo 03 ── + Roteamento condicional
    │
Módulo 04 ── + LLM + Ferramentas (ReAct)
    │
Módulo 05 ── + Múltiplos agentes (Supervisor)
    │
Módulo 06 ── + Revisão humana (interrupt/resume)
```

## Recursos

- [Documentação LangGraph.js](https://langchain-ai.github.io/langgraphjs/)
- [Documentação LangGraph Python](https://langchain-ai.github.io/langgraph/)
- [Anthropic Console](https://console.anthropic.com/)
