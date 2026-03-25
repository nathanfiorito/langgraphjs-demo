/**
 * MÓDULO 05 — MULTI-AGENT (ORQUESTRAÇÃO DE MÚLTIPLOS AGENTES)
 * =============================================================
 *
 * O padrão mais poderoso do LangGraph: múltiplos agentes especializados
 * trabalhando juntos sob a coordenação de um supervisor.
 *
 * Padrão Supervisor:
 *   - O SUPERVISOR avalia a tarefa e delega para o especialista certo
 *   - Cada ESPECIALISTA tem ferramentas e prompts específicos
 *   - O supervisor avalia o resultado e decide se está pronto ou precisa
 *     de mais trabalho
 *
 * Agentes neste exemplo:
 *   - 🎯 Supervisor: orquestra e avalia qualidade
 *   - 📊 AgenteAnalista: analisa dados e calcula métricas
 *   - ✍️  AgenteRedator: escreve e formata relatórios
 *
 * Fluxo:
 *
 *   START → [supervisor] ──→ "analista" ──→ [analista] ──┐
 *                │                                         │
 *                │           "redator" ──→ [redator]  ──┐ │
 *                │                                      ↓ ↓
 *                │           "finalizar" ──────────→ [finalizar] → END
 *                └───────────────────────────────────────┘
 *
 */

import "dotenv/config";
import { Annotation, StateGraph, START, END } from "@langchain/langgraph";
import { ChatAnthropic } from "@langchain/anthropic";
import { tool } from "@langchain/core/tools";
import { ToolNode } from "@langchain/langgraph/prebuilt";
import {
  BaseMessage,
  HumanMessage,
  SystemMessage,
  AIMessage,
} from "@langchain/core/messages";
import { z } from "zod";

// ─────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────

type ProximoAgente = "analista" | "redator" | "finalizar";

// ─────────────────────────────────────────────
// 1. ESTADO COMPARTILHADO
// ─────────────────────────────────────────────
//
// Todos os agentes leem e escrevem no mesmo estado.
// Isso permite que o redator acesse os dados que o analista calculou.
//

const MultiAgenteState = Annotation.Root({
  // Tarefa original do usuário
  tarefa: Annotation<string>,

  // Qual agente deve executar a próxima etapa
  proximoAgente: Annotation<ProximoAgente>,

  // Trabalho produzido pelo agente analista
  analiseRealizada: Annotation<string>,

  // Trabalho produzido pelo agente redator
  relatorioRedigido: Annotation<string>,

  // Resultado final consolidado
  resultadoFinal: Annotation<string>,

  // Histórico de mensagens de cada agente (para contexto)
  mensagensAnalista: Annotation<BaseMessage[]>({
    reducer: (atual, novas) => [...(atual ?? []), ...novas],
    default: () => [],
  }),

  mensagensRedator: Annotation<BaseMessage[]>({
    reducer: (atual, novas) => [...(atual ?? []), ...novas],
    default: () => [],
  }),

  // Log das decisões do supervisor
  decisoesSupervisor: Annotation<string[]>({
    reducer: (atual, novas) => [...(atual ?? []), ...novas],
    default: () => [],
  }),
});

type Estado = typeof MultiAgenteState.State;

// ─────────────────────────────────────────────
// 2. MODELOS LLM
// ─────────────────────────────────────────────

const llm = new ChatAnthropic({
  model: "claude-haiku-4-5-20251001",
  temperature: 0,
});

// ─────────────────────────────────────────────
// 3. FERRAMENTAS DO ANALISTA
// ─────────────────────────────────────────────

const calcularEstatisticas = tool(
  async ({ numeros }) => {
    const soma = numeros.reduce((a: number, b: number) => a + b, 0);
    const media = soma / numeros.length;
    const minimo = Math.min(...numeros);
    const maximo = Math.max(...numeros);
    const variancia =
      numeros.reduce((acc: number, n: number) => acc + Math.pow(n - media, 2), 0) /
      numeros.length;
    const desvioPadrao = Math.sqrt(variancia);

    return JSON.stringify({ soma, media: media.toFixed(2), minimo, maximo, desvioPadrao: desvioPadrao.toFixed(2), contagem: numeros.length });
  },
  {
    name: "calcularEstatisticas",
    description: "Calcula estatísticas descritivas de uma lista de números",
    schema: z.object({
      numeros: z.array(z.number()).describe("Lista de números para análise"),
    }),
  }
);

