/**
 * MÓDULO 06 — HUMAN-IN-THE-LOOP
 * ================================
 *
 * Em muitos cenários, o agente precisa de aprovação humana antes de agir.
 * O LangGraph permite PAUSAR a execução, aguardar input humano e CONTINUAR.
 *
 * Conceitos fundamentais:
 *
 *   CHECKPOINTER: persiste o estado do grafo entre execuções
 *     - MemorySaver: salva em memória (ideal para demos e testes)
 *     - Em produção: SqliteSaver, PostgresSaver, etc.
 *
 *   interrupt(): pausa o grafo e retorna controle ao chamador
 *     - Pode passar uma mensagem para o humano
 *     - O grafo fica "congelado" até ser retomado
 *
 *   Command({ resume }): retoma o grafo com a resposta humana
 *     - O valor de `resume` fica disponível como retorno de interrupt()
 *
 *   thread_id: identifica uma "conversa" específica no checkpointer
 *     - Permite múltiplas execuções paralelas independentes
 *
 * Fluxo:
 *
 *   INVOCAÇÃO 1:
 *     START → [rascunharEmail] → [aguardarAprovacao] ← PAUSA AQUI
 *
 *   INVOCAÇÃO 2 (após aprovação humana):
 *     [aguardarAprovacao] → [enviarEmail] → END
 *        ↑                     ↑
 *        |                     |
 *     (se rejeitado)     (se aprovado)
 *        ↓
 *     [revisarEmail] → [aguardarAprovacao] ← PAUSA DE NOVO
 *
 */

import "dotenv/config";
import { Annotation, StateGraph, START, END, interrupt, Command, MemorySaver } from "@langchain/langgraph";
import { ChatAnthropic } from "@langchain/anthropic";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import * as readline from "readline";

// ─────────────────────────────────────────────
// UTILITÁRIO: input interativo no terminal
// ─────────────────────────────────────────────

function perguntarUsuario(prompt: string): Promise<string> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(prompt, (resposta) => {
      rl.close();
      resolve(resposta.trim());
    });
  });
}

// ─────────────────────────────────────────────
// 1. ESTADO
// ─────────────────────────────────────────────

const EmailState = Annotation.Root({
  // Solicitação original do usuário
  solicitacao: Annotation<string>,

  // Destinatário do email
  destinatario: Annotation<string>,

  // Rascunho gerado pelo LLM
  rascunho: Annotation<string>,

  // Feedback do revisor humano (se rejeitado)
  feedbackHumano: Annotation<string>,

  // Número de revisões realizadas
  numeroRevisoes: Annotation<number>,

  // Status final
  status: Annotation<"aguardando" | "aprovado" | "enviado" | "cancelado">,
});

type Estado = typeof EmailState.State;

// ─────────────────────────────────────────────
// 2. LLM
// ─────────────────────────────────────────────

const llm = new ChatAnthropic({
  model: "claude-haiku-4-5-20251001",
  temperature: 0.7, // Um pouco mais criativo para geração de texto
});

// ─────────────────────────────────────────────
// 3. NÓS
// ─────────────────────────────────────────────

// Nó 1: Gera o rascunho do email
async function rascunharEmail(estado: Estado): Promise<Partial<Estado>> {
  const ehRevisao = estado.numeroRevisoes > 0;
  console.log(
    ehRevisao
      ? `\n✏️  [rascunharEmail] Revisando (tentativa ${estado.numeroRevisoes + 1})...`
      : "\n✏️  [rascunharEmail] Gerando rascunho inicial..."
  );

  const prompt = ehRevisao
    ? `Você escreveu o seguinte rascunho de email:\n\n${estado.rascunho}\n\n` +
      `O revisor pediu as seguintes alterações:\n${estado.feedbackHumano}\n\n` +
      "Reescreva o email incorporando o feedback."
    : `Escreva um email profissional para ${estado.destinatario} sobre: ${estado.solicitacao}`;

  const resposta = await llm.invoke([
    new SystemMessage(
      "Você é um redator profissional especializado em comunicação corporativa. " +
      "Escreva emails claros, objetivos e com tom adequado ao contexto. " +
      "Inclua assunto (Subject:), corpo e assinatura."
    ),
    new HumanMessage(prompt),
  ]);

  console.log("   ✓ Rascunho gerado");

  return {
    rascunho: resposta.content as string,
    status: "aguardando",
  };
}

// Nó 2: PAUSA para revisão humana
// ─────────────────────────────────────────────
//
// interrupt() é a função mágica aqui.
// Ela PAUSA o grafo e retorna ao chamador com o valor passado como argumento.
// Quando o grafo for retomado com Command({ resume: valor }),
// interrupt() retorna esse valor.
//
async function aguardarAprovacao(estado: Estado): Promise<Partial<Estado>> {
  console.log("\n" + "─".repeat(60));
  console.log("⏸️  [aguardarAprovacao] AGUARDANDO REVISÃO HUMANA");
  console.log("─".repeat(60));
  console.log(`\n📧 RASCUNHO DO EMAIL (revisão ${estado.numeroRevisoes + 1}):`);
  console.log("─".repeat(60));
  console.log(estado.rascunho);
  console.log("─".repeat(60));

  // interrupt() pausa o grafo aqui.
  // A string passada é retornada para quem chamou graph.invoke()
  // como parte do estado de interrupção.
  //
  // Quando retomado com Command({ resume: "aprovado" }), essa
  // variável receberá "aprovado".
  const decisaoHumana = interrupt(
    "Revise o email acima e responda:\n" +
    "  • 'aprovado' — para enviar o email\n" +
    "  • 'cancelado' — para cancelar\n" +
    "  • Qualquer outro texto — para solicitar alterações\n"
  );

  console.log(`\n👤 Decisão humana recebida: "${decisaoHumana}"`);

  if (decisaoHumana === "aprovado") {
    return { status: "aprovado", feedbackHumano: "" };
  } else if (decisaoHumana === "cancelado") {
    return { status: "cancelado" };
  } else {
    // Qualquer outra resposta é tratada como feedback para revisão
    return {
      status: "aguardando",
      feedbackHumano: decisaoHumana,
      numeroRevisoes: (estado.numeroRevisoes ?? 0) + 1,
    };
  }
}

