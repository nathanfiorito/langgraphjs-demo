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
 * COMO OS MOCKS FUNCIONAM:
 *
 * Os testes injetam diferentes implementações de SupervisorInterface para
 * verificar tanto o fluxo correto quanto a robustez do guardrail:
 *
 * ┌─ criarSupervisorCorreto ───────────────────────────────────────────────┐
 * │  Toma decisões na ordem certa: revisor → formatador → publicador       │
 * │  Verifica que o pipeline completo funciona normalmente                 │
 * └────────────────────────────────────────────────────────────────────────┘
 *
 * ┌─ criarSupervisorMalicioso ─────────────────────────────────────────────┐
 * │  Sempre retorna "publicador" — tenta pular todas as etapas             │
 * │  Verifica que o guardrail CORRIGE a decisão errada                     │
 * └────────────────────────────────────────────────────────────────────────┘
 *
 * O ponto-chave: o guardrail em rotearSupervisor() é DETERMINÍSTICO.
 * Ele sempre prevalece sobre o que o supervisor (mock ou real) decidiu.
 * Assim, mesmo um LLM real que "alucine" uma ordem errada será corrigido.
 *
 * 🎯 BÔNUS (opcional, requer ANTHROPIC_API_KEY):
 *
 * O withStructuredOutput() faz o Claude retornar JSON validado pelo schema Zod,
 * mas ele não tem o método .decidir() da SupervisorInterface.
 * Por isso, criamos um wrapper fino que adapta a interface.
 * Veja o exemplo completo no bloco comentado ao final do arquivo.
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

// ─────────────────────────────────────────────
// 🎯 BÔNUS: Substituir o mock pelo Claude real
// ─────────────────────────────────────────────
//
// Depois de passar nos testes, você pode trocar o supervisor mock pelo Claude.
//
// O withStructuredOutput() garante que o LLM retorne JSON no schema Zod certo,
// mas o retorno é o objeto diretamente — não tem o método .decidir().
// Por isso criamos um wrapper (SupervisorReal) que adapta a interface.
//
// Passos:
//   1. Copie o bloco abaixo para um arquivo separado (ex: runBonus04.ts)
//   2. Certifique-se de ter ANTHROPIC_API_KEY no arquivo .env na raiz do repo
//   3. Execute: npx tsx runBonus04.ts
//
// import "dotenv/config";
// import { ChatAnthropic } from "@langchain/anthropic";
// import { z } from "zod";
// import { criarGrafo, SupervisorInterface, Estado } from "./challenges/challenge-04.js";
//
// const DecisaoSchema = z.object({
//   proximo: z.enum(["revisor", "formatador", "publicador"]),
//   motivo: z.string(),
// });
//
// // Wrapper que adapta o LLM estruturado à SupervisorInterface
// class SupervisorReal implements SupervisorInterface {
//   private chain = new ChatAnthropic({
//     model: "claude-haiku-4-5-20251001",
//   }).withStructuredOutput(DecisaoSchema);
//
//   async decidir(estado: Estado) {
//     const prompt = `
//       Você é um supervisor de publicação. Decida o próximo passo.
//       Estado: revisao="${estado.revisao ?? ""}", formatacao="${estado.formatacao ?? ""}"
//       Escolha: revisor, formatador ou publicador.
//     `;
//     // withStructuredOutput retorna o objeto Zod validado diretamente
//     return await this.chain.invoke(prompt);
//   }
// }
//
// // Mesma função criarGrafo dos testes — só o argumento muda
// const grafoReal = criarGrafo(new SupervisorReal());
//
// const config = { configurable: { thread_id: "bonus-01" } };
// const resultado = await grafoReal.invoke(
//   { conteudoOriginal: "Artigo sobre LangGraph e guardrails", historico: [] },
//   config
// );
// console.log("Publicado:", resultado.publicado);
// console.log("URL:", resultado.urlPublicacao);
// console.log("Histórico:", resultado.historico);
