"""
MÓDULO 04 — TOOL CALLING (AGENTE COM FERRAMENTAS)
===================================================

Aqui entra o LLM! Este módulo implementa o padrão ReAct:

  ReAct = Reasoning + Acting
  O agente alterna entre "pensar" (raciocinar sobre o problema)
  e "agir" (chamar ferramentas para obter informações).

Ferramentas (Tools) são funções Python que o LLM pode invocar.
O LLM decide QUANDO e COMO chamar cada ferramenta.

Fluxo do padrão ReAct:

  START → [agente] ──── (precisa de tool) ──→ [executar_tools] ─┐
              ↑                                                    │
              └────────────────────────────────────────────────────┘
              │
          (resposta final)
              ↓
             END

Diferenças em relação ao TypeScript:
  - @tool decorator em vez de tool() function
  - add_messages reducer de langgraph.graph.message (em vez de Annotation manual)
  - bind_tools() em vez de bindTools()
  - asyncio.run() para executar código assíncrono
  - Verificação de tool_calls via hasattr/getattr
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

sys.stdout.reconfigure(encoding="utf-8")

# Carrega .env da raiz do repositório (dois níveis acima de src/)
load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")


# ─────────────────────────────────────────────
# 1. DEFINIÇÃO DAS FERRAMENTAS
# ─────────────────────────────────────────────
#
# @tool decorator converte uma função Python em uma ferramenta LangChain.
# O docstring se torna a descrição da ferramenta (ajuda o LLM a decidir quando usar).
# Os type hints dos parâmetros definem o schema que o LLM deve seguir.
#

@tool
def calcular_imc(peso: float, altura: float) -> str:
    """Calcula o Índice de Massa Corporal (IMC) e retorna a classificação.
    Use quando o usuário perguntar sobre IMC, peso ideal ou saúde corporal.

    Args:
        peso: Peso em quilogramas (kg)
        altura: Altura em metros (ex: 1.75)
    """
    imc = peso / (altura ** 2)

    if imc < 18.5:
        classificacao = "Abaixo do peso"
    elif imc < 25:
        classificacao = "Peso normal"
    elif imc < 30:
        classificacao = "Sobrepeso"
    else:
        classificacao = "Obesidade"

    return json.dumps({
        "imc": round(imc, 2),
        "classificacao": classificacao,
        "peso": peso,
        "altura": altura,
    }, ensure_ascii=False)


@tool
def buscar_clima_atual(cidade: str) -> str:
    """Busca as condições climáticas atuais de uma cidade brasileira.
    Retorna temperatura, sensação térmica, condição do céu e umidade.

    Args:
        cidade: Nome da cidade brasileira
    """
    # Dados simulados — em produção, chamaria uma API real (ex: OpenWeatherMap)
    climas = {
        "São Paulo": {"temperatura": 22, "sensacao": 20, "condicao": "Parcialmente nublado", "umidade": 75},
        "Rio de Janeiro": {"temperatura": 30, "sensacao": 33, "condicao": "Ensolarado", "umidade": 80},
        "Curitiba": {"temperatura": 15, "sensacao": 13, "condicao": "Chuvoso", "umidade": 90},
        "Porto Alegre": {"temperatura": 18, "sensacao": 16, "condicao": "Nublado", "umidade": 85},
    }

    clima = climas.get(cidade, {
        "temperatura": 20,
        "sensacao": 19,
        "condicao": "Dados não disponíveis para esta cidade",
        "umidade": 70,
    })

    return json.dumps({"cidade": cidade, **clima, "unidade": "Celsius"}, ensure_ascii=False)


@tool
def converter_moeda(valor: float, moeda_origem: str, moeda_destino: str) -> str:
    """Converte um valor monetário de uma moeda para outra.
    Moedas suportadas: USD, BRL, EUR, GBP, JPY.

    Args:
        valor: Valor a ser convertido
        moeda_origem: Código da moeda de origem (ex: BRL)
        moeda_destino: Código da moeda de destino (ex: USD)
    """
    # Taxas simuladas em relação ao USD
    taxas = {
        "USD": 1.0,
        "BRL": 5.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 149.5,
    }

    origem = moeda_origem.upper()
    destino = moeda_destino.upper()

    if origem not in taxas or destino not in taxas:
        return json.dumps({"erro": f"Moeda não suportada: {origem} ou {destino}"})

    valor_usd = valor / taxas[origem]
    valor_convertido = valor_usd * taxas[destino]

    return json.dumps({
        "valor_original": valor,
        "moeda_origem": origem,
        "valor_convertido": round(valor_convertido, 2),
        "moeda_destino": destino,
        "taxa": round(taxas[destino] / taxas[origem], 4),
    }, ensure_ascii=False)


ferramentas = [calcular_imc, buscar_clima_atual, converter_moeda]


# ─────────────────────────────────────────────
# 2. MODELO LLM COM FERRAMENTAS VINCULADAS
# ─────────────────────────────────────────────
#
# bind_tools() informa ao Claude quais ferramentas ele pode usar.
# O Claude decide autonomamente quando e como invocar cada uma.
#

modelo = ChatAnthropic(
    model="claude-haiku-4-5-20251001",  # Haiku: rápido e econômico para demos
    temperature=0,
).bind_tools(ferramentas)


# ─────────────────────────────────────────────
# 3. ESTADO
# ─────────────────────────────────────────────
#
# add_messages é um reducer especial do LangGraph para listas de mensagens.
# Ele garante que as mensagens sejam acumuladas corretamente,
# tratando IDs duplicados e outros casos especiais.
#

class AgenteState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ─────────────────────────────────────────────
# 4. NÓS
# ─────────────────────────────────────────────

async def agente(estado: AgenteState) -> dict:
    print(f"\n🤖 [agente] Pensando... ({len(estado['messages'])} msgs no contexto)")

    resposta = await modelo.ainvoke(estado["messages"])

    # Verifica se o LLM quer chamar alguma ferramenta
    tool_calls = getattr(resposta, "tool_calls", [])
    if tool_calls:
        nomes = [t["name"] for t in tool_calls]
        print(f"   → Solicitando ferramenta(s): {', '.join(nomes)}")
    else:
        print("   → Respondendo diretamente ao usuário")

    return {"messages": [resposta]}


# ─────────────────────────────────────────────
# 5. FUNÇÃO DE ROTEAMENTO
# ─────────────────────────────────────────────
#
# Verifica a última mensagem:
#   - Se o LLM chamou ferramentas → vai para o nó de ferramentas
#   - Se deu uma resposta final   → termina o grafo
#

def verificar_proximo_passo(estado: AgenteState) -> str:
    ultima_mensagem = estado["messages"][-1]
    tool_calls = getattr(ultima_mensagem, "tool_calls", [])
    if tool_calls:
        return "executar_tools"
    return END


# ─────────────────────────────────────────────
# 6. GRAFO
# ─────────────────────────────────────────────
#
# ToolNode é um nó pré-construído do LangGraph que:
#   1. Lê as tool_calls da última mensagem
#   2. Executa cada ferramenta com os argumentos fornecidos pelo LLM
#   3. Adiciona as respostas como ToolMessages no estado
#

grafo = (
    StateGraph(AgenteState)
    .add_node("agente", agente)
    .add_node("executar_tools", ToolNode(ferramentas))
    .add_edge(START, "agente")
    .add_conditional_edges("agente", verificar_proximo_passo)
    .add_edge("executar_tools", "agente")
    .compile()
)


# ─────────────────────────────────────────────
# 7. EXECUÇÃO
# ─────────────────────────────────────────────

async def perguntar(pergunta: str) -> None:
    print("\n" + "═" * 60)
    print(f"👤 Usuário: {pergunta}")

    resultado = await grafo.ainvoke({
        "messages": [HumanMessage(content=pergunta)],
    })

    ultima_mensagem = resultado["messages"][-1]
    print(f"\n🤖 Claude: {ultima_mensagem.content}")
    print(f"\n📊 Total de mensagens na conversa: {len(resultado['messages'])}")


async def main():
    print("═══════════════════════════════════════════════════════════")
    print("  MÓDULO 04 — TOOL CALLING (Python)")
    print("═══════════════════════════════════════════════════════════")

    await perguntar("Qual o clima atual em São Paulo?")
    await perguntar("Tenho 80kg e 1,75m de altura. Qual meu IMC?")
    await perguntar("Tenho R$ 1000 reais. Quanto vale em euros e dólares?")


if __name__ == "__main__":
    asyncio.run(main())
