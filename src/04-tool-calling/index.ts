/**
 * MÓDULO 04 — TOOL CALLING (AGENTE COM FERRAMENTAS)
 * ===================================================
 *
 * Aqui entra o LLM! Este módulo implementa o padrão ReAct:
 *
 *   ReAct = Reasoning + Acting
 *   O agente alterna entre "pensar" (raciocinar sobre o problema)
 *   e "agir" (chamar ferramentas para obter informações).
 *
 * Ferramentas (Tools) são funções TypeScript que o LLM pode invocar.
 * O LLM decide QUANDO e COMO chamar cada ferramenta.
 *
 * Fluxo do padrão ReAct:
 *
 *   START → [agente] ──── (precisa de tool) ──→ [executarTools] ─┐
 *               ↑                                                  │
 *               └──────────────────────────────────────────────────┘
 *               │
 *           (resposta final)
 *               ↓
 *              END
 *
 * Ferramentas implementadas (simuladas, sem APIs reais):
 *   - calcularIMC: calcula o Índice de Massa Corporal
 *   - buscarClimaAtual: retorna informações de clima
 *   - converterMoeda: converte valores entre moedas
 *
 */

import "dotenv/config";
import { Annotation, StateGraph, START, END } from "@langchain/langgraph";
import { ToolNode } from "@langchain/langgraph/prebuilt";
import { ChatAnthropic } from "@langchain/anthropic";
import { tool } from "@langchain/core/tools";
import { BaseMessage, HumanMessage } from "@langchain/core/messages";
import { z } from "zod";

// ─────────────────────────────────────────────
// 1. DEFINIÇÃO DAS FERRAMENTAS
// ─────────────────────────────────────────────
//
// tool() recebe dois argumentos:
//   1. A função que executa a lógica
//   2. Um objeto de configuração com nome, descrição e schema (Zod)
//
// O schema Zod define EXATAMENTE quais parâmetros o LLM deve fornecer.
// A descrição ajuda o LLM a entender quando usar a ferramenta.
//

const calcularIMC = tool(
  async ({ peso, altura }) => {
    const imc = peso / (altura * altura);
    let classificacao: string;

    if (imc < 18.5) classificacao = "Abaixo do peso";
    else if (imc < 25) classificacao = "Peso normal";
    else if (imc < 30) classificacao = "Sobrepeso";
    else classificacao = "Obesidade";

    return JSON.stringify({
      imc: imc.toFixed(2),
      classificacao,
      peso,
      altura,
    });
  },
  {
    name: "calcularIMC",
    description:
      "Calcula o Índice de Massa Corporal (IMC) e retorna a classificação. " +
      "Use quando o usuário perguntar sobre IMC, peso ideal ou saúde corporal.",
    schema: z.object({
      peso: z.number().describe("Peso em quilogramas (kg)"),
      altura: z.number().describe("Altura em metros (ex: 1.75)"),
    }),
  }
);

const buscarClimaAtual = tool(
  async ({ cidade }) => {
    // Dados simulados — em produção, chamaria uma API real (ex: OpenWeatherMap)
    const climas: Record<string, object> = {
      "São Paulo": { temperatura: 22, sensacao: 20, condicao: "Parcialmente nublado", umidade: 75 },
      "Rio de Janeiro": { temperatura: 30, sensacao: 33, condicao: "Ensolarado", umidade: 80 },
      "Curitiba": { temperatura: 15, sensacao: 13, condicao: "Chuvoso", umidade: 90 },
      "Porto Alegre": { temperatura: 18, sensacao: 16, condicao: "Nublado", umidade: 85 },
    };

    const clima = climas[cidade] ?? {
      temperatura: 20,
      sensacao: 19,
      condicao: "Dados não disponíveis para esta cidade",
      umidade: 70,
    };

    return JSON.stringify({ cidade, ...clima, unidade: "Celsius" });
  },
  {
    name: "buscarClimaAtual",
    description:
      "Busca as condições climáticas atuais de uma cidade brasileira. " +
      "Retorna temperatura, sensação térmica, condição do céu e umidade.",
    schema: z.object({
      cidade: z.string().describe("Nome da cidade brasileira"),
    }),
  }
);

const converterMoeda = tool(
  async ({ valor, moedaOrigem, moedaDestino }) => {
    // Taxas simuladas em relação ao USD
    const taxas: Record<string, number> = {
      USD: 1.0,
      BRL: 5.0,
      EUR: 0.92,
      GBP: 0.79,
      JPY: 149.5,
    };

    const origem = moedaOrigem.toUpperCase();
    const destino = moedaDestino.toUpperCase();

    if (!taxas[origem] || !taxas[destino]) {
      return JSON.stringify({ erro: `Moeda não suportada: ${origem} ou ${destino}` });
    }

    const valorEmUSD = valor / taxas[origem];
    const valorConvertido = valorEmUSD * taxas[destino];

    return JSON.stringify({
      valorOriginal: valor,
      moedaOrigem: origem,
      valorConvertido: valorConvertido.toFixed(2),
      moedaDestino: destino,
      taxa: (taxas[destino] / taxas[origem]).toFixed(4),
    });
  },
  {
    name: "converterMoeda",
    description:
      "Converte um valor monetário de uma moeda para outra. " +
      "Moedas suportadas: USD, BRL, EUR, GBP, JPY.",
    schema: z.object({
      valor: z.number().describe("Valor a ser convertido"),
      moedaOrigem: z.string().describe("Código da moeda de origem (ex: BRL)"),
      moedaDestino: z.string().describe("Código da moeda de destino (ex: USD)"),
    }),
  }
);