// Nó 3: Envia o email (simulado)
function enviarEmail(estado: Estado): Partial<Estado> {
  console.log("\n📤 [enviarEmail] Enviando email...");
  console.log(`   Para: ${estado.destinatario}`);
  console.log("   ✓ Email enviado com sucesso!");

  return { status: "enviado" };
}

// Nó 4: Cancela o processo
function cancelar(estado: Estado): Partial<Estado> {
  console.log("\n❌ [cancelar] Processo cancelado pelo usuário.");
  return { status: "cancelado" };
}

// ─────────────────────────────────────────────
// 4. FUNÇÕES DE ROTEAMENTO
// ─────────────────────────────────────────────

function aposAprovacao(estado: Estado): "enviarEmail" | "rascunharEmail" | "cancelar" {
  if (estado.status === "aprovado") return "enviarEmail";
  if (estado.status === "cancelado") return "cancelar";
  return "rascunharEmail"; // precisa de revisão
}

// ─────────────────────────────────────────────
// 5. GRAFO COM CHECKPOINTER
// ─────────────────────────────────────────────
//
// O checkpointer é passado para compile().
// Ele salva o estado após cada nó, permitindo retomar depois.
//

const checkpointer = new MemorySaver();

const grafo = new StateGraph(EmailState)
  .addNode("rascunharEmail", rascunharEmail)
  .addNode("aguardarAprovacao", aguardarAprovacao)
  .addNode("enviarEmail", enviarEmail)
  .addNode("cancelar", cancelar)

  .addEdge(START, "rascunharEmail")
  .addEdge("rascunharEmail", "aguardarAprovacao")

  .addConditionalEdges("aguardarAprovacao", aposAprovacao, {
    enviarEmail: "enviarEmail",
    rascunharEmail: "rascunharEmail",
    cancelar: "cancelar",
  })

  .addEdge("enviarEmail", END)
  .addEdge("cancelar", END)

  // IMPORTANTE: checkpointer é passado aqui
  .compile({ checkpointer });

// ─────────────────────────────────────────────
// 6. EXECUÇÃO COM LOOP HUMAN-IN-THE-LOOP
// ─────────────────────────────────────────────

async function main() {
  console.log("═══════════════════════════════════════════════════════════");
  console.log("  MÓDULO 06 — HUMAN-IN-THE-LOOP");
  console.log("═══════════════════════════════════════════════════════════");

  // thread_id identifica esta "sessão" de trabalho no checkpointer
  // Usar o mesmo thread_id permite retomar de onde parou
  const threadConfig = {
    configurable: { thread_id: "email-session-001" },
  };

  // ── FASE 1: Execução inicial ──────────────────────────────────────
  // O grafo vai rodar até o interrupt() em aguardarAprovacao
  console.log("\n▶️  FASE 1: Gerando rascunho...");

  const estadoInicial = await grafo.invoke(
    {
      solicitacao: "Solicitar reunião para apresentar os resultados do Q1",
      destinatario: "Diretoria Executiva",
      numeroRevisoes: 0,
    },
    threadConfig
  );

  // Quando o grafo é interrompido, invoke() retorna com o estado atual
  // Verificamos se foi interrompido checando o estado do grafo
  const estadoGrafo = await grafo.getState(threadConfig);

  if (estadoGrafo.next.length === 0) {
    console.log("\n✅ Grafo concluído sem interrupção.");
    return;
  }

  console.log(`\n⏸️  Grafo pausado em: ${estadoGrafo.next.join(", ")}`);

  // ── FASE 2: Loop de revisão humana ────────────────────────────────
  let continuar = true;

  while (continuar) {
    // Pergunta ao usuário real o que fazer
    const decisao = await perguntarUsuario(
      "\n👤 Sua decisão (aprovado / cancelado / ou feedback de revisão): "
    );

    console.log("\n▶️  Retomando grafo com decisão humana...");

    // Command({ resume: valor }) retoma o grafo
    // O valor é retornado por interrupt() no nó aguardarAprovacao
    const resultado = await grafo.invoke(
      new Command({ resume: decisao }),
      threadConfig
    );

    // Verifica o estado atual do grafo
    const estadoAtual = await grafo.getState(threadConfig);

    if (estadoAtual.next.length === 0) {
      // Grafo finalizou
      console.log("\n" + "═".repeat(60));
      console.log("🏁 PROCESSO FINALIZADO");
      console.log(`   Status final: ${resultado.status}`);
      continuar = false;
    } else {
      // Ainda está pausado (mais uma revisão foi solicitada)
      console.log(`\n⏸️  Grafo pausado novamente em: ${estadoAtual.next.join(", ")}`);
    }
  }
}

main();
