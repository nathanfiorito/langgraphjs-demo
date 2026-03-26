"""
DESAFIO 04 — ORQUESTRADOR COM GUARDRAILS
==========================================

Conceitos testados: Módulos 05 e 06
  - Padrão supervisor com agentes especializados
  - Guardrails determinísticos na função de roteamento
  - Checkpointer (MemorySaver) para persistência de estado
  - Inspeção de estado com get_state()

CENÁRIO:
Implemente um supervisor que orquestra um pipeline de publicação de artigos.
O pipeline tem 3 agentes especializados com sequência OBRIGATÓRIA:

  1. "revisor"    — revisa o conteúdo do artigo
  2. "formatador" — formata o artigo revisado
  3. "publicador" — publica o artigo formatado

REGRAS DO GUARDRAIL (implemente em rotear_supervisor):

  - Se `revisao` estiver vazia → SEMPRE ir para "revisor"
  - Se `revisao` preenchida e `formatacao` vazia → SEMPRE ir para "formatador"
  - Se ambas preenchidas → ir para "publicador"
  - NUNCA ir para "publicador" se `formatacao` estiver vazia

🎯 BÔNUS (opcional, requer ANTHROPIC_API_KEY):
Substitua o supervisor mock pelo Claude real usando with_structured_output:
  from langchain_anthropic import ChatAnthropic
  from pydantic import BaseModel
  from typing import Literal

  class Decisao(BaseModel):
      proximo: Literal["revisor", "formatador", "publicador"]

  llm = ChatAnthropic(model="claude-haiku-4-5-20251001")
  supervisor_real = llm.with_structured_output(Decisao)

INSTRUÇÕES:
  1. Implemente rotear_supervisor() com os guardrails
  2. Implemente os 3 agentes especializados
  3. Monte o grafo com MemorySaver
"""

import operator
from typing import TypedDict, Annotated, Literal, Protocol

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


# ─────────────────────────────────────────────
# TIPOS
# ─────────────────────────────────────────────

ProximoAgente = Literal["revisor", "formatador", "publicador"]


# ─────────────────────────────────────────────
# ESTADO (já definido)
# ─────────────────────────────────────────────

class PublicacaoState(TypedDict):
    conteudo_original: str
    proximo_agente: ProximoAgente
    revisao: str
    formatacao: str
    publicado: bool
    url_publicacao: str
    historico: Annotated[list[str], operator.add]


# ─────────────────────────────────────────────
# INTERFACE DO SUPERVISOR
# ─────────────────────────────────────────────

class SupervisorInterface(Protocol):
    async def decidir(self, estado: PublicacaoState) -> dict:
        """Retorna dict com 'proximo' e 'motivo'."""
        ...


# ─────────────────────────────────────────────
# NÓ SUPERVISOR (já implementado)
# ─────────────────────────────────────────────

def criar_no_supervisor(supervisor: SupervisorInterface):
    async def supervisor_no(estado: PublicacaoState) -> dict:
        print("\n🎯 [supervisor] Avaliando...")
        decisao = await supervisor.decidir(estado)
        print(f"   Decisão: {decisao['proximo']} — {decisao['motivo']}")
        return {
            "proximo_agente": decisao["proximo"],
            "historico": [f"supervisor → {decisao['proximo']}: {decisao['motivo']}"],
        }
    return supervisor_no


# ─────────────────────────────────────────────
# TODO 1: Implemente a função de roteamento COM GUARDRAILS
# ─────────────────────────────────────────────
#
# Aplique as regras descritas no topo do arquivo.
# Se o supervisor tomou uma decisão errada, corrija-a e imprima um aviso.
#

def rotear_supervisor(estado: PublicacaoState) -> str:
    # TODO: implemente com guardrails
    raise NotImplementedError("TODO: implemente rotear_supervisor com guardrails")


# ─────────────────────────────────────────────
# TODO 2: Implemente os 3 agentes especializados
# ─────────────────────────────────────────────

def revisor(estado: PublicacaoState) -> dict:
    # TODO: deve preencher `revisao` com versão revisada do conteudo_original
    # e adicionar uma entrada no historico
    raise NotImplementedError("TODO: implemente o revisor")


def formatador(estado: PublicacaoState) -> dict:
    # TODO: deve preencher `formatacao` com o conteúdo da revisao formatado
    # e adicionar uma entrada no historico
    # DICA: Adicione markdown, ex: "## Título\n\n" + revisao
    raise NotImplementedError("TODO: implemente o formatador")


def publicador(estado: PublicacaoState) -> dict:
    # TODO: deve setar publicado=True, gerar uma url_publicacao fictícia
    # e adicionar uma entrada no historico
    raise NotImplementedError("TODO: implemente o publicador")


# ─────────────────────────────────────────────
# TODO 3: Monte o grafo com checkpointer
# ─────────────────────────────────────────────

def criar_grafo(supervisor: SupervisorInterface):
    checkpointer = MemorySaver()
    # TODO: monte e retorne o grafo compilado com checkpointer
    raise NotImplementedError("TODO: monte o grafo")