const ferramentas = [calcularIMC, buscarClimaAtual, converterMoeda];

// ─────────────────────────────────────────────
// 2. MODELO LLM COM FERRAMENTAS VINCULADAS
// ─────────────────────────────────────────────
//
// bindTools() informa ao Claude quais ferramentas ele pode usar.
// O Claude decide autonomamente quando e como invocar cada uma.
//

const modelo = new ChatAnthropic({
  model: "claude-haiku-4-5-20251001", // Haiku: rápido e econômico para demos
  temperature: 0,
}).bindTools(ferramentas);

// ─────────────────────────────────────────────
// 3. ESTADO
// ─────────────────────────────────────────────
//
// BaseMessage[] é o tipo padrão para conversas com LLMs.
// O reducer concatena as mensagens — nunca sobrescreve.
// Isso preserva o histórico completo da conversa.
//

const AgenteState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (atual, novas) => [...(atual ?? []), ...novas],
    default: () => [],
  }),
});

type Estado = typeof AgenteState.State;

// ─────────────────────────────────────────────
// 4. NÓS
// ─────────────────────────────────────────────

// Nó do agente: chama o LLM com o histórico de mensagens
async function agente(estado: Estado): Promise<Partial<Estado>> {
  console.log(`\n🤖 [agente] Pensando... (${estado.messages.length} msgs no contexto)`);

  const resposta = await modelo.invoke(estado.messages);

  // Verifica se o LLM quer chamar alguma ferramenta
  if (resposta.tool_calls && resposta.tool_calls.length > 0) {
    console.log(
      `   → Solicitando ferramenta(s): ${resposta.tool_calls.map((t) => t.name).join(", ")}`
    );
  } else {
    console.log("   → Respondendo diretamente ao usuário");
  }

  return { messages: [resposta] };
}

// ─────────────────────────────────────────────
// 5. FUNÇÃO DE ROTEAMENTO
// ─────────────────────────────────────────────
//
// Verifica a última mensagem:
//   - Se o LLM chamou ferramentas → vai para o nó de ferramentas
//   - Se deu uma resposta final   → termina o grafo
//

function verificarProximoPasso(estado: Estado): "executarTools" | typeof END {
  const ultimaMensagem = estado.messages[estado.messages.length - 1];

  // AIMessage tem a propriedade tool_calls quando o LLM quer usar ferramentas
  if ("tool_calls" in ultimaMensagem && Array.isArray(ultimaMensagem.tool_calls) && ultimaMensagem.tool_calls.length > 0) {
    return "executarTools";
  }

  return END;
}

// ─────────────────────────────────────────────
// 6. GRAFO
// ─────────────────────────────────────────────
//
// ToolNode é um nó pré-construído do LangGraph que:
//   1. Lê as tool_calls da última mensagem
//   2. Executa cada ferramenta com os argumentos fornecidos pelo LLM
//   3. Adiciona as respostas como ToolMessages no estado
//

const grafo = new StateGraph(AgenteState)
  .addNode("agente", agente)
  .addNode("executarTools", new ToolNode(ferramentas))

  .addEdge(START, "agente")

  // Após o agente pensar, decidimos se vamos executar ferramentas ou terminar
  .addConditionalEdges("agente", verificarProximoPasso)

  // Após executar ferramentas, voltamos ao agente para processar os resultados
  .addEdge("executarTools", "agente")

  .compile();

// ─────────────────────────────────────────────
// 7. EXECUÇÃO
// ─────────────────────────────────────────────

async function perguntar(pergunta: string) {
  console.log("\n" + "═".repeat(60));
  console.log(`👤 Usuário: ${pergunta}`);

  const resultado = await grafo.invoke({
    messages: [new HumanMessage(pergunta)],
  });

  const ultimaMensagem = resultado.messages[resultado.messages.length - 1];
  console.log(`\n🤖 Claude: ${ultimaMensagem.content}`);
  console.log(`\n📊 Total de mensagens na conversa: ${resultado.messages.length}`);
}

async function main() {
  console.log("═══════════════════════════════════════════════════════════");
  console.log("  MÓDULO 04 — TOOL CALLING");
  console.log("═══════════════════════════════════════════════════════════");

  // Pergunta 1: usa apenas uma ferramenta
  await perguntar("Qual o clima atual em São Paulo?");

  // Pergunta 2: usa apenas uma ferramenta
  await perguntar("Tenho 80kg e 1,75m de altura. Qual meu IMC?");

  // Pergunta 3: pode usar múltiplas ferramentas
  await perguntar(
    "Tenho R$ 1000 reais. Quanto vale em euros e dólares?"
  );
}

main();
