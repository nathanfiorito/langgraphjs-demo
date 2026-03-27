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

COMO OS MOCKS FUNCIONAM:

  Os testes injetam diferentes implementações de SupervisorInterface para
  verificar tanto o fluxo correto quanto a robustez do guardrail:

  ┌─ SupervisorCorreto ─────────────────────────────────────────────────────┐
  │  Toma decisões na ordem certa: revisor → formatador → publicador        │
  │  Verifica que o pipeline completo funciona normalmente                  │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌─ SupervisorMalicioso ───────────────────────────────────────────────────┐
  │  Sempre retorna "publicador" — tenta pular todas as etapas              │
  │  Verifica que o guardrail CORRIGE a decisão errada                      │
  └──────────────────────────────────────────────────────────────────────────┘

  O ponto-chave: o guardrail em rotear_supervisor() é DETERMINÍSTICO.
  Ele sempre prevalece sobre o que o supervisor (mock ou real) decidiu.
  Assim, mesmo um LLM real que "alucine" uma ordem errada será corrigido.

🎯 BÔNUS (opcional, requer ANTHROPIC_API_KEY):

  O with_structured_output() faz o Claude retornar JSON validado pelo schema
  Pydantic — mas ele não tem o método .decidir() da SupervisorInterface.
  Por isso, criamos um wrapper fino que adapta a interface.

  Veja o exemplo completo no bloco comentado ao final do arquivo.

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


# ─────────────────────────────────────────────
# 🎯 BÔNUS: Substituir o mock pelo Claude real
# ─────────────────────────────────────────────
#
# Depois de passar nos testes, você pode trocar o supervisor mock pelo Claude.
#
# O with_structured_output() garante que o LLM retorne JSON no formato certo,
# mas o retorno é um objeto Pydantic — não tem o método .decidir().
# Por isso criamos um wrapper (SupervisorReal) que adapta a interface.
#
# Passos:
#   1. Copie o bloco abaixo para um arquivo separado (ex: run_bonus_04.py)
#   2. Certifique-se de ter ANTHROPIC_API_KEY no arquivo .env na raiz do repo
#   3. Execute: python run_bonus_04.py
#
# import asyncio
# from pathlib import Path
# from dotenv import load_dotenv
# from typing import Literal
# from pydantic import BaseModel
# from langchain_anthropic import ChatAnthropic
# from challenges.challenge_04 import criar_grafo, PublicacaoState
#
# load_dotenv(dotenv_path=Path(__file__).parents[0] / ".env")
#
# class Decisao(BaseModel):
#     proximo: Literal["revisor", "formatador", "publicador"]
#     motivo: str
#
# # Wrapper que adapta o LLM estruturado à SupervisorInterface
# class SupervisorReal:
#     def __init__(self):
#         llm = ChatAnthropic(model="claude-haiku-4-5-20251001")
#         # with_structured_output garante saída no formato de Decisao
#         self._chain = llm.with_structured_output(Decisao)
#
#     async def decidir(self, estado: PublicacaoState) -> dict:
#         prompt = f"""
#         Você é um supervisor de publicação. Decida o próximo passo.
#         Estado: revisao="{estado.get('revisao', '')}", formatacao="{estado.get('formatacao', '')}"
#         Escolha: revisor, formatador ou publicador.
#         """
#         decisao = await self._chain.ainvoke(prompt)
#         return {"proximo": decisao.proximo, "motivo": decisao.motivo}
#
# # Mesma função criar_grafo dos testes — só o argumento muda
# grafo_real = criar_grafo(SupervisorReal())
#
# async def main():
#     config = {"configurable": {"thread_id": "bonus-01"}}
#     resultado = await grafo_real.ainvoke(
#         {"conteudo_original": "Artigo sobre LangGraph e guardrails", "historico": []},
#         config,
#     )
#     print("Publicado:", resultado["publicado"])
#     print("URL:", resultado["url_publicacao"])
#     print("Histórico:", resultado["historico"])
#
# if __name__ == "__main__":
#     asyncio.run(main())
