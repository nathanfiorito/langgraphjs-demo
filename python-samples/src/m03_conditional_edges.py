"""
MÓDULO 03 — CONDITIONAL EDGES (ROTEAMENTO DINÂMICO)
=====================================================

Conditional Edges permitem que o fluxo se ramifique com base no estado.

Como funciona:
  - add_conditional_edges(nó_origem, função_roteamento, mapa_destinos)
  - A função de roteamento recebe o estado e retorna uma string (chave)
  - O mapa associa cada chave ao nó de destino

Cenário: Um sistema de triagem de suporte ao cliente.

                   ┌──────────────────┐
                   │    [triagem]     │
                   └────────┬─────────┘
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
        [urgente]     [tecnico]       [geral]
             │              │              │
             └──────────────┴──────────────┘
                            │
                     [registrar]
                            │
                           END
"""

import sys
import operator
from typing import TypedDict, Annotated, Literal

from langgraph.graph import StateGraph, START, END

sys.stdout.reconfigure(encoding="utf-8")


# ─────────────────────────────────────────────
# TIPOS
# ─────────────────────────────────────────────

TipoSolicitacao = Literal["urgente", "tecnico", "geral"]
Prioridade = Literal["alta", "media", "baixa"]


# ─────────────────────────────────────────────
# ESTADO
# ─────────────────────────────────────────────

class SuporteState(TypedDict):
    mensagem: str
    tipo: TipoSolicitacao
    prioridade: Prioridade
    fila_destino: str
    tempo_resposta_estimado: str
    acoes: Annotated[list[str], operator.add]


# ─────────────────────────────────────────────
# NÓS
# ─────────────────────────────────────────────

def triagem(estado: SuporteState) -> dict:
    print("\n🔎 [triagem] Analisando mensagem...")
    print(f'   Mensagem: "{estado["mensagem"]}"')

    msg = estado["mensagem"].lower()

    tipo: TipoSolicitacao = "geral"
    prioridade: Prioridade = "baixa"

    if any(p in msg for p in ["urgente", "sistema caiu", "fora do ar"]):
        tipo = "urgente"
        prioridade = "alta"
    elif any(p in msg for p in ["bug", "erro", "falha", "api"]):
        tipo = "tecnico"
        prioridade = "media"

    print(f"   Classificado como: tipo={tipo}, prioridade={prioridade}")

    return {
        "tipo": tipo,
        "prioridade": prioridade,
        "acoes": [f"Triagem concluída: {tipo} (prioridade {prioridade})"],
    }


# ─────────────────────────────────────────────
# FUNÇÃO DE ROTEAMENTO
# ─────────────────────────────────────────────
#
# Recebe o estado e retorna uma STRING que indica qual caminho seguir.
# O retorno deve corresponder às chaves do mapa em add_conditional_edges.
#

def rotear(estado: SuporteState) -> TipoSolicitacao:
    print(f"\n🔀 [router] Roteando para: {estado['tipo']}")
    return estado["tipo"]


# ─────────────────────────────────────────────
# NÓS DE TRATAMENTO
# ─────────────────────────────────────────────

def tratar_urgente(estado: SuporteState) -> dict:
    print("\n🚨 [tratar_urgente] Escalando para equipe de plantão...")
    return {
        "fila_destino": "PLANTÃO_24H",
        "tempo_resposta_estimado": "15 minutos",
        "acoes": [
            "Alerta enviado para equipe de plantão",
            "SLA de emergência ativado",
            "Notificação para gerente de plantão",
        ],
    }


def tratar_tecnico(estado: SuporteState) -> dict:
    print("\n🔧 [tratar_tecnico] Encaminhando para time técnico...")
    return {
        "fila_destino": "SUPORTE_TECNICO",
        "tempo_resposta_estimado": "2 horas",
        "acoes": [
            "Ticket técnico criado",
            "Logs do sistema coletados",
            "Engenheiro de plantão notificado",
        ],
    }


def tratar_geral(estado: SuporteState) -> dict:
    print("\n💬 [tratar_geral] Encaminhando para suporte padrão...")
    return {
        "fila_destino": "SUPORTE_GERAL",
        "tempo_resposta_estimado": "24 horas",
        "acoes": [
            "Ticket padrão criado",
            "Email de confirmação enviado ao cliente",
        ],
    }


def registrar(estado: SuporteState) -> dict:
    print("\n📋 [registrar] Registrando atendimento...")
    return {
        "acoes": [
            f"Atendimento registrado na fila: {estado['fila_destino']}",
            f"Tempo de resposta estimado: {estado['tempo_resposta_estimado']}",
        ],
    }


# ─────────────────────────────────────────────
# GRAFO
# ─────────────────────────────────────────────

grafo = (
    StateGraph(SuporteState)
    .add_node("triagem", triagem)
    .add_node("tratar_urgente", tratar_urgente)
    .add_node("tratar_tecnico", tratar_tecnico)
    .add_node("tratar_geral", tratar_geral)
    .add_node("registrar", registrar)

    .add_edge(START, "triagem")

    # ── CONDITIONAL EDGE ────────────────────────────────────────────────
    # Após "triagem", a função `rotear` decide o próximo nó.
    # O terceiro argumento é um mapa: { chave_retornada: nó_destino }
    .add_conditional_edges("triagem", rotear, {
        "urgente": "tratar_urgente",
        "tecnico": "tratar_tecnico",
        "geral": "tratar_geral",
    })

    # Todos os caminhos convergem para "registrar"
    .add_edge("tratar_urgente", "registrar")
    .add_edge("tratar_tecnico", "registrar")
    .add_edge("tratar_geral", "registrar")
    .add_edge("registrar", END)
    .compile()
)


# ─────────────────────────────────────────────
# EXECUÇÃO — testamos 3 cenários diferentes
# ─────────────────────────────────────────────

def testar(mensagem: str) -> None:
    print("\n" + "═" * 55)
    resultado = grafo.invoke({
        "mensagem": mensagem,
        "acoes": [],
    })

    print("\n─────────────────────────────────────")
    print("📊 RESULTADO:")
    print(f"  Fila:      {resultado['fila_destino']}")
    print(f"  SLA:       {resultado['tempo_resposta_estimado']}")
    print("\n  Ações realizadas:")
    for acao in resultado["acoes"]:
        print(f"    • {acao}")


def main():
    print("═══════════════════════════════════════════════════════")
    print("  MÓDULO 03 — CONDITIONAL EDGES (Python)")
    print("═══════════════════════════════════════════════════════")

    testar("URGENTE: sistema caiu em produção!")
    testar("Encontrei um bug na API de pagamentos, retorna erro 500")
    testar("Gostaria de saber como alterar meus dados cadastrais")


if __name__ == "__main__":
    main()