const identificarTendencia = tool(
  async ({ valores, periodos }) => {
    const n = valores.length;
    const ultimosTres = valores.slice(-3);
    const tendencia =
      ultimosTres[2] > ultimosTres[0]
        ? "crescente"
        : ultimosTres[2] < ultimosTres[0]
        ? "decrescente"
        : "estável";

    const variacao = (((valores[n - 1] - valores[0]) / valores[0]) * 100).toFixed(1);

    return JSON.stringify({ tendencia, variacaoTotal: `${variacao}%`, periodos, valores });
  },
  {
    name: "identificarTendencia",
    description: "Identifica tendência em uma série temporal de valores",
    schema: z.object({
      valores: z.array(z.number()).describe("Série histórica de valores"),
      periodos: z.array(z.string()).describe("Rótulos dos períodos"),
    }),
  }
);

const ferramentasAnalista = [calcularEstatisticas, identificarTendencia];

// ─────────────────────────────────────────────
// 4. AGENTE SUPERVISOR
// ─────────────────────────────────────────────

async function supervisor(estado: Estado): Promise<Partial<Estado>> {
  console.log("\n🎯 [supervisor] Avaliando situação...");

  // O supervisor usa function calling para retornar uma decisão estruturada
  const modeloComEsquema = llm.withStructuredOutput(
    z.object({
      proximo: z
        .enum(["analista", "redator", "finalizar"])
        .describe(
          "Próximo agente: 'analista' para análise de dados, " +
          "'redator' para redigir relatório (após análise), " +
          "'finalizar' quando o trabalho estiver completo"
        ),
      justificativa: z.string().describe("Motivo da decisão"),
    })
  );

  const contexto = `
Tarefa: ${estado.tarefa}
Análise realizada: ${estado.analiseRealizada || "Ainda não feita"}
Relatório redigido: ${estado.relatorioRedigido || "Ainda não feito"}
  `.trim();

  const decisao = await modeloComEsquema.invoke([
    new SystemMessage(
      "Você é um supervisor que coordena agentes especializados. " +
      "Avalie o progresso e decida qual agente deve agir a seguir. " +
      "Sequência típica: analista primeiro, depois redator, depois finalizar."
    ),
    new HumanMessage(contexto),
  ]);

  console.log(`   Decisão: ${decisao.proximo} — ${decisao.justificativa}`);

  return {
    proximoAgente: decisao.proximo as ProximoAgente,
    decisoesSupervisor: [`${decisao.proximo}: ${decisao.justificativa}`],
  };
}

// ─────────────────────────────────────────────
// 5. AGENTE ANALISTA
// ─────────────────────────────────────────────

const llmAnalista = new ChatAnthropic({
  model: "claude-haiku-4-5-20251001",
  temperature: 0,
}).bindTools(ferramentasAnalista);

async function analista(estado: Estado): Promise<Partial<Estado>> {
  console.log("\n📊 [analista] Realizando análise...");

  const mensagensIniciais: BaseMessage[] = [
    new SystemMessage(
      "Você é um analista de dados especialista. " +
      "Analise os dados da tarefa usando as ferramentas disponíveis. " +
      "Seja preciso e objetivo na análise."
    ),
    new HumanMessage(estado.tarefa),
  ];

  // Loop ReAct: o analista pode chamar ferramentas múltiplas vezes
  let mensagens = mensagensIniciais;
  let analiseTexto = "";

  for (let i = 0; i < 5; i++) { // máximo 5 iterações
    const resposta = await llmAnalista.invoke(mensagens);
    mensagens = [...mensagens, resposta];

    if (!resposta.tool_calls || resposta.tool_calls.length === 0) {
      // Sem mais ferramentas: o analista chegou à conclusão
      analiseTexto = resposta.content as string;
      console.log("   ✓ Análise concluída");
      break;
    }

    console.log(
      `   → Usando ferramenta(s): ${resposta.tool_calls.map((t) => t.name).join(", ")}`
    );

    // Executa as ferramentas
    const resultadoTools = await new ToolNode(ferramentasAnalista).invoke({
      messages: mensagens,
    });

    mensagens = [...mensagens, ...resultadoTools.messages];
  }

  return {
    analiseRealizada: analiseTexto,
    mensagensAnalista: mensagens,
  };
}

