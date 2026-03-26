/**
 * MÓDULO 03 — CONDITIONAL EDGES (ROTEAMENTO DINÂMICO)
 * =====================================================
 *
 * Até agora nossos grafos eram lineares: A → B → C.
 * Conditional Edges permitem que o fluxo se ramifique com base no estado.
 *
 * Como funciona:
 *   - addConditionalEdges(nóOrigem, funçãoDeRoteamento, mapaDeDestinos)
 *   - A função de roteamento recebe o estado e retorna uma string (chave)
 *   - O mapa associa cada chave ao nó de destino
 *
 * Cenário: Um sistema de triagem de suporte ao cliente.
 * Com base na urgência e no tipo da solicitação, o fluxo é diferente.
 *
 *                    ┌──────────────────┐
 *                    │    [triagem]     │
 *                    └────────┬─────────┘
 *                             │
 *              ┌──────────────┼──────────────┐
 *              ↓              ↓              ↓
 *         [urgente]     [tecnico]      [geral]
 *              │              │              │
 *              └──────────────┴──────────────┘
 *                             │
 *                      [registrar]
 *                             │
 *                            END
 *
 */

import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

// ─────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────

type TipoSolicitacao = "urgente" | "tecnico" | "geral";
type Prioridade = "alta" | "media" | "baixa";

// ─────────────────────────────────────────────
// ESTADO
// ─────────────────────────────────────────────

const SuporteState = Annotation.Root({
  mensagem: Annotation<string>,
  tipo: Annotation<TipoSolicitacao>,
  prioridade: Annotation<Prioridade>,
  filaDestino: Annotation<string>,
  tempoRespostaEstimado: Annotation<string>,
  acoes: Annotation<string[]>({
    reducer: (atual, novas) => [...(atual ?? []), ...novas],
    default: () => [],
  }),
});

type Estado = typeof SuporteState.State;

// ─────────────────────────────────────────────
// NÓS
// ─────────────────────────────────────────────

// Nó 1: Triagem — analisa a mensagem e classifica
function triagem(estado: Estado): Partial<Estado> {
  console.log("\n🔎 [triagem] Analisando mensagem...");
  console.log(`   Mensagem: "${estado.mensagem}"`);

  // Lógica de classificação simples baseada em palavras-chave
  const msg = estado.mensagem.toLowerCase();

  let tipo: TipoSolicitacao = "geral";
  let prioridade: Prioridade = "baixa";

  if (msg.includes("urgente") || msg.includes("sistema caiu") || msg.includes("fora do ar")) {
    tipo = "urgente";
    prioridade = "alta";
  } else if (msg.includes("bug") || msg.includes("erro") || msg.includes("falha") || msg.includes("api")) {
    tipo = "tecnico";
    prioridade = "media";
  }

  console.log(`   Classificado como: tipo=${tipo}, prioridade=${prioridade}`);

  return {
    tipo,
    prioridade,
    acoes: [`Triagem concluída: ${tipo} (prioridade ${prioridade})`],
  };
}

// ─────────────────────────────────────────────
// FUNÇÃO DE ROTEAMENTO
// ─────────────────────────────────────────────
//
// Esta função é o coração das conditional edges.
// Recebe o estado e retorna uma STRING que indica qual caminho seguir.
//
// IMPORTANTE: O retorno deve corresponder às chaves do mapa passado
// para addConditionalEdges.
//

function rotear(estado: Estado): TipoSolicitacao {
  console.log(`\n🔀 [router] Roteando para: ${estado.tipo}`);
  return estado.tipo; // "urgente" | "tecnico" | "geral"
}

// Nó 2a: Tratamento para casos urgentes
function tratarUrgente(estado: Estado): Partial<Estado> {
  console.log("\n🚨 [tratarUrgente] Escalando para equipe de plantão...");

  return {
    filaDestino: "PLANTÃO_24H",
    tempoRespostaEstimado: "15 minutos",
    acoes: [
      "Alerta enviado para equipe de plantão",
      "SLA de emergência ativado",
      "Notificação para gerente de plantão",
    ],
  };
}

// Nó 2b: Tratamento para problemas técnicos
function tratarTecnico(estado: Estado): Partial<Estado> {
  console.log("\n🔧 [tratarTecnico] Encaminhando para time técnico...");

  return {
    filaDestino: "SUPORTE_TECNICO",
    tempoRespostaEstimado: "2 horas",
    acoes: [
      "Ticket técnico criado",
      "Logs do sistema coletados",
      "Engenheiro de plantão notificado",
    ],
  };
}

// Nó 2c: Tratamento para questões gerais
function tratarGeral(estado: Estado): Partial<Estado> {
  console.log("\n💬 [tratarGeral] Encaminhando para suporte padrão...");

  return {
    filaDestino: "SUPORTE_GERAL",
    tempoRespostaEstimado: "24 horas",
    acoes: [
      "Ticket padrão criado",
      "Email de confirmação enviado ao cliente",
    ],
  };
}

// Nó 3: Registra o resultado final (comum a todos os caminhos)
function registrar(estado: Estado): Partial<Estado> {
  console.log("\n📋 [registrar] Registrando atendimento...");

  return {
    acoes: [
      `Atendimento registrado na fila: ${estado.filaDestino}`,
      `Tempo de resposta estimado: ${estado.tempoRespostaEstimado}`,
    ],
  };
}

// ─────────────────────────────────────────────
// GRAFO
// ─────────────────────────────────────────────

const grafo = new StateGraph(SuporteState)
  .addNode("triagem", triagem)
  .addNode("tratarUrgente", tratarUrgente)
  .addNode("tratarTecnico", tratarTecnico)
  .addNode("tratarGeral", tratarGeral)
  .addNode("registrar", registrar)

  .addEdge(START, "triagem")

  // ── CONDITIONAL EDGE ────────────────────────────────────────────────
  // Após "triagem", a função `rotear` decide o próximo nó.
  // O segundo argumento é a função de roteamento.
  // O terceiro é um mapa: { chave_retornada: nó_destino }
  .addConditionalEdges("triagem", rotear, {
    urgente: "tratarUrgente",
    tecnico: "tratarTecnico",
    geral: "tratarGeral",
  })

  // Todos os caminhos convergem para "registrar"
  .addEdge("tratarUrgente", "registrar")
  .addEdge("tratarTecnico", "registrar")
  .addEdge("tratarGeral", "registrar")

  .addEdge("registrar", END)
  .compile();

// ─────────────────────────────────────────────
// EXECUÇÃO — testamos 3 cenários diferentes
// ─────────────────────────────────────────────

async function testar(mensagem: string) {
  console.log("\n" + "═".repeat(55));
  const resultado = await grafo.invoke({ mensagem });

  console.log("\n─────────────────────────────────────");
  console.log("📊 RESULTADO:");
  console.log(`  Fila:      ${resultado.filaDestino}`);
  console.log(`  SLA:       ${resultado.tempoRespostaEstimado}`);
  console.log("\n  Ações realizadas:");
  resultado.acoes.forEach((a) => console.log(`    • ${a}`));
}

async function main() {
  console.log("═══════════════════════════════════════════════════════");
  console.log("  MÓDULO 03 — CONDITIONAL EDGES");
  console.log("═══════════════════════════════════════════════════════");

  await testar("URGENTE: sistema caiu em produção!");
  await testar("Encontrei um bug na API de pagamentos, retorna erro 500");
  await testar("Gostaria de saber como alterar meus dados cadastrais");
}

main();
