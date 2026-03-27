"""
DESAFIO 01 — CONSTRUA SEU PIPELINE
=====================================

Conceitos testados: Módulos 01 e 02
  - Definição de estado com TypedDict + Annotated
  - Reducer de acumulação de lista (operator.add)
  - Reducer de merge de dict (função customizada)
  - Construção e execução de um grafo com 3 nós

CENÁRIO:
Você deve construir um pipeline de processamento de pedidos de e-commerce.
O pipeline recebe um pedido bruto e passa por 3 etapas:

  1. validar: verifica se o pedido tem todos os campos obrigatórios
  2. calcular: calcula o total com desconto e frete
  3. formatar: gera o resumo final do pedido

INSTRUÇÕES:
  1. Complete a definição do estado (PedidoState)
  2. Implemente as 3 funções de nó
  3. Monte o grafo conectando os nós

Execute os testes com: pytest tests/
"""

import operator
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END


# ─────────────────────────────────────────────
# TIPOS DE APOIO
# ─────────────────────────────────────────────

class ItemPedido(TypedDict):
    nome: str
    quantidade: int
    preco_unitario: float


# ─────────────────────────────────────────────
# TODO 1: Defina o estado do pipeline
# ─────────────────────────────────────────────
#
# O estado deve ter os seguintes campos:
#
#   itens: list[ItemPedido]         — itens do pedido (sem reducer, último vence)
#   codigo_desconto: str            — código de desconto aplicado (pode ser vazio)
#   subtotal: float                 — soma de todos os itens
#   desconto: float                 — valor do desconto em R$
#   frete: float                    — valor do frete em R$
#   total: float                    — subtotal - desconto + frete
#   valido: bool                    — se o pedido é válido
#   erros: list[str]                — lista de erros (ACUMULATIVA — use operator.add)
#   resumo: dict                    — resumo final (MERGE — use função merge_dict)
#
# DICA: Use Annotated[tipo, reducer] para os campos acumulativos.
#

def merge_dict(atual: dict, novo: dict) -> dict:
    """Mescla dois dicionários."""
    return {**atual, **novo}


class PedidoState(TypedDict):
    itens: Annotated[list[ItemPedido], operator.add]
    codigo_desconto: str
    subtotal: float
    desconto: float
    frete: float
    total: float
    valido: bool
    erros: Annotated[list[str], operator.add]
    resumo: Annotated[dict, merge_dict]


# ─────────────────────────────────────────────
# TODO 2: Implemente o nó "validar"
# ─────────────────────────────────────────────
#
# Este nó deve:
#   - Verificar se há pelo menos 1 item no pedido
#   - Verificar se todos os itens têm quantidade > 0 e preco_unitario > 0
#   - Definir `valido` como True/False
#   - Acumular mensagens de erro em `erros` (se houver)
#

def validar(estado: PedidoState) -> dict:
    # TODO: implemente a validação
    erros = []

    print("Validando pedido.")

    if not estado["itens"] or len(estado["itens"]) < 1:
        print("Não existe nenhum Item presente no Pedido.")
        erros.append("Não existe nenhum Item presente no Pedido.")
    
    for item in estado["itens"]:
        if(item["quantidade"] < 1 or item["preco_unitario"] < 1):
            print("Quantidade ou Preço Unitário inválido.")
            erros.append("Quantidade ou Preço Unitário inválido.")

    print("Validação concluída.")

    return {
        "valido": False if len(erros) > 0 else True,
        "erros": erros
    }



# ─────────────────────────────────────────────
# TODO 3: Implemente o nó "calcular"
# ─────────────────────────────────────────────
#
# Este nó deve:
#   - Calcular o subtotal (soma de quantidade * preco_unitario de cada item)
#   - Aplicar desconto baseado no codigo_desconto:
#       "DESC10" → 10% de desconto
#       "DESC20" → 20% de desconto
#       qualquer outro → 0% de desconto
#   - Calcular o frete:
#       subtotal >= 200 → frete grátis (0)
#       subtotal < 200  → frete fixo de R$15
#   - Calcular o total: subtotal - desconto + frete
#   - Atualizar o campo resumo com: { subtotal, desconto, frete } (merge parcial)
#
# DICA: Se o pedido não for válido (estado["valido"] == False), retorne sem calcular.
#

def calcular(estado: PedidoState) -> dict:
    # TODO: implemente os cálculos
    subtotal = 0
    desconto = 0
    frete = 0

    print("Calculando subtotal.")

    for item in estado["itens"]:
        subtotal += item["quantidade"] * item["preco_unitario"]

    print("Calculando desconto.")

    if(estado["codigo_desconto"] == "DESC10"):
        desconto = subtotal * 0.1
    elif(estado["codigo_desconto"] == "DESC20"):
        desconto = subtotal * 0.2
        
    print("Calculando frete.")
    
    if subtotal < 200:
        frete = 15

    print("Calculo concluído.")

    return {
        "subtotal": subtotal,
        "frete": frete,
        "desconto": desconto
    }

# ─────────────────────────────────────────────
# TODO 4: Implemente o nó "formatar"
# ─────────────────────────────────────────────
#
# Este nó deve:
#   - Gerar um resumo final do pedido com todos os dados calculados
#   - Atualizar o campo resumo com: { total, total_itens, status }
#     onde total_itens é a soma das quantidades de todos os itens
#     e status é "aprovado" se válido, "rejeitado" se inválido
#

def formatar(estado: PedidoState) -> dict:
    # TODO: implemente a formatação
    total = 0
    total_itens = 0
    status = "aprovado"

    print("Formatando resultado final.")

    for item in estado["itens"]:
        total_itens += item["quantidade"]

    print("Calculando total.")

    total = estado["subtotal"] - estado["desconto"] + estado["frete"]

    if not estado["valido"]:
        status = "rejeitado"

    print("Formatação concluida.")

    return {
        "total": total,
        "resumo": {
            "status":status, 
            "total_itens": total_itens,
            "subtotal": estado["subtotal"],
            "desconto": estado["desconto"],
            "frete": estado["frete"],
            "total": total
            }
    }


# ─────────────────────────────────────────────
# TODO 5: Monte o grafo
# ─────────────────────────────────────────────
#
# O grafo deve ter o fluxo:
#   START → validar → calcular → formatar → END
#

def criar_grafo():
    return (
        StateGraph(PedidoState)
        .add_node("validar", validar)
        .add_node("calcular", calcular)
        .add_node("formatar", formatar)

        .add_edge(START, "validar")
        .add_edge("validar", "calcular")
        .add_edge("calcular", "formatar")
        .add_edge("formatar", END)
        .compile()
             )
