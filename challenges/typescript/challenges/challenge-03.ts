/**
 * DESAFIO 03 — CICLO REACT MANUAL
 * =================================
 *
 * Conceitos testados: Módulo 04
 *   - Loop ReAct (agente ↔ ferramentas)
 *   - Estado com BaseMessage[] e add_messages
 *   - Conditional edges para controlar o loop
 *   - ToolNode para executar ferramentas
 *
 * CENÁRIO:
 * Implemente um agente ReAct que resolve problemas matemáticos usando
 * ferramentas. O agente deve:
 *   1. Receber uma pergunta matemática
 *   2. Decidir qual ferramenta usar (ou responder diretamente)
 *   3. Executar a ferramenta
 *   4. Usar o resultado para responder
 *
 * FERRAMENTAS DISPONÍVEIS (já implementadas):
 *   - somar(a, b)        → retorna a + b
 *   - multiplicar(a, b)  → retorna a * b
 *   - potencia(base, exp) → retorna base ^ exp
 *
 * FLUXO DO GRAFO (ReAct):
 *
 *   START → [agente] ──(tem tool_calls?)──→ SIM → [executar_tools] ──┐
 *               ↑                                                      │
 *               └──────────────────────────────────────────────────────┘
 *               │
 *           NÃO → END
 *
 * TESTES:
 * Os testes usam um LLM MOCKADO que simula respostas predefinidas.
 * Você não precisa de ANTHROPIC_API_KEY para rodar os testes.
 *
 * 🎯 BÔNUS (opcional, requer ANTHROPIC_API_KEY):
 * Depois de passar nos testes com o mock, substitua o llmMock pelo Claude real:
 *   import { ChatAnthropic } from "@langchain/anthropic";
 *   const modelo = new ChatAnthropic({ model: "claude-haiku-4-5-20251001" }).bindTools(ferramentas);
 * E teste com perguntas reais de matemática.
 *
 * INSTRUÇÕES:
 *   1. Implemente o nó "agente" que chama o LLM
 *   2. Implemente a função verificarProximoPasso
 *   3. Monte o grafo com o loop ReAct
 */

import { Annotation, StateGraph, START, END } from "@langchain/langgraph";
import { ToolNode } from "@langchain/langgraph/prebuilt";
import { tool } from "@langchain/core/tools";
import { BaseMessage, AIMessage } from "@langchain/core/messages";
import { z } from "zod";

// ─────────────────────────────────────────────
// FERRAMENTAS (já implementadas)
// ─────────────────────────────────────────────

export const somar = tool(
  async ({ a, b }: { a: number; b: number }) => String(a + b),
  {
    name: "somar",
    description: "Soma dois números",
    schema: z.object({ a: z.number(), b: z.number() }),
  }
);

export const multiplicar = tool(
  async ({ a, b }: { a: number; b: number }) => String(a * b),
  {
    name: "multiplicar",
    description: "Multiplica dois números",
    schema: z.object({ a: z.number(), b: z.number() }),
  }
);

export const potencia = tool(
  async ({ base, exp }: { base: number; exp: number }) => String(Math.pow(base, exp)),
  {
    name: "potencia",
    description: "Calcula base elevado ao expoente",
    schema: z.object({ base: z.number(), exp: z.number() }),
  }
);

export const ferramentas = [somar, multiplicar, potencia];

// ─────────────────────────────────────────────
// ESTADO
// ─────────────────────────────────────────────
//
// Use Annotation com reducer de acumulação para messages.
// DICA: Importe add_messages de @langchain/langgraph e use como reducer.
//

export const AgenteState = Annotation.Root({
  // TODO: adicione o campo messages com o reducer correto
  // messages: Annotation<BaseMessage[]>({ reducer: ..., default: ... }),
});

export type Estado = typeof AgenteState.State;

// ─────────────────────────────────────────────
// INTERFACE DO LLM (para permitir injeção do mock nos testes)
// ─────────────────────────────────────────────

export interface LLMInterface {
  invoke(messages: BaseMessage[]): Promise<AIMessage>;
}

// ─────────────────────────────────────────────
// TODO 1: Implemente o nó "agente"
// ─────────────────────────────────────────────
//
// O nó deve:
//   - Chamar llm.invoke(estado.messages)
//   - Retornar a resposta como { messages: [resposta] }
//
// O parâmetro `llm` é injetado para permitir usar mock nos testes.
//

export function criarNoAgente(llm: LLMInterface) {
  return async function agente(estado: Estado): Promise<Partial<Estado>> {
    // TODO: implemente o nó agente
    throw new Error("TODO: implemente o nó agente");
  };
}

// ─────────────────────────────────────────────
// TODO 2: Implemente a função de roteamento
// ─────────────────────────────────────────────
//
// Verifica se a última mensagem tem tool_calls:
//   - Se sim → retorna "executar_tools"
//   - Se não → retorna END
//

export function verificarProximoPasso(estado: Estado): "executar_tools" | typeof END {
  // TODO: implemente a verificação de tool_calls
  throw new Error("TODO: implemente verificarProximoPasso");
}

// ─────────────────────────────────────────────
// TODO 3: Monte o grafo
// ─────────────────────────────────────────────
//
// O LLM é injetado para permitir usar mock nos testes.
// Em uso real, passe o modelo real aqui.
//

export function criarGrafo(llm: LLMInterface) {
  // TODO: monte e retorne o grafo compilado com o loop ReAct
  throw new Error("TODO: monte o grafo");
}

// ─────────────────────────────────────────────
// 🎯 BÔNUS: Use com Claude real (requer ANTHROPIC_API_KEY)
// ─────────────────────────────────────────────
//
// import "dotenv/config";
// import { ChatAnthropic } from "@langchain/anthropic";
//
// const claudeReal = new ChatAnthropic({
//   model: "claude-haiku-4-5-20251001",
//   temperature: 0,
// }).bindTools(ferramentas);
//
// const grafoReal = criarGrafo(claudeReal as LLMInterface);
// const resultado = await grafoReal.invoke({
//   messages: [new HumanMessage("Quanto é (3 + 4) elevado ao quadrado?")],
// });
// console.log(resultado.messages[resultado.messages.length - 1].content);
