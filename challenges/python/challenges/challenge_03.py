"""
DESAFIO 03 — CICLO REACT MANUAL
=================================

Conceitos testados: Módulo 04
  - Loop ReAct (agente ↔ ferramentas)
  - Estado com BaseMessage[] e add_messages
  - add_conditional_edges para controlar o loop
  - ToolNode para executar ferramentas

CENÁRIO:
Implemente um agente ReAct que resolve problemas matemáticos usando
ferramentas. O agente deve:
  1. Receber uma pergunta matemática
  2. Decidir qual ferramenta usar (ou responder diretamente)
  3. Executar a ferramenta
  4. Usar o resultado para responder

FERRAMENTAS DISPONÍVEIS (já implementadas):
  - somar(a, b)           → retorna a + b
  - multiplicar(a, b)     → retorna a * b
  - potencia(base, exp)   → retorna base ** exp

FLUXO DO GRAFO (ReAct):

  START → [agente] ──(tem tool_calls?)──→ SIM → [executar_tools] ──┐
              ↑                                                       │
              └───────────────────────────────────────────────────────┘
              │
          NÃO → END

TESTES:
Os testes usam um LLM MOCKADO que simula respostas predefinidas.
Você não precisa de ANTHROPIC_API_KEY para rodar os testes.

🎯 BÔNUS (opcional, requer ANTHROPIC_API_KEY):
Depois de passar nos testes, substitua o mock pelo Claude real:
  from langchain_anthropic import ChatAnthropic
  modelo_real = ChatAnthropic(model="claude-haiku-4-5-20251001").bind_tools(ferramentas)

INSTRUÇÕES:
  1. Implemente o nó "agente" que chama o LLM
  2. Implemente a função verificar_proximo_passo
  3. Monte o grafo com o loop ReAct
"""

from typing import TypedDict, Annotated, Protocol

from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


# ─────────────────────────────────────────────
# FERRAMENTAS (já implementadas)
# ─────────────────────────────────────────────

@tool
def somar(a: float, b: float) -> str:
    """Soma dois números.

    Args:
        a: Primeiro número
        b: Segundo número
    """
    return str(a + b)


@tool
def multiplicar(a: float, b: float) -> str:
    """Multiplica dois números.

    Args:
        a: Primeiro número
        b: Segundo número
    """
    return str(a * b)


@tool
def potencia(base: float, exp: float) -> str:
    """Calcula base elevado ao expoente.

    Args:
        base: Base da potência
        exp: Expoente
    """
    return str(base ** exp)


ferramentas = [somar, multiplicar, potencia]


# ─────────────────────────────────────────────
# ESTADO
# ─────────────────────────────────────────────
#
# Use add_messages como reducer para o campo messages.
# Isso garante acumulação correta de mensagens.
#

class AgenteState(TypedDict):
    pass  # TODO: adicione o campo messages com add_messages como reducer


# ─────────────────────────────────────────────
# INTERFACE DO LLM (para injeção do mock nos testes)
# ─────────────────────────────────────────────

class LLMInterface(Protocol):
    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        ...


# ─────────────────────────────────────────────
# TODO 1: Implemente o nó "agente"
# ─────────────────────────────────────────────
#
# O nó deve:
#   - Chamar llm.ainvoke(estado["messages"])
#   - Retornar a resposta como { "messages": [resposta] }
#
# O parâmetro `llm` é injetado para permitir usar mock nos testes.
#

def criar_no_agente(llm: LLMInterface):
    async def agente(estado: AgenteState) -> dict:
        # TODO: implemente o nó agente
        raise NotImplementedError("TODO: implemente o nó agente")
    return agente


# ─────────────────────────────────────────────
# TODO 2: Implemente a função de roteamento
# ─────────────────────────────────────────────
#
# Verifica se a última mensagem tem tool_calls:
#   - Se sim → retorna "executar_tools"
#   - Se não → retorna END
#

def verificar_proximo_passo(estado: AgenteState) -> str:
    # TODO: implemente a verificação de tool_calls
    raise NotImplementedError("TODO: implemente verificar_proximo_passo")


# ─────────────────────────────────────────────
# TODO 3: Monte o grafo
# ─────────────────────────────────────────────
#
# O LLM é injetado para permitir usar mock nos testes.
#

def criar_grafo(llm: LLMInterface):
    # TODO: monte e retorne o grafo compilado com o loop ReAct
    raise NotImplementedError("TODO: monte o grafo")


# ─────────────────────────────────────────────
# 🎯 BÔNUS: Use com Claude real (requer ANTHROPIC_API_KEY)
# ─────────────────────────────────────────────
#
# import asyncio
# from pathlib import Path
# from dotenv import load_dotenv
# from langchain_anthropic import ChatAnthropic
# from langchain_core.messages import HumanMessage
#
# load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")
#
# modelo_real = ChatAnthropic(
#     model="claude-haiku-4-5-20251001", temperature=0
# ).bind_tools(ferramentas)
#
# grafo_real = criar_grafo(modelo_real)
#
# async def main():
#     resultado = await grafo_real.ainvoke({
#         "messages": [HumanMessage(content="Quanto é (3 + 4) elevado ao quadrado?")]
#     })
#     print(resultado["messages"][-1].content)
#
# if __name__ == "__main__":
#     asyncio.run(main())
