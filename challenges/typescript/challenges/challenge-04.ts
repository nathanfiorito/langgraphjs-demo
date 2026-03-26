/**
 * DESAFIO 04 — ORQUESTRADOR COM GUARDRAILS
 * ==========================================
 *
 * Conceitos testados: Módulos 05 e 06
 *   - Padrão supervisor com agentes especializados
 *   - Guardrails determinísticos na função de roteamento
 *   - Checkpointer (MemorySaver) para persistência de estado
 *   - Inspeção de estado com getState()
 *
 * CENÁRIO:
 * Implemente um supervisor que orquestra um pipeline de publicação de artigos.
 * O pipeline tem 3 agentes especializados e deve seguir uma sequência OBRIGATÓRIA:
 *
 *   1. "revisor"   — revisa o conteúdo do artigo
 *   2. "formatador" — formata o artigo revisado
 *   3. "publicador" — publica o artigo formatado
 *
 * REGRAS DO GUARDRAIL (implemente em rotearSupervisor):
 *
 *   - Se `revisao` estiver vazia → SEMPRE ir para "revisor"
 *   - Se `revisao` preenchida e `formatacao` vazia → SEMPRE ir para "formatador"
 *   - Se ambas preenchidas → ir para "publicador" (ou o que o supervisor disse)
 *   - NUNCA ir para "publicador" se `formatacao` estiver vazia
 *
 * O supervisor usa um mock que pode tomar decisões erradas intencionalmente,
 * e o guardrail deve corrigi-las.
 *
 * FLUXO:
 *   START → [supervisor] ──(guardrail)──→ [revisor]    ──→ [supervisor]
 *                                       → [formatador] ──→ [supervisor]
 *                                       → [publicador] ──→ END
 *
 * TESTES:
 * Os testes verificam tanto o fluxo correto quanto a correção pelo guardrail.
 *
 * 🎯 BÔNUS (opcional, requer ANTHROPIC_API_KEY):
 * Substitua o supervisorMock pelo Claude real usando withStructuredOutput:
 *   import { ChatAnthropic } from "@langchain/anthropic";
 *   import { z } from "zod";
 *   const llm = new ChatAnthropic({ model: "claude-haiku-4-5-20251001" });
 *   const supervisorReal = llm.withStructuredOutput(z.object({
 *     proximo: z.enum(["revisor", "formatador", "publicador"]),
 *   }));
 *
 * INSTRUÇÕES:
 *   1. Implemente rotearSupervisor() com os guardrails
 *   2. Implemente os 3 agentes especializados
 *   3. Monte o grafo com MemorySaver
 */

import { Annotation, StateGraph, START, END, MemorySaver } from "@langchain/langgraph";

// ─────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────

export type ProximoAgente = "revisor" | "formatador" | "publicador";

// ─────────────────────────────────────────────
// ESTADO (já definido)
// ─────────────────────────────────────────────

export const PublicacaoState = Annotation.Root({
  conteudoOriginal: Annotation<string>,
  proximoAgente: Annotation<ProximoAgente>,
  revisao: Annotation<string>,
  formatacao: Annotation<string>,
  publicado: Annotation<boolean>,
  urlPublicacao: Annotation<string>,
  historico: Annotation<string[]>({
    reducer: (atual, novas) => [...(atual ?? []), ...novas],
    default: () => [],
  }),
});

export type Estado = typeof PublicacaoState.State;

// ─────────────────────────────────────────────
// INTERFACE DO SUPERVISOR (para injeção do mock)
// ─────────────────────────────────────────────

export interface SupervisorInterface {
  decidir(estado: Estado): Promise<{ proximo: ProximoAgente; motivo: string }>;
}

// ─────────────────────────────────────────────
// NÓ SUPERVISOR (já implementado)
// ─────────────────────────────────────────────

export function criarNoSupervisor(supervisor: SupervisorInterface) {
  return async function supervisorNo(estado: Estado): Promise<Partial<Estado>> {
    console.log("\n🎯 [supervisor] Avaliando...");
    const decisao = await supervisor.decidir(estado);
    console.log(`   Decisão: ${decisao.proximo} — ${decisao.motivo}`);
    return {
      proximoAgente: decisao.proximo,
      historico: [`supervisor → ${decisao.proximo}: ${decisao.motivo}`],
    };
  };
}

// ─────────────────────────────────────────────
// TODO 1: Implemente a função de roteamento COM GUARDRAILS
// ─────────────────────────────────────────────
//
// Aplique as regras do guardrail descritas no topo do arquivo.
// Se o supervisor tomou uma decisão errada, corrija-a e logue um aviso.
//

export function rotearSupervisor(estado: Estado): ProximoAgente | typeof END {
  // TODO: implemente com guardrails
  throw new Error("TODO: implemente rotearSupervisor com guardrails");
}

// ─────────────────────────────────────────────
// TODO 2: Implemente os 3 agentes especializados
// ─────────────────────────────────────────────

export function revisor(estado: Estado): Partial<Estado> {
  // TODO: deve preencher o campo `revisao` com uma versão revisada do conteúdo
  // e adicionar uma entrada no historico
  throw new Error("TODO: implemente o revisor");
}

export function formatador(estado: Estado): Partial<Estado> {
  // TODO: deve preencher o campo `formatacao` com o conteúdo da revisao formatado
  // e adicionar uma entrada no historico
  // DICA: Adicione markdown, ex: "## Título\n\n" + revisao
  throw new Error("TODO: implemente o formatador");
}

export function publicador(estado: Estado): Partial<Estado> {
  // TODO: deve setar publicado=true, gerar uma urlPublicacao fictícia
  // e adicionar uma entrada no historico
  // DICA: urlPublicacao pode ser "https://blog.exemplo.com/artigo-001"
  throw new Error("TODO: implemente o publicador");
}

// ─────────────────────────────────────────────
// TODO 3: Monte o grafo com checkpointer
// ─────────────────────────────────────────────
//
// Use MemorySaver como checkpointer.
// O supervisor é injetado para permitir mock nos testes.
//

export function criarGrafo(supervisor: SupervisorInterface) {
  const checkpointer = new MemorySaver();
  // TODO: monte e retorne o grafo compilado com checkpointer
  throw new Error("TODO: monte o grafo");
}
