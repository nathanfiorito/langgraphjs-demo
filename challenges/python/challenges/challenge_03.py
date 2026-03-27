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

COMO OS MOCKS FUNCIONAM:

  Os testes não chamam a API real — eles injetam um objeto LLMMock que
  implementa a mesma interface (LLMInterface) que um LLM real usaria.

  ┌─ Nos testes (tests/test_challenge_03.py) ──────────────────────────────┐
  │  class LLMMock:                                                          │
  │      async def ainvoke(self, messages) -> AIMessage:                     │
  │          return self.respostas[self.indice]   # resposta predefinida     │
  │                                                                          │
  │  mock = LLMMock([                                                        │
  │      criar_tool_call("somar", {"a": 3, "b": 4}),   # 1ª chamada: usa   │
  │      AIMessage(content="O resultado é 7"),          # 2ª chamada: encerra│
  │  ])                                                                      │
  │  grafo = criar_grafo(mock)  ← mock injetado aqui                        │
  └──────────────────────────────────────────────────────────────────────────┘

  Isso permite testar o fluxo do grafo (loop ReAct, acumulação de mensagens,
  roteamento) sem depender de API key ou de respostas não-determinísticas.

  Quando você quiser usar o LLM real, basta trocar o mock — o grafo não muda.

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
    # TODO: adicione o campo messages com add_messages como reducer
    messages: Annotated[list[BaseMessage], add_messages]


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
        
        resposta = await llm.ainvoke(estado["messages"])

        tool_calls = getattr(resposta, "tool_calls", [])
        if tool_calls:
            nomes = [t["name"] for t in tool_calls]
            print(f"   → Solicitando ferramenta(s): {', '.join(nomes)}")
        else:
            print("   → Respondendo diretamente ao usuário")

        return {"messages": [resposta]}

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
    ultima_mensagem = estado["messages"][-1]
    tool_calls = getattr(ultima_mensagem, "tool_calls", [])
    if tool_calls:
        return "executar_tools"
    return END


# ─────────────────────────────────────────────
# TODO 3: Monte o grafo
# ─────────────────────────────────────────────
#
# O LLM é injetado para permitir usar mock nos testes.
#

def criar_grafo(llm: LLMInterface):
    # TODO: monte e retorne o grafo compilado com o loop ReAct
    return (
        StateGraph(AgenteState)
        .add_node("agente", criar_no_agente(llm))
        .add_node("executar_tools", ToolNode(ferramentas))
        .add_edge(START, "agente")
        .add_conditional_edges("agente", verificar_proximo_passo)
        .add_edge("executar_tools", "agente")
        .compile()
    )


# ─────────────────────────────────────────────
# 🎯 BÔNUS: Substituir o mock pelo Claude real
# ─────────────────────────────────────────────
#
# Depois de passar nos testes com o mock, você pode rodar com o LLM real.
# O ChatAnthropic com .bind_tools() já implementa a interface LLMInterface
# (tem o método .ainvoke), então é só trocar na chamada de criar_grafo().
#
# Passos:
#   1. Copie o bloco abaixo para um arquivo separado (ex: run_bonus_03.py)
#   2. Certifique-se de ter ANTHROPIC_API_KEY no arquivo .env na raiz do repo
#   3. Execute: python run_bonus_03.py
#
# import asyncio
# from pathlib import Path
# from dotenv import load_dotenv
# from langchain_anthropic import ChatAnthropic
# from langchain_core.messages import HumanMessage
# from challenges.challenge_03 import criar_grafo, ferramentas
#
# load_dotenv(dotenv_path=Path(__file__).parents[0] / ".env")
#
# # bind_tools() vincula as ferramentas ao modelo — ele saberá quando chamá-las
# modelo_real = ChatAnthropic(
#     model="claude-haiku-4-5-20251001", temperature=0
# ).bind_tools(ferramentas)
#
# # Mesma função criar_grafo dos testes — só o argumento muda
# grafo_real = criar_grafo(modelo_real)
#
# async def main():
#     resultado = await grafo_real.ainvoke({
#         "messages": [HumanMessage(content="Quanto é (3 + 4) elevado ao quadrado?")]
#     })
#     print(resultado["messages"][-1].content)
#     # Esperado: algo como "O resultado é 49"
#
# if __name__ == "__main__":
#     asyncio.run(main())