// ─────────────────────────────────────────────
// 6. AGENTE REDATOR
// ─────────────────────────────────────────────

async function redator(estado: Estado): Promise<Partial<Estado>> {
  console.log("\n✍️  [redator] Redigindo relatório...");

  const resposta = await llm.invoke([
    new SystemMessage(
      "Você é um redator especializado em relatórios executivos. " +
      "Transforme a análise técnica em um relatório claro e profissional. " +
      "Use formatação markdown com títulos, bullets e destaques."
    ),
    new HumanMessage(
      `Tarefa original: ${estado.tarefa}\n\n` +
      `Análise realizada pelo analista:\n${estado.analiseRealizada}\n\n` +
      "Escreva um relatório executivo baseado nessa análise."
    ),
  ]);

  console.log("   ✓ Relatório redigido");

  return {
    relatorioRedigido: resposta.content as string,
    mensagensRedator: [
      new HumanMessage("Redija o relatório"),
      resposta as AIMessage,
    ],
  };
}

// ─────────────────────────────────────────────
// 7. NÓ FINALIZAR
// ─────────────────────────────────────────────

function finalizar(estado: Estado): Partial<Estado> {
  console.log("\n🏁 [finalizar] Consolidando resultado...");

  const resultado = `
# Trabalho Concluído

## Relatório Final
${estado.relatorioRedigido}

---
*Gerado por: Supervisor → Analista → Redator*
*Decisões do supervisor:*
${estado.decisoesSupervisor.map((d) => `  - ${d}`).join("\n")}
  `.trim();

  return { resultadoFinal: resultado };
}

// ─────────────────────────────────────────────
// 8. FUNÇÃO DE ROTEAMENTO DO SUPERVISOR
// ─────────────────────────────────────────────

function rotearSupervisor(estado: Estado): ProximoAgente | typeof END {
  const proximo = estado.proximoAgente;
  if (proximo === "finalizar") return "finalizar";
  return proximo;
}

// ─────────────────────────────────────────────
// 9. GRAFO MULTI-AGENTE
// ─────────────────────────────────────────────

const grafo = new StateGraph(MultiAgenteState)
  .addNode("supervisor", supervisor)
  .addNode("analista", analista)
  .addNode("redator", redator)
  .addNode("finalizar", finalizar)

  .addEdge(START, "supervisor")

  // O supervisor decide para onde ir
  .addConditionalEdges("supervisor", rotearSupervisor, {
    analista: "analista",
    redator: "redator",
    finalizar: "finalizar",
  })

  // Após cada agente, volta ao supervisor para avaliação
  .addEdge("analista", "supervisor")
  .addEdge("redator", "supervisor")

  .addEdge("finalizar", END)
  .compile();

// ─────────────────────────────────────────────
// 10. EXECUÇÃO
// ─────────────────────────────────────────────

async function main() {
  console.log("═══════════════════════════════════════════════════════════");
  console.log("  MÓDULO 05 — MULTI-AGENT");
  console.log("═══════════════════════════════════════════════════════════");

  const tarefa =
    "Analise as vendas mensais do último trimestre: " +
    "Janeiro: R$45.000, Fevereiro: R$52.000, Março: R$61.000. " +
    "Calcule as estatísticas e identifique a tendência. " +
    "Depois prepare um relatório executivo com os insights.";

  console.log(`\n📋 Tarefa: ${tarefa}`);

  const resultado = await grafo.invoke({ tarefa });

  console.log("\n" + "═".repeat(60));
  console.log("📄 RESULTADO FINAL:");
  console.log("═".repeat(60));
  console.log(resultado.resultadoFinal);
}

main();
