"""
MÓDULO 05 — MULTI-AGENT (ORQUESTRAÇÃO DE MÚLTIPLOS AGENTES)
=============================================================

O padrão mais poderoso do LangGraph: múltiplos agentes especializados
trabalhando juntos sob a coordenação de um supervisor.

Padrão Supervisor:
  - O SUPERVISOR avalia a tarefa e delega para o especialista certo
  - Cada ESPECIALISTA tem ferramentas e prompts específicos
  - O supervisor avalia o resultado e decide se está pronto ou precisa
    de mais trabalho

Diferenças em relação ao TypeScript:
  - withStructuredOutput(zodSchema) → with_structured_output(PydanticModel)
  - Pydantic BaseModel define o schema de saída estruturada do supervisor
  - asyncio.run() para main assíncrono
  - Guardrails idênticos ao TS — lógica determinística que sobrepõe a IA

Fluxo:
  START → [supervisor] ──→ "analista" ──→ [analista] ──┐
                │                                        │
                │           "redator"  ──→ [redator]  ──│
                │                                        ↓
                └──────── "finalizar"  ──→ [finalizar] → END
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import TypedDict, Annotated, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")


# ─────────────────────────────────────────────
# TIPOS
# ─────────────────────────────────────────────

ProximoAgente = Literal["analista", "redator", "finalizar"]


# ─────────────────────────────────────────────
# 1. ESTADO COMPARTILHADO
# ─────────────────────────────────────────────

class MultiAgenteState(TypedDict):
    tarefa: str
    proximo_agente: ProximoAgente
    analise_realizada: str
    relatorio_redigido: str
    resultado_final: str
    mensagens_analista: Annotated[list[BaseMessage], add_messages]
    mensagens_redator: Annotated[list[BaseMessage], add_messages]
    decisoes_supervisor: Annotated[list[str], lambda a, b: a + b]


# ─────────────────────────────────────────────
# 2. SCHEMA DE SAÍDA ESTRUTURADA DO SUPERVISOR
# ─────────────────────────────────────────────
#
# Em Python, usamos um Pydantic BaseModel em vez do schema Zod do TypeScript.
# with_structured_output(DecisaoSupervisor) garante que o LLM retorne
# um objeto com exatamente esses campos.
#

class DecisaoSupervisor(BaseModel):
    proximo: Literal["analista", "redator", "finalizar"] = Field(
        description=(
            "Próximo agente. Siga OBRIGATORIAMENTE esta sequência:\n"
            "1. Se análise_realizada estiver vazia → 'analista'\n"
            "2. Se análise_realizada preenchida e relatorio_redigido vazio → 'redator'\n"
            "3. Se ambos preenchidos → 'finalizar'"
        )
    )
    justificativa: str = Field(description="Motivo da decisão")


# ─────────────────────────────────────────────
# 3. MODELOS LLM
# ─────────────────────────────────────────────

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)


# ─────────────────────────────────────────────
# 4. FERRAMENTAS DO ANALISTA
# ─────────────────────────────────────────────

@tool
def calcular_estatisticas(numeros: list[float]) -> str:
    """Calcula estatísticas descritivas de uma lista de números.

    Args:
        numeros: Lista de números para análise
    """
    soma = sum(numeros)
    media = soma / len(numeros)
    minimo = min(numeros)
    maximo = max(numeros)
    variancia = sum((n - media) ** 2 for n in numeros) / len(numeros)
    desvio_padrao = variancia ** 0.5

    return json.dumps({
        "soma": soma,
        "media": round(media, 2),
        "minimo": minimo,
        "maximo": maximo,
        "desvio_padrao": round(desvio_padrao, 2),
        "contagem": len(numeros),
    }, ensure_ascii=False)


@tool
def identificar_tendencia(valores: list[float], periodos: list[str]) -> str:
    """Identifica tendência em uma série temporal de valores.

    Args:
        valores: Série histórica de valores
        periodos: Rótulos dos períodos
    """
    ultimos_tres = valores[-3:]
    if ultimos_tres[-1] > ultimos_tres[0]:
        tendencia = "crescente"
    elif ultimos_tres[-1] < ultimos_tres[0]:
        tendencia = "decrescente"
    else:
        tendencia = "estável"

    variacao = ((valores[-1] - valores[0]) / valores[0] * 100)

    return json.dumps({
        "tendencia": tendencia,
        "variacao_total": f"{variacao:.1f}%",
        "periodos": periodos,
        "valores": valores,
    }, ensure_ascii=False)


ferramentas_analista = [calcular_estatisticas, identificar_tendencia]


# ─────────────────────────────────────────────
# 5. AGENTE SUPERVISOR
# ─────────────────────────────────────────────

async def supervisor(estado: MultiAgenteState) -> dict:
    print("\n🎯 [supervisor] Avaliando situação...")

    # with_structured_output(PydanticModel) garante retorno tipado
    modelo_estruturado = llm.with_structured_output(DecisaoSupervisor)

    contexto = (
        f"Tarefa: {estado['tarefa']}\n"
        f"Análise realizada: {estado.get('analise_realizada') or 'Ainda não feita'}\n"
        f"Relatório redigido: {estado.get('relatorio_redigido') or 'Ainda não feito'}"
    )

    decisao: DecisaoSupervisor = await modelo_estruturado.ainvoke([
        SystemMessage(content=(
            "Você é um supervisor que coordena agentes especializados. "
            "Avalie o progresso e decida qual agente deve agir a seguir. "
            "Siga OBRIGATORIAMENTE: analista → redator → finalizar."
        )),
        HumanMessage(content=contexto),
    ])

    print(f"   Decisão: {decisao.proximo} — {decisao.justificativa}")

    return {
        "proximo_agente": decisao.proximo,
        "decisoes_supervisor": [f"{decisao.proximo}: {decisao.justificativa}"],
    }


# ─────────────────────────────────────────────
# 6. AGENTE ANALISTA
# ─────────────────────────────────────────────

llm_analista = ChatAnthropic(
    model="claude-haiku-4-5-20251001", temperature=0
).bind_tools(ferramentas_analista)


async def analista(estado: MultiAgenteState) -> dict:
    print("\n📊 [analista] Realizando análise...")

    mensagens: list[BaseMessage] = [
        SystemMessage(content=(
            "Você é um analista de dados especialista. "
            "Analise os dados da tarefa usando as ferramentas disponíveis. "
            "Seja preciso e objetivo na análise."
        )),
        HumanMessage(content=estado["tarefa"]),
    ]

    analise_texto = ""

    for i in range(5):  # máximo 5 iterações
        resposta = await llm_analista.ainvoke(mensagens)
        mensagens = [*mensagens, resposta]

        tool_calls = getattr(resposta, "tool_calls", [])
        if not tool_calls:
            analise_texto = resposta.content
            print("   ✓ Análise concluída")
            break

        print(f"   → Usando ferramenta(s): {', '.join(t['name'] for t in tool_calls)}")

        # Executa as ferramentas e obtém os resultados
        resultado_tools = await ToolNode(ferramentas_analista).ainvoke({
            "messages": mensagens,
        })
        mensagens = [*mensagens, *resultado_tools["messages"]]

        # Fallback na última iteração
        if i == 4:
            analise_texto = f"Análise parcial (máximo de iterações atingido): {resposta.content}"

    return {
        "analise_realizada": analise_texto,
        "mensagens_analista": mensagens,
    }


# ─────────────────────────────────────────────
# 7. AGENTE REDATOR
# ─────────────────────────────────────────────

async def redator(estado: MultiAgenteState) -> dict:
    print("\n✍️  [redator] Redigindo relatório...")

    resposta = await llm.ainvoke([
        SystemMessage(content=(
            "Você é um redator especializado em relatórios executivos. "
            "Transforme a análise técnica em um relatório claro e profissional. "
            "Use formatação markdown com títulos, bullets e destaques."
        )),
        HumanMessage(content=(
            f"Tarefa original: {estado['tarefa']}\n\n"
            f"Análise realizada pelo analista:\n{estado['analise_realizada']}\n\n"
            "Escreva um relatório executivo baseado nessa análise."
        )),
    ])

    print("   ✓ Relatório redigido")

    return {
        "relatorio_redigido": resposta.content,
        "mensagens_redator": [
            HumanMessage(content="Redija o relatório"),
            resposta,
        ],
    }


# ─────────────────────────────────────────────
# 8. NÓ FINALIZAR
# ─────────────────────────────────────────────

def finalizar(estado: MultiAgenteState) -> dict:
    print("\n🏁 [finalizar] Consolidando resultado...")

    decisoes = "\n".join(f"  - {d}" for d in estado.get("decisoes_supervisor", []))
    resultado = (
        f"# Trabalho Concluído\n\n"
        f"## Relatório Final\n{estado['relatorio_redigido']}\n\n"
        f"---\n"
        f"*Gerado por: Supervisor → Analista → Redator*\n"
        f"*Decisões do supervisor:*\n{decisoes}"
    )

    return {"resultado_final": resultado}


# ─────────────────────────────────────────────
# 9. FUNÇÃO DE ROTEAMENTO COM GUARDRAILS
# ─────────────────────────────────────────────
#
# Guardrail: nunca confia cegamente na decisão do LLM.
# Regras determinísticas garantem a sequência obrigatória.
#

def rotear_supervisor(estado: MultiAgenteState) -> str:
    proximo = estado.get("proximo_agente", "analista")

    # Guardrail 1: sem análise → forçar analista
    if not estado.get("analise_realizada"):
        if proximo != "analista":
            print(f"   ⚠️  Guardrail: supervisor escolheu '{proximo}' sem análise → forçando 'analista'")
        return "analista"

    # Guardrail 2: sem relatório → nunca finalizar
    if not estado.get("relatorio_redigido"):
        if proximo == "finalizar":
            print("   ⚠️  Guardrail: supervisor quis finalizar sem relatório → forçando 'redator'")
        return "redator" if proximo in ("finalizar", "redator") else "analista"

    return "finalizar" if proximo == "finalizar" else proximo


# ─────────────────────────────────────────────
# 10. GRAFO MULTI-AGENTE
# ─────────────────────────────────────────────

grafo = (
    StateGraph(MultiAgenteState)
    .add_node("supervisor", supervisor)
    .add_node("analista", analista)
    .add_node("redator", redator)
    .add_node("finalizar", finalizar)
    .add_edge(START, "supervisor")
    .add_conditional_edges("supervisor", rotear_supervisor, {
        "analista": "analista",
        "redator": "redator",
        "finalizar": "finalizar",
    })
    .add_edge("analista", "supervisor")
    .add_edge("redator", "supervisor")
    .add_edge("finalizar", END)
    .compile()
)


# ─────────────────────────────────────────────
# 11. EXECUÇÃO
# ─────────────────────────────────────────────

async def main():
    print("═══════════════════════════════════════════════════════════")
    print("  MÓDULO 05 — MULTI-AGENT (Python)")
    print("═══════════════════════════════════════════════════════════")

    tarefa = (
        "Analise as vendas mensais do último trimestre: "
        "Janeiro: R$45.000, Fevereiro: R$52.000, Março: R$61.000. "
        "Calcule as estatísticas e identifique a tendência. "
        "Depois prepare um relatório executivo com os insights."
    )

    print(f"\n📋 Tarefa: {tarefa}")

    resultado = await grafo.ainvoke({
        "tarefa": tarefa,
        "analise_realizada": "",
        "relatorio_redigido": "",
        "resultado_final": "",
        "mensagens_analista": [],
        "mensagens_redator": [],
        "decisoes_supervisor": [],
    })

    print("\n" + "═" * 60)
    print("📄 RESULTADO FINAL:")
    print("═" * 60)
    print(resultado["resultado_final"])


if __name__ == "__main__":
    asyncio.run(main())
