import { describe, it, expect } from "vitest";
import { AIMessage, HumanMessage, ToolMessage } from "@langchain/core/messages";
import { criarGrafo, ferramentas, LLMInterface } from "../challenges/challenge-03.js";

// ─────────────────────────────────────────────
// LLM MOCK
// ─────────────────────────────────────────────
//
// Simula o comportamento do LLM sem chamar a API real.
// O mock retorna tool_calls predefinidos baseados na última mensagem.
//

class LLMMock implements LLMInterface {
  private respostas: AIMessage[];
  private indice = 0;

  constructor(respostas: AIMessage[]) {
    this.respostas = respostas;
  }

  async invoke(_messages: any[]): Promise<AIMessage> {
    const resposta = this.respostas[this.indice];
    this.indice = Math.min(this.indice + 1, this.respostas.length - 1);
    return resposta;
  }
}

// Cria uma AIMessage que simula uma chamada de ferramenta
function criarToolCall(nome: string, args: object, id = "tc_001"): AIMessage {
  return new AIMessage({
    content: "",
    tool_calls: [{ id, name: nome, args }],
  });
}

// ─────────────────────────────────────────────
// TESTES
// ─────────────────────────────────────────────

describe("Desafio 03 — Ciclo ReAct Manual", () => {
  it("executa uma única ferramenta e responde", async () => {
    // Cenário: LLM chama somar(3, 4), recebe 7, responde "O resultado é 7"
    const mock = new LLMMock([
      criarToolCall("somar", { a: 3, b: 4 }),           // 1ª chamada: usa ferramenta
      new AIMessage({ content: "O resultado é 7" }),    // 2ª chamada: responde
    ]);

    const grafo = criarGrafo(mock);
    const resultado = await grafo.invoke({
      messages: [new HumanMessage("Quanto é 3 + 4?")],
    });

    const ultimaMensagem = resultado.messages[resultado.messages.length - 1];
    expect(ultimaMensagem.content).toBe("O resultado é 7");

    // Deve ter: HumanMessage + AIMessage(tool_call) + ToolMessage + AIMessage(resposta)
    expect(resultado.messages.length).toBe(4);
  });

  it("acumula múltiplas mensagens no estado", async () => {
    const mock = new LLMMock([
      criarToolCall("multiplicar", { a: 5, b: 6 }),
      new AIMessage({ content: "5 multiplicado por 6 é 30" }),
    ]);

    const grafo = criarGrafo(mock);
    const resultado = await grafo.invoke({
      messages: [new HumanMessage("Quanto é 5 * 6?")],
    });

    // Verifica que as mensagens foram acumuladas corretamente
    expect(resultado.messages[0]).toBeInstanceOf(HumanMessage);
    // A última deve ser a resposta final (AIMessage sem tool_calls)
    const ultima = resultado.messages[resultado.messages.length - 1];
    expect(ultima).toBeInstanceOf(AIMessage);
    const toolCalls = (ultima as AIMessage).tool_calls ?? [];
    expect(toolCalls.length).toBe(0);
  });

  it("responde diretamente sem usar ferramentas", async () => {
    // LLM decide responder sem chamar nenhuma ferramenta
    const mock = new LLMMock([
      new AIMessage({ content: "Dois mais dois é quatro." }),
    ]);

    const grafo = criarGrafo(mock);
    const resultado = await grafo.invoke({
      messages: [new HumanMessage("Quanto é 2 + 2?")],
    });

    // Deve ter apenas HumanMessage + AIMessage
    expect(resultado.messages.length).toBe(2);
    expect(resultado.messages[1].content).toBe("Dois mais dois é quatro.");
  });

  it("executa múltiplas ferramentas em sequência", async () => {
    // LLM usa duas ferramentas antes de responder
    const mock = new LLMMock([
      criarToolCall("somar", { a: 10, b: 5 }, "tc_001"),
      criarToolCall("potencia", { base: 15, exp: 2 }, "tc_002"),
      new AIMessage({ content: "Primeiro somei 10+5=15, depois elevei ao quadrado: 225" }),
    ]);

    const grafo = criarGrafo(mock);
    const resultado = await grafo.invoke({
      messages: [new HumanMessage("Qual é (10+5) ao quadrado?")],
    });

    // Deve ter: Human + AI(tool1) + Tool + AI(tool2) + Tool + AI(resposta)
    expect(resultado.messages.length).toBe(6);

    const ultima = resultado.messages[resultado.messages.length - 1];
    expect(ultima.content).toContain("225");
  });

  it("as ferramentas retornam o resultado correto", async () => {
    // Verifica se o ToolNode executa as ferramentas corretamente
    const mock = new LLMMock([
      criarToolCall("potencia", { base: 2, exp: 10 }, "tc_pot"),
      new AIMessage({ content: "2^10 = 1024" }),
    ]);

    const grafo = criarGrafo(mock);
    const resultado = await grafo.invoke({
      messages: [new HumanMessage("2 elevado a 10?")],
    });

    // A ToolMessage deve conter o resultado correto da ferramenta
    const toolMessage = resultado.messages.find(
      (m): m is ToolMessage => m instanceof ToolMessage
    );
    expect(toolMessage).toBeDefined();
    expect(toolMessage!.content).toBe("1024");
  });
});
