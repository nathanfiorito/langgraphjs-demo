/**
 * MÓDULO 02 — GERENCIAMENTO DE ESTADO
 * =====================================
 *
 * O estado é o coração do LangGraph. Neste módulo exploramos:
 *
 *   1. Reducers customizados — controlam como atualizações são aplicadas
 *   2. Valores default — inicializam campos automaticamente
 *   3. Estado com tipos complexos — objetos, arrays, unions
 *   4. Como nós leem e escrevem no estado de forma segura
 *
 * Cenário: Um pipeline de análise de texto que acumula métricas
 * ao longo da execução.
 *
 *   START → [analisar] → [calcularMetricas] → [gerarRelatorio] → END
 *
 */

import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

// ─────────────────────────────────────────────
// TIPOS DE APOIO
// ─────────────────────────────────────────────

interface Metrica {
  nome: string;
  valor: number;
}

type StatusAnalise = "pendente" | "em_progresso" | "concluido" | "erro";

// ─────────────────────────────────────────────
// 1. ESTADO COM REDUCERS AVANÇADOS
// ─────────────────────────────────────────────
//
// Reducer é uma função: (estadoAtual, atualização) => novoEstado
//
// Sem reducer (padrão): o novo valor SUBSTITUI o anterior
// Com reducer: você controla a mesclagem
//

const AnaliseState = Annotation.Root({
  // ── Campos simples (último valor vence) ──────────────────────────
  texto: Annotation<string>,
  status: Annotation<StatusAnalise>,

  // ── Array com reducer de acumulação ─────────────────────────────
  // Cada nó pode "adicionar" itens sem sobrescrever o array inteiro
  metricas: Annotation<Metrica[]>({
    reducer: (atual, novas) => [...(atual ?? []), ...novas],
    default: () => [],
  }),

  // ── Array de log com acumulação ──────────────────────────────────
  logs: Annotation<string[]>({
    reducer: (atual, novas) => [...(atual ?? []), ...novas],
    default: () => [],
  }),

  // ── Objeto com reducer de mesclagem (deep merge simples) ─────────
  // Permite que nós atualizem apenas algumas propriedades do objeto
  resumo: Annotation<Record<string, unknown>>({
    reducer: (atual, novo) => ({ ...(atual ?? {}), ...novo }),
    default: () => ({}),
  }),
});

type Estado = typeof AnaliseState.State;

// ─────────────────────────────────────────────
// 2. FUNÇÕES UTILITÁRIAS (não são nós)
// ─────────────────────────────────────────────

function log(mensagem: string): void {
  console.log(`  ℹ️  ${mensagem}`);
}

function contarPalavras(texto: string): number {
  return texto.trim().split(/\s+/).filter(Boolean).length;
}

function contarCaracteres(texto: string): number {
  return texto.replace(/\s/g, "").length;
}

function calcularPalavraMedia(texto: string): number {
  const palavras = texto.trim().split(/\s+/).filter(Boolean);
  if (palavras.length === 0) return 0;
  const totalChars = palavras.reduce((sum, p) => sum + p.length, 0);
  return Math.round(totalChars / palavras.length);
}

// ─────────────────────────────────────────────
// 3. NÓS
// ─────────────────────────────────────────────

// Nó 1: Valida o texto e inicia a análise
function analisar(estado: Estado): Partial<Estado> {
  console.log("\n🔍 [analisar] Iniciando análise...");

  if (!estado.texto || estado.texto.trim().length === 0) {
    log("Texto vazio detectado — marcando como erro");
    return {
      status: "erro",
      logs: ["ERRO: Texto vazio recebido"],
    };
  }

  log(`Texto com ${estado.texto.length} caracteres recebido`);

  return {
    status: "em_progresso",
    logs: [`Análise iniciada — ${new Date().toISOString()}`],
    // Atualização parcial do objeto resumo (o reducer faz o merge)
    resumo: { textoOriginal: estado.texto },
  };
}

// Nó 2: Calcula e acumula métricas no estado
function calcularMetricas(estado: Estado): Partial<Estado> {
  console.log("\n📐 [calcularMetricas] Calculando métricas...");

  // Demonstração importante: lemos do estado global
  // mas retornamos APENAS as atualizações — não o estado completo
  const novasMetricas: Metrica[] = [
    { nome: "palavras", valor: contarPalavras(estado.texto) },
    { nome: "caracteres_sem_espaco", valor: contarCaracteres(estado.texto) },
    { nome: "chars_por_palavra", valor: calcularPalavraMedia(estado.texto) },
    { nome: "total_caracteres", valor: estado.texto.length },
  ];

  novasMetricas.forEach((metrica) => log(`${metrica.nome}: ${metrica.valor}`));

  return {
    // O reducer de `metricas` vai ACUMULAR esses itens (não sobrescrever)
    metricas: novasMetricas,
    logs: [`${novasMetricas.length} métricas calculadas`],
    resumo: { totalMetricas: novasMetricas.length },
  };
}

// Nó 3: Gera o relatório final consolidando o estado
function gerarRelatorio(estado: Estado): Partial<Estado> {
  console.log("\n📄 [gerarRelatorio] Gerando relatório...");

  // Aqui demonstramos que podemos ler TODO o estado acumulado
  const palavrasMetrica = estado.metricas.find((metrica) => metrica.nome === "palavras");
  const charsMetrica = estado.metricas.find(
    (metrica) => metrica.nome === "caracteres_sem_espaco"
  );

  log(`Total de métricas disponíveis: ${estado.metricas.length}`);
  log(`Logs acumulados até agora: ${estado.logs.length}`);

  return {
    status: "concluido",
    logs: ["Relatório gerado com sucesso"],
    // Merge final no objeto resumo
    resumo: {
      palavras: palavrasMetrica?.valor,
      caracteresSemEspaco: charsMetrica?.valor,
      statusFinal: "concluido",
    },
  };
}

// ─────────────────────────────────────────────
// 4. GRAFO
// ─────────────────────────────────────────────

const grafo = new StateGraph(AnaliseState)
  .addNode("analisar", analisar)
  .addNode("calcularMetricas", calcularMetricas)
  .addNode("gerarRelatorio", gerarRelatorio)
  .addEdge(START, "analisar")
  .addEdge("analisar", "calcularMetricas")
  .addEdge("calcularMetricas", "gerarRelatorio")
  .addEdge("gerarRelatorio", END)
  .compile();

// ─────────────────────────────────────────────
// 5. EXECUÇÃO E INSPEÇÃO DO ESTADO
// ─────────────────────────────────────────────

async function main() {
  console.log("═══════════════════════════════════════");
  console.log("  MÓDULO 02 — GERENCIAMENTO DE ESTADO");
  console.log("═══════════════════════════════════════");

  const textoExemplo =
    "O LangGraph permite criar agentes de IA complexos usando grafos de estado. " +
    "Cada nó do grafo recebe o estado atual e retorna atualizações parciais.";

  const resultado = await grafo.invoke({ texto: textoExemplo });

  console.log("\n─────────────────────────────────────");
  console.log("📊 ESTADO FINAL:");
  console.log("─────────────────────────────────────");
  console.log("Status:", resultado.status);

  console.log("\nMétricas acumuladas (via reducer):");
  resultado.metricas.forEach((m) =>
    console.log(`  • ${m.nome.padEnd(25)} = ${m.valor}`)
  );

  console.log("\nResumo (via merge reducer):");
  console.log(JSON.stringify(resultado.resumo, null, 2));

  console.log("\nLogs do pipeline:");
  resultado.logs.forEach((log, i) => console.log(`  ${i + 1}. ${log}`));
}

main();
