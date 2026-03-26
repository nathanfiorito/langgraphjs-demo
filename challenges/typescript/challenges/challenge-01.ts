/**
 * DESAFIO 01 — CONSTRUA SEU PIPELINE
 * =====================================
 *
 * Conceitos testados: Módulos 01 e 02
 *   - Definição de estado com TypedDict / Annotation
 *   - Reducer de acumulação de lista
 *   - Reducer de merge de objeto
 *   - Construção e execução de um grafo com 3 nós
 *
 * CENÁRIO:
 * Você deve construir um pipeline de processamento de pedidos de e-commerce.
 * O pipeline recebe um pedido bruto e passa por 3 etapas:
 *
 *   1. validar: verifica se o pedido tem todos os campos obrigatórios
 *   2. calcular: calcula o total com desconto e frete
 *   3. formatar: gera o resumo final do pedido
 *
 * INSTRUÇÕES:
 *   1. Complete a definição do estado (PedidoState)
 *   2. Implemente as 3 funções de nó
 *   3. Monte o grafo conectando os nós
 *
 * Execute os testes com: npm test
 */

import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

// ─────────────────────────────────────────────
// TIPOS DE APOIO
// ─────────────────────────────────────────────

export interface ItemPedido {
  nome: string;
  quantidade: number;
  precoUnitario: number;
}

// ─────────────────────────────────────────────
// TODO 1: Defina o estado do pipeline
// ─────────────────────────────────────────────
//
// O estado deve ter os seguintes campos:
//
//   itens: ItemPedido[]           — itens do pedido (sem reducer, último vence)
//   codigoDesconto: string        — código de desconto aplicado (pode ser vazio)
//   subtotal: number              — soma de todos os itens
//   desconto: number              — valor do desconto em R$
//   frete: number                 — valor do frete em R$
//   total: number                 — subtotal - desconto + frete
//   valido: boolean               — se o pedido é válido
//   erros: string[]               — lista de erros de validação (ACUMULATIVA)
//   resumo: Record<string, unknown> — resumo final (MERGE — campo a campo)
//
// DICA: Use Annotation<T>({ reducer, default }) para os campos acumulativos.
//

export const PedidoState = Annotation.Root({
  // TODO: adicione os campos aqui
  // Exemplo:
  // meuCampo: Annotation<string>,
});

export type Estado = typeof PedidoState.State;

// ─────────────────────────────────────────────
// TODO 2: Implemente o nó "validar"
// ─────────────────────────────────────────────
//
// Este nó deve:
//   - Verificar se há pelo menos 1 item no pedido
//   - Verificar se todos os itens têm quantidade > 0 e precoUnitario > 0
//   - Definir `valido` como true/false
//   - Acumular mensagens de erro em `erros` (se houver)
//
// DICA: Retorne apenas os campos que você quer atualizar (Partial<Estado>)
//

export function validar(estado: Estado): Partial<Estado> {
  // TODO: implemente a validação
  throw new Error("TODO: implemente o nó validar");
}

// ─────────────────────────────────────────────
// TODO 3: Implemente o nó "calcular"
// ─────────────────────────────────────────────
//
// Este nó deve:
//   - Calcular o subtotal (soma de quantidade * precoUnitario de cada item)
//   - Aplicar desconto baseado no codigoDesconto:
//       "DESC10" → 10% de desconto
//       "DESC20" → 20% de desconto
//       qualquer outro → 0% de desconto
//   - Calcular o frete:
//       subtotal >= 200 → frete grátis (0)
//       subtotal < 200  → frete fixo de R$15
//   - Calcular o total: subtotal - desconto + frete
//   - Atualizar o campo resumo com: { subtotal, desconto, frete } (merge parcial)
//
// DICA: Se o pedido não for válido (estado.valido === false), retorne sem calcular.
//

export function calcular(estado: Estado): Partial<Estado> {
  // TODO: implemente os cálculos
  throw new Error("TODO: implemente o nó calcular");
}

// ─────────────────────────────────────────────
// TODO 4: Implemente o nó "formatar"
// ─────────────────────────────────────────────
//
// Este nó deve:
//   - Gerar um resumo final do pedido com todos os dados calculados
//   - Atualizar o campo resumo com: { total, totalItens, status }
//     onde totalItens é a soma das quantidades de todos os itens
//     e status é "aprovado" se válido, "rejeitado" se inválido
//
// DICA: Use merge no campo resumo para não perder os dados do nó anterior.
//

export function formatar(estado: Estado): Partial<Estado> {
  // TODO: implemente a formatação
  throw new Error("TODO: implemente o nó formatar");
}

// ─────────────────────────────────────────────
// TODO 5: Monte o grafo
// ─────────────────────────────────────────────
//
// O grafo deve ter o fluxo:
//   START → validar → calcular → formatar → END
//

export function criarGrafo() {
  // TODO: crie e retorne o grafo compilado
  throw new Error("TODO: monte o grafo");
}
