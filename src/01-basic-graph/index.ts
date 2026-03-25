/**
 * MÓDULO 01 — GRAFO BÁSICO
 * ========================
 *
 * Conceito central do LangGraph: tudo é um grafo.
 *
 * Um grafo é composto por:
 *   - NODES (nós): funções que recebem o estado atual e retornam um estado parcial
 *   - EDGES (arestas): conexões entre nós que definem o fluxo de execução
 *   - STATE (estado): um objeto compartilhado que trafega por todo o grafo
 *
 * Neste módulo NÃO usamos LLM — o foco é entender a estrutura do grafo puro.
 *
 * Fluxo deste exemplo:
 *
 *   START → [receberTexto] → [processarTexto] → [formatarResultado] → END
 *
 */

import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

// ─────────────────────────────────────────────
// 1. DEFINIÇÃO DO ESTADO
// ─────────────────────────────────────────────
//
// O estado é o "objeto compartilhado" que percorre todo o grafo.
// Cada nó pode ler qualquer campo e retornar atualizações parciais.
//
// Annotation.Root define o schema do estado com tipos TypeScript.
// Cada campo pode ter um "reducer" que controla como atualizações são mescladas.
//
const PipelineState = Annotation.Root({
  // Campo simples: o último valor escrito vence (comportamento padrão)
  textoOriginal: Annotation<string>,
  textoProcessado: Annotation<string>,
  resultado: Annotation<string>,

  // Campo com reducer customizado: acumula valores em um array
  // Isso é muito útil para manter um histórico de etapas
  etapas: Annotation<string[]>({
    reducer: (estadoAtual, novaEtapa) => [...(estadoAtual ?? []), ...novaEtapa],
    default: () => [],
  }),
});

// TypeScript helper: extrai o tipo do estado para uso nos nós
type Estado = typeof PipelineState.State;

// ─────────────────────────────────────────────
// 2. DEFINIÇÃO DOS NÓS
// ─────────────────────────────────────────────
//
// Um nó é simplesmente uma função com a assinatura:
//   (estado: Estado) => Partial<Estado>
//
// Ela recebe o estado completo e retorna APENAS os campos que quer atualizar.
// O LangGraph se encarrega de mesclar as atualizações no estado global.
//

// Nó 1: Valida e registra o texto recebido
function receberTexto(estado: Estado): Partial<Estado> {
  console.log("\n📥 [receberTexto] Texto recebido:", estado.textoOriginal);

  return {
    etapas: [`Texto recebido com ${estado.textoOriginal.length} caracteres`],
  };
}

// Nó 2: Aplica transformações no texto
function processarTexto(estado: Estado): Partial<Estado> {
  const processado = estado.textoOriginal
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "_"); // substitui espaços por underscores

  console.log("\n⚙️  [processarTexto] Texto processado:", processado);

  return {
    textoProcessado: processado,
    etapas: [`Texto transformado: "${processado}"`],
  };
}

// Nó 3: Formata o resultado final
function formatarResultado(estado: Estado): Partial<Estado> {
  const resultado = `[RESULTADO]: ${estado.textoProcessado}`;

  console.log("\n✅ [formatarResultado] Resultado final:", resultado);

  return {
    resultado,
    etapas: ["Resultado formatado com sucesso"],
  };
}

// ─────────────────────────────────────────────
// 3. CONSTRUÇÃO DO GRAFO
// ─────────────────────────────────────────────
//
// StateGraph recebe o schema do estado como parâmetro.
// O padrão builder (encadeamento de métodos) torna a construção legível.
//

const grafo = new StateGraph(PipelineState)
  // Registra os nós
  .addNode("receberTexto", receberTexto)
  .addNode("processarTexto", processarTexto)
  .addNode("formatarResultado", formatarResultado)

  // Define as arestas (fluxo de execução)
  // START e END são constantes especiais do LangGraph
  .addEdge(START, "receberTexto")
  .addEdge("receberTexto", "processarTexto")
  .addEdge("processarTexto", "formatarResultado")
  .addEdge("formatarResultado", END)

  // compile() valida o grafo e retorna um objeto executável
  .compile();

// ─────────────────────────────────────────────
// 4. EXECUÇÃO
// ─────────────────────────────────────────────

async function main() {
  console.log("═══════════════════════════════════════");
  console.log("  MÓDULO 01 — GRAFO BÁSICO");
  console.log("═══════════════════════════════════════");

  // invoke() executa o grafo com um estado inicial
  // Retorna o estado final após todos os nós terem sido processados
  const estadoFinal = await grafo.invoke({
    textoOriginal: "hello world langgraph",
  });

  console.log("\n─────────────────────────────────────");
  console.log("📊 ESTADO FINAL COMPLETO:");
  console.log("─────────────────────────────────────");
  console.log("Texto original: ", estadoFinal.textoOriginal);
  console.log("Texto processado:", estadoFinal.textoProcessado);
  console.log("Resultado:       ", estadoFinal.resultado);
  console.log("\nEtapas executadas:");
  estadoFinal.etapas.forEach((etapa, i) => console.log(`  ${i + 1}. ${etapa}`));
}

main();
