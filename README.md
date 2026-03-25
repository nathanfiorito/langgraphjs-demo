# LangGraph.js — Estudo de Orquestração de Agentes de IA

Repositório de estudo didático sobre **LangGraph.js**, a principal biblioteca para criação de agentes de IA baseados em grafos de estado. Os exemplos usam **Claude** (Anthropic) como LLM.

## O que é LangGraph?

LangGraph é uma biblioteca que permite construir aplicações de IA como **grafos de estado**, onde:

- **Nodes (Nós)** são funções que processam e transformam dados
- **Edges (Arestas)** definem o fluxo entre os nós (podendo ser condicionais)
- **State (Estado)** é um objeto compartilhado que trafega por todo o grafo

Isso permite criar desde pipelines simples até sistemas multi-agente complexos com suporte a ferramentas, roteamento dinâmico e revisão humana.

```
         ┌─────────────────────────────────────────┐
         │              LANGGRAPH                  │
         │                                         │
         │   START → [nó A] → [nó B] → [nó C] → END │
         │                  ↑     │               │
         │                  └─────┘ (loop)        │
         └─────────────────────────────────────────┘
```

## Estrutura do Repositório

```
src/
├── 01-basic-graph/          # Conceito fundamental: nodes, edges e state
├── 02-state-management/     # Reducers, defaults e tipos complexos de estado
├── 03-conditional-edges/    # Roteamento dinâmico baseado no estado
├── 04-tool-calling/         # Agente com ferramentas (padrão ReAct)
├── 05-multi-agent/          # Múltiplos agentes com supervisor
└── 06-human-in-the-loop/    # Interrupção e revisão humana
```

## Pré-requisitos

- Node.js 18+
- Chave de API da Anthropic ([obter aqui](https://console.anthropic.com/))

## Configuração

```bash
# 1. Instalar dependências
npm install

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env e adicione sua ANTHROPIC_API_KEY
```

## Como Executar

Cada módulo é independente e pode ser executado separadamente:

```bash
npm run 01:basic-graph        # Não requer API key
npm run 02:state-management   # Não requer API key
npm run 03:conditional-edges  # Não requer API key
npm run 04:tool-calling       # Requer ANTHROPIC_API_KEY
npm run 05:multi-agent        # Requer ANTHROPIC_API_KEY
npm run 06:human-in-the-loop  # Requer ANTHROPIC_API_KEY (interativo)
```

---

## Módulos

### 01 — Grafo Básico

**Conceitos:** `StateGraph`, `Annotation`, `addNode`, `addEdge`, `START`, `END`

O módulo mais fundamental. Mostra como construir um grafo sem LLM, focando na estrutura:

```typescript
const grafo = new StateGraph(MeuState)
  .addNode("passo1", funcaoPasso1)
  .addNode("passo2", funcaoPasso2)
  .addEdge(START, "passo1")
  .addEdge("passo1", "passo2")
  .addEdge("passo2", END)
  .compile();

const resultado = await grafo.invoke({ textoOriginal: "hello world" });
```

---

### 02 — Gerenciamento de Estado

**Conceitos:** Reducers customizados, acumulação de arrays, merge de objetos, valores default

O estado é o coração do LangGraph. Este módulo mostra como controlá-lo com precisão:

```typescript
const Estado = Annotation.Root({
  // Último valor vence (padrão)
  status: Annotation<string>,

  // Array acumulativo — cada nó adiciona itens sem sobrescrever
  logs: Annotation<string[]>({
    reducer: (atual, novas) => [...(atual ?? []), ...novas],
    default: () => [],
  }),

  // Objeto com merge — permite atualizações parciais
  resumo: Annotation<Record<string, unknown>>({
    reducer: (atual, novo) => ({ ...(atual ?? {}), ...novo }),
    default: () => ({}),
  }),
});
```

---

### 03 — Conditional Edges

**Conceitos:** `addConditionalEdges`, funções de roteamento, grafos ramificados

O roteamento dinâmico é o que transforma pipelines lineares em grafos inteligentes:

```typescript
function rotear(estado: Estado): "caminhoA" | "caminhoB" | "caminhoC" {
  if (estado.urgente) return "caminhoA";
  if (estado.tecnico) return "caminhoB";
  return "caminhoC";
}

grafo.addConditionalEdges("triagem", rotear, {
  caminhoA: "tratarUrgente",
  caminhoB: "tratarTecnico",
  caminhoC: "tratarGeral",
});
```

---

### 04 — Tool Calling (Padrão ReAct)

**Conceitos:** `tool()`, `ToolNode`, `bindTools`, loop Reasoning→Acting

O padrão ReAct permite que o LLM use ferramentas para resolver problemas:

```
                    ┌─────────────────────────────┐
                    │        Padrão ReAct          │
                    │                              │
  Pergunta ──→ [agente] ──→ chama ferramenta       │
                  ↑    ←── resultado da ferramenta │
                  └─── raciocina sobre resultado   │
                  └─── (repete até ter resposta)   │
                  └──→ resposta final              │
                    └─────────────────────────────┘
```

---

### 05 — Multi-Agent

**Conceitos:** Padrão Supervisor, agentes especializados, estado compartilhado

O padrão de orquestração mais poderoso: um supervisor delega tarefas para agentes especializados:

```
  Tarefa → [Supervisor] → [Analista] → [Supervisor] → [Redator] → [Supervisor] → FIM
                              ↑               ↑              ↑
                         especialista    avalia resultado  especialista
                         em dados        do analista       em texto
```

---

### 06 — Human-in-the-Loop

**Conceitos:** `interrupt()`, `Command({ resume })`, `MemorySaver`, `thread_id`

Permite pausar o grafo e aguardar input humano antes de continuar:

```typescript
// No nó — pausa o grafo
const decisaoHumana = interrupt("Deseja aprovar? (sim/não)");

// Para retomar — em outro invoke()
await grafo.invoke(
  new Command({ resume: "sim" }),
  { configurable: { thread_id: "minha-sessao" } }
);
```

---

## Diagrama Geral de Complexidade

```
Módulo 01 ──── Grafo puro (sem LLM)
    │
Módulo 02 ──── + Estado avançado
    │
Módulo 03 ──── + Roteamento condicional
    │
Módulo 04 ──── + LLM + Ferramentas
    │
Módulo 05 ──── + Múltiplos agentes
    │
Módulo 06 ──── + Revisão humana
```

## Dependências Principais

| Pacote | Função |
|---|---|
| `@langchain/langgraph` | Framework de grafos de estado |
| `@langchain/anthropic` | Integração com Claude (Anthropic) |
| `@langchain/core` | Tipos base (Messages, Tools, etc.) |
| `zod` | Schema validation para ferramentas |
| `dotenv` | Variáveis de ambiente |

## Recursos

- [Documentação oficial do LangGraph.js](https://langchain-ai.github.io/langgraphjs/)
- [LangGraph Academy](https://academy.langchain.com/)
- [Anthropic Console](https://console.anthropic.com/)
