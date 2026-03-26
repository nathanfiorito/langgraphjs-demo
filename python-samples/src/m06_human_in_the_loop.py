"""
MÓDULO 06 — HUMAN-IN-THE-LOOP
================================

Em muitos cenários, o agente precisa de aprovação humana antes de agir.
O LangGraph permite PAUSAR a execução, aguardar input humano e CONTINUAR.

Conceitos fundamentais:

  CHECKPOINTER: persiste o estado do grafo entre execuções
    - MemorySaver: salva em memória (ideal para demos e testes)
    - Em produção: SqliteSaver, PostgresSaver, etc.

  interrupt(): pausa o grafo e retorna controle ao chamador

  Command(resume=valor): retoma o grafo com a resposta humana
    - Equivale ao Command({ resume: value }) do TypeScript

  thread_id: identifica uma "conversa" específica no checkpointer

Fluxo:

  INVOCAÇÃO 1:
    START → [rascunhar_email] → [aguardar_aprovacao] ← PAUSA AQUI

  INVOCAÇÃO 2 (após decisão humana):
    [aguardar_aprovacao] → [enviar_email] → END
                        → [rascunhar_email] → [aguardar_aprovacao] ← PAUSA DE NOVO
                        → [cancelar] → END

Diferenças em relação ao TypeScript:
  - Command(resume=valor) em vez de new Command({ resume: value })
  - MemorySaver de langgraph.checkpoint.memory
  - input() em vez de readline para capturar input do terminal
  - get_state() em vez de getState()
  - asyncio.run() para main assíncrono
"""

import sys
import asyncio
from pathlib import Path
from typing import TypedDict, Literal

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")


# ─────────────────────────────────────────────
# 1. ESTADO
# ─────────────────────────────────────────────

class EmailState(TypedDict):
    solicitacao: str
    destinatario: str
    rascunho: str
    feedback_humano: str
    numero_revisoes: int
    status: Literal["aguardando", "aprovado", "enviado", "cancelado"]


# ─────────────────────────────────────────────
# 2. LLM
# ─────────────────────────────────────────────

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.7)


# ─────────────────────────────────────────────
# 3. NÓS
# ─────────────────────────────────────────────

async def rascunhar_email(estado: EmailState) -> dict:
    eh_revisao = estado.get("numero_revisoes", 0) > 0
    tentativa = estado.get("numero_revisoes", 0) + 1
    print(
        f"\n✏️  [rascunhar_email] {'Revisando' if eh_revisao else 'Gerando rascunho inicial'} "
        f"(tentativa {tentativa})..."
    )

    if eh_revisao:
        prompt = (
            f"Você escreveu o seguinte rascunho de email:\n\n{estado['rascunho']}\n\n"
            f"O revisor pediu as seguintes alterações:\n{estado['feedback_humano']}\n\n"
            "Reescreva o email incorporando o feedback."
        )
    else:
        prompt = (
            f"Escreva um email profissional para {estado['destinatario']} "
            f"sobre: {estado['solicitacao']}"
        )

    resposta = await llm.ainvoke([
        SystemMessage(content=(
            "Você é um redator profissional especializado em comunicação corporativa. "
            "Escreva emails claros, objetivos e com tom adequado ao contexto. "
            "Inclua assunto (Subject:), corpo e assinatura."
        )),
        HumanMessage(content=prompt),
    ])

    print("   ✓ Rascunho gerado")
    return {
        "rascunho": resposta.content,
        "status": "aguardando",
    }


async def aguardar_aprovacao(estado: EmailState) -> dict:
    print("\n" + "─" * 60)
    print("⏸️  [aguardar_aprovacao] AGUARDANDO REVISÃO HUMANA")
    print("─" * 60)
    print(f"\n📧 RASCUNHO DO EMAIL (revisão {estado.get('numero_revisoes', 0) + 1}):")
    print("─" * 60)
    print(estado["rascunho"])
    print("─" * 60)

    # ── interrupt() ──────────────────────────────────────────────────
    # Pausa o grafo aqui e retorna o controle ao chamador.
    # A string passada fica disponível via graph.get_state().
    # Quando retomado com Command(resume=valor), essa variável recebe o valor.
    decisao_humana = interrupt(
        "Revise o email acima e responda:\n"
        "  • 'aprovado' — para enviar o email\n"
        "  • 'cancelado' — para cancelar\n"
        "  • Qualquer outro texto — para solicitar alterações\n"
    )

    print(f'\n👤 Decisão humana recebida: "{decisao_humana}"')

    if decisao_humana == "aprovado":
        return {"status": "aprovado", "feedback_humano": ""}
    elif decisao_humana == "cancelado":
        return {"status": "cancelado"}
    else:
        return {
            "status": "aguardando",
            "feedback_humano": decisao_humana,
            "numero_revisoes": estado.get("numero_revisoes", 0) + 1,
        }


