/**
 * DESAFIO 02 — ROTEAMENTO INTELIGENTE
 * =====================================
 *
 * Conceitos testados: Módulo 03
 *   - addConditionalEdges com roteamento por múltiplos critérios
 *   - Funções de roteamento que retornam strings
 *   - Grafos com múltiplos caminhos convergindo
 *
 * CENÁRIO:
 * Você deve construir um sistema de roteamento de notificações.
 * Com base no tipo e urgência da notificação, ela é enviada
 * por canais diferentes.
 *
 * REGRAS DE ROTEAMENTO (implemente na função rotear):
 *
 *   urgente + sistema   → "incidente"  (canal de incidentes — alerta imediato)
 *   urgente + negocio   → "escalada"   (canal de escalada — decisores)
 *   urgente + outro     → "urgencia"   (canal de urgência geral)
 *   normal  + sistema   → "tecnico"    (canal técnico)
 *   normal  + negocio   → "comercial"  (canal comercial)
 *   normal  + outro     → "padrao"     (canal padrão)
 *
 * FLUXO DO GRAFO:
 *
 *   START → [classificar] ──(condicional)──→ [incidente]  ──┐
 *                                          → [escalada]   ──┤
 *                                          → [urgencia]   ──┤
 *                                          → [tecnico]    ──┤
 *                                          → [comercial]  ──┤
 *                                          → [padrao]     ──┤
 *                                                            ↓
 *                                               [registrar_envio] → END
 *
 * INSTRUÇÕES:
 *   1. Implemente a função rotear()
 *   2. Implemente os 6 handlers de canal
 *   3. Monte o grafo com addConditionalEdges
 */

import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

// ─────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────

export type Urgencia = "urgente" | "normal";
export type TipoNotificacao = "sistema" | "negocio" | "outro";
export type Canal =
  | "incidente"
  | "escalada"
  | "urgencia"
  | "tecnico"
  | "comercial"
  | "padrao";

// ─────────────────────────────────────────────
// ESTADO (já definido — não precisa alterar)
// ─────────────────────────────────────────────

export const NotificacaoState = Annotation.Root({
  titulo: Annotation<string>,
  mensagem: Annotation<string>,
  urgencia: Annotation<Urgencia>,
  tipo: Annotation<TipoNotificacao>,
  canal: Annotation<Canal>,
  destinatarios: Annotation<string[]>,
  enviado: Annotation<boolean>,
  timestampEnvio: Annotation<string>,
});

export type Estado = typeof NotificacaoState.State;

// ─────────────────────────────────────────────
// NÓ CLASSIFICAR (já implementado)
// ─────────────────────────────────────────────

export function classificar(estado: Estado): Partial<Estado> {
  // Este nó apenas valida os dados — a classificação real vem do estado inicial
  console.log(`\n📋 [classificar] ${estado.urgencia.toUpperCase()} | ${estado.tipo}`);
  return {};
}

// ─────────────────────────────────────────────
// TODO 1: Implemente a função de roteamento
// ─────────────────────────────────────────────
//
// Recebe o estado e retorna o nome do canal como string.
// Use as combinações de urgencia + tipo descritas acima.
//

export function rotear(estado: Estado): Canal {
  // TODO: implemente o roteamento baseado em urgencia + tipo
  throw new Error("TODO: implemente a função rotear");
}

// ─────────────────────────────────────────────
// TODO 2: Implemente os handlers de canal
// ─────────────────────────────────────────────
//
// Cada handler deve:
//   - Definir o campo `canal` com o canal correspondente
//   - Definir `destinatarios` com uma lista de emails fictícios relevantes
//   - Definir `enviado` como true
//   - Definir `timestampEnvio` com new Date().toISOString()
//

export function handleIncidente(estado: Estado): Partial<Estado> {
  // TODO: canal "incidente" — alertar equipe de plantão + oncall
  throw new Error("TODO: implemente handleIncidente");
}

export function handleEscalada(estado: Estado): Partial<Estado> {
  // TODO: canal "escalada" — alertar diretoria + gerentes
  throw new Error("TODO: implemente handleEscalada");
}

export function handleUrgencia(estado: Estado): Partial<Estado> {
  // TODO: canal "urgencia" — alertar equipe geral de urgência
  throw new Error("TODO: implemente handleUrgencia");
}

export function handleTecnico(estado: Estado): Partial<Estado> {
  // TODO: canal "tecnico" — equipe técnica
  throw new Error("TODO: implemente handleTecnico");
}

export function handleComercial(estado: Estado): Partial<Estado> {
  // TODO: canal "comercial" — equipe comercial + CRM
  throw new Error("TODO: implemente handleComercial");
}

export function handlePadrao(estado: Estado): Partial<Estado> {
  // TODO: canal "padrao" — fila de notificações padrão
  throw new Error("TODO: implemente handlePadrao");
}

// ─────────────────────────────────────────────
// NÓ REGISTRAR (já implementado)
// ─────────────────────────────────────────────

export function registrarEnvio(estado: Estado): Partial<Estado> {
  console.log(`\n✅ [registrar] Canal: ${estado.canal} | Destinatários: ${estado.destinatarios?.length ?? 0}`);
  return {};
}

// ─────────────────────────────────────────────
// TODO 3: Monte o grafo
// ─────────────────────────────────────────────
//
// DICA: Use addConditionalEdges com um mapa que cobre todos os 6 canais.
// Todos os handlers devem convergir para "registrar_envio".
//

export function criarGrafo() {
  // TODO: monte e retorne o grafo compilado
  throw new Error("TODO: monte o grafo");
}
