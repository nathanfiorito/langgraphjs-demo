"""
MÓDULO 01 — GRAFO BÁSICO
=========================

Conceito central do LangGraph: tudo é um grafo.

Um grafo é composto por:
  - NODES (nós): funções que recebem o estado atual e retornam um estado parcial
  - EDGES (arestas): conexões entre nós que definem o fluxo de execução
  - STATE (estado): um objeto compartilhado que trafega por todo o grafo

Neste módulo NÃO usamos LLM — o foco é entender a estrutura do grafo puro.

Fluxo deste exemplo:

  START → [receber_texto] → [processar_texto] → [formatar_resultado] → END

Diferenças em relação ao TypeScript:
  - Estado usa TypedDict + Annotated (em vez de Annotation.Root)
  - Reducers são funções Python simples (operator.add para listas)
  - Métodos do grafo são snake_case: add_node, add_edge (em vez de addNode, addEdge)
"""

import sys
import operator
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END

# Garante saída UTF-8 em terminais Windows (MSYS2, cmd, PowerShell)
sys.stdout.reconfigure(encoding="utf-8")


# ─────────────────────────────────────────────
# 1. DEFINIÇÃO DO ESTADO
# ─────────────────────────────────────────────
#
# Em Python, o estado é um TypedDict.
# Para campos com reducer customizado, usamos Annotated[tipo, função_reducer].
#
# Annotated[list[str], operator.add] significa:
#   - O tipo do campo é list[str]
#   - Quando um nó retorna um valor para este campo, ele é SOMADO ao existente
#     usando operator.add (equivalente a lista1 + lista2)
#
# Campos sem Annotated usam o comportamento padrão: último valor vence.
#

class PipelineState(TypedDict):
    texto_original: str                            # último valor vence
    texto_processado: str                          # último valor vence
    resultado: str                                 # último valor vence
    etapas: Annotated[list[str], operator.add]     # acumulação de lista


# ─────────────────────────────────────────────
# 2. DEFINIÇÃO DOS NÓS
# ─────────────────────────────────────────────
#
# Um nó é uma função com a assinatura:
#   (estado: dict) -> dict  (com apenas os campos que quer atualizar)
#
# O LangGraph se encarrega de mesclar as atualizações no estado global.
#

# Nó 1: Valida e registra o texto recebido
def receber_texto(estado: PipelineState) -> dict:
    print(f"\n📥 [receber_texto] Texto recebido: {estado['texto_original']}")

    return {
        "etapas": [f"Texto recebido com {len(estado['texto_original'])} caracteres"]
    }


# Nó 2: Aplica transformações no texto
def processar_texto(estado: PipelineState) -> dict:
    processado = (
        estado["texto_original"]
        .strip()
        .upper()
        .replace(" ", "_")          # substitui espaços por underscores
    )

    print(f"\n⚙️  [processar_texto] Texto processado: {processado}")

    return {
        "texto_processado": processado,
        "etapas": [f'Texto transformado: "{processado}"'],
    }


# Nó 3: Formata o resultado final
def formatar_resultado(estado: PipelineState) -> dict:
    resultado = f"[RESULTADO]: {estado['texto_processado']}"

    print(f"\n✅ [formatar_resultado] Resultado final: {resultado}")

    return {
        "resultado": resultado,
        "etapas": ["Resultado formatado com sucesso"],
    }


# ─────────────────────────────────────────────
# 3. CONSTRUÇÃO DO GRAFO
# ─────────────────────────────────────────────
#
# A API Python usa snake_case:
#   .add_node()  (em vez de .addNode())
#   .add_edge()  (em vez de .addEdge())
#   .compile()   (igual)
#

grafo = (
    StateGraph(PipelineState)
    .add_node("receber_texto", receber_texto)
    .add_node("processar_texto", processar_texto)
    .add_node("formatar_resultado", formatar_resultado)
    .add_edge(START, "receber_texto")
    .add_edge("receber_texto", "processar_texto")
    .add_edge("processar_texto", "formatar_resultado")
    .add_edge("formatar_resultado", END)
    .compile()
)


# ─────────────────────────────────────────────
# 4. EXECUÇÃO
# ─────────────────────────────────────────────

def main():
    print("═══════════════════════════════════════")
    print("  MÓDULO 01 — GRAFO BÁSICO (Python)")
    print("═══════════════════════════════════════")

    # Estado inicial: apenas os campos necessários para iniciar
    # Campos com Annotated[list, operator.add] começam como []
    estado_final = grafo.invoke({
        "texto_original": "hello world langgraph",
        "etapas": [],
    })

    print("\n─────────────────────────────────────")
    print("📊 ESTADO FINAL COMPLETO:")
    print("─────────────────────────────────────")
    print(f"Texto original:  {estado_final['texto_original']}")
    print(f"Texto processado: {estado_final['texto_processado']}")
    print(f"Resultado:        {estado_final['resultado']}")
    print("\nEtapas executadas:")
    for i, etapa in enumerate(estado_final["etapas"], 1):
        print(f"  {i}. {etapa}")


if __name__ == "__main__":
    main()