def enviar_email(estado: EmailState) -> dict:
    print("\n📤 [enviar_email] Enviando email...")
    print(f"   Para: {estado['destinatario']}")
    print("   ✓ Email enviado com sucesso!")
    return {"status": "enviado"}


def cancelar(estado: EmailState) -> dict:
    print("\n❌ [cancelar] Processo cancelado pelo usuário.")
    return {"status": "cancelado"}


# ─────────────────────────────────────────────
# 4. FUNÇÃO DE ROTEAMENTO
# ─────────────────────────────────────────────

def apos_aprovacao(estado: EmailState) -> str:
    if estado["status"] == "aprovado":
        return "enviar_email"
    if estado["status"] == "cancelado":
        return "cancelar"
    return "rascunhar_email"  # precisa de revisão


# ─────────────────────────────────────────────
# 5. GRAFO COM CHECKPOINTER
# ─────────────────────────────────────────────
#
# O checkpointer é passado para .compile().
# MemorySaver persiste o estado em memória — ideal para demos.
#

checkpointer = MemorySaver()

grafo = (
    StateGraph(EmailState)
    .add_node("rascunhar_email", rascunhar_email)
    .add_node("aguardar_aprovacao", aguardar_aprovacao)
    .add_node("enviar_email", enviar_email)
    .add_node("cancelar", cancelar)
    .add_edge(START, "rascunhar_email")
    .add_edge("rascunhar_email", "aguardar_aprovacao")
    .add_conditional_edges("aguardar_aprovacao", apos_aprovacao, {
        "enviar_email": "enviar_email",
        "rascunhar_email": "rascunhar_email",
        "cancelar": "cancelar",
    })
    .add_edge("enviar_email", END)
    .add_edge("cancelar", END)
    .compile(checkpointer=checkpointer)
)


# ─────────────────────────────────────────────
# 6. EXECUÇÃO COM LOOP HUMAN-IN-THE-LOOP
# ─────────────────────────────────────────────

async def main():
    print("═══════════════════════════════════════════════════════════")
    print("  MÓDULO 06 — HUMAN-IN-THE-LOOP (Python)")
    print("═══════════════════════════════════════════════════════════")

    # thread_id identifica esta "sessão" no checkpointer
    thread_config = {"configurable": {"thread_id": "email-session-001"}}

    # ── FASE 1: Execução inicial ───────────────────────────────────────
    print("\n▶️  FASE 1: Gerando rascunho...")

    await grafo.ainvoke(
        {
            "solicitacao": "Solicitar reunião para apresentar os resultados do Q1",
            "destinatario": "Diretoria Executiva",
            "numero_revisoes": 0,
            "status": "aguardando",
        },
        thread_config,
    )

    # Verifica se o grafo foi interrompido
    estado_grafo = grafo.get_state(thread_config)
    if not estado_grafo.next:
        print("\n✅ Grafo concluído sem interrupção.")
        return

    print(f"\n⏸️  Grafo pausado em: {list(estado_grafo.next)}")

    # ── FASE 2: Loop de revisão humana ────────────────────────────────
    continuar = True
    while continuar:
        # Captura input real do usuário
        decisao = input(
            "\n👤 Sua decisão (aprovado / cancelado / ou feedback de revisão): "
        ).strip()

        print("\n▶️  Retomando grafo com decisão humana...")

        # Command(resume=valor) retoma o grafo
        # O valor é retornado por interrupt() no nó aguardar_aprovacao
        resultado = await grafo.ainvoke(
            Command(resume=decisao),
            thread_config,
        )

        estado_atual = grafo.get_state(thread_config)

        if not estado_atual.next:
            print("\n" + "═" * 60)
            print("🏁 PROCESSO FINALIZADO")
            print(f"   Status final: {resultado['status']}")
            continuar = False
        else:
            print(f"\n⏸️  Grafo pausado novamente em: {list(estado_atual.next)}")


if __name__ == "__main__":
    asyncio.run(main())
