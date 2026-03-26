"""
MÓDULO 02 — GERENCIAMENTO DE ESTADO
=====================================

O estado é o coração do LangGraph. Neste módulo exploramos:

  1. Reducers customizados — controlam como atualizações são aplicadas
  2. operator.add para listas — acumulação automática
  3. Reducer de merge para dicts — atualização parcial de objetos
  4. Tipos complexos com Literal e TypedDict aninhado

Cenário: Um pipeline de análise de texto que acumula métricas
ao longo da execução.

  START → [analisar] → [calcular_metricas] → [gerar_relatorio] → END

Diferenças em relação ao TypeScript:
  - Sem Annotation.Root — usamos TypedDict diretamente
  - Reducer de dict: função customizada (sem equivalente direto ao spread do JS)
  - Literal["a", "b"] em vez de union types com |
  - TypedDict aninhado em vez de interface
"""

import sys
import operator
from typing import TypedDict, Annotated, Literal

from langgraph.graph import StateGraph, START, END

sys.stdout.reconfigure(encoding="utf-8")


# ─────────────────────────────────────────────
# TIPOS DE APOIO
# ─────────────────────────────────────────────

class Metrica(TypedDict):
    nome: str
    valor: float


# Literal define um tipo restrito a valores específicos
# Equivale ao union type: "pendente" | "em_progresso" | "concluido" | "erro"
StatusAnalise = Literal["pendente", "em_progresso", "concluido", "erro"]


# ─────────────────────────────────────────────
# 1. REDUCER CUSTOMIZADO PARA DICTS
# ─────────────────────────────────────────────
#
# Python não tem um reducer de merge nativo para dicts como o JS ({...a, ...b}).
# Criamos uma função simples que faz o merge (shallow):
#

def merge_dict(atual: dict, novo: dict) -> dict:
    """Faz o merge de dois dicts, com o novo sobrescrevendo chaves existentes."""
    return {**atual, **novo}


# ─────────────────────────────────────────────
# 2. ESTADO COM REDUCERS VARIADOS
# ─────────────────────────────────────────────

class AnaliseState(TypedDict):
    # ── Campos simples (último valor vence) ──────────────────────────
    texto: str
    status: StatusAnalise

    # ── Lista com acumulação ─────────────────────────────────────────
    # operator.add em listas faz: lista_atual + lista_nova
    # Cada nó pode adicionar itens sem sobrescrever a lista inteira
    metricas: Annotated[list[Metrica], operator.add]
    logs: Annotated[list[str], operator.add]

    # ── Dict com merge ────────────────────────────────────────────────
    # merge_dict mescla os dicts: {**atual, **novo}
    # Nós podem atualizar apenas algumas chaves sem afetar as demais
    resumo: Annotated[dict, merge_dict]


# ─────────────────────────────────────────────
# 3. FUNÇÕES UTILITÁRIAS
# ─────────────────────────────────────────────

def log(mensagem: str) -> None:
    print(f"  ℹ️  {mensagem}")


def contar_palavras(texto: str) -> int:
    return len([p for p in texto.split() if p])


def contar_caracteres(texto: str) -> int:
    return len(texto.replace(" ", ""))


def calcular_media_palavra(texto: str) -> float:
    palavras = [p for p in texto.split() if p]
    if not palavras:
        return 0.0
    return round(sum(len(p) for p in palavras) / len(palavras), 2)


# ─────────────────────────────────────────────
# 4. NÓS
# ─────────────────────────────────────────────

def analisar(estado: AnaliseState) -> dict:
    print("\n🔍 [analisar] Iniciando análise...")

    if not estado.get("texto", "").strip():
        log("Texto vazio detectado — marcando como erro")
        return {
            "status": "erro",
            "logs": ["ERRO: Texto vazio recebido"],
        }

    log(f"Texto com {len(estado['texto'])} caracteres recebido")

    return {
        "status": "em_progresso",
        "logs": ["Análise iniciada"],
        # Atualização parcial do dict resumo — merge_dict preserva os outros campos
        "resumo": {"texto_original": estado["texto"]},
    }


def calcular_metricas(estado: AnaliseState) -> dict:
    print("\n📐 [calcular_metricas] Calculando métricas...")

    # Demonstração: lemos do estado global, mas retornamos APENAS as atualizações
    novas_metricas: list[Metrica] = [
        {"nome": "palavras", "valor": contar_palavras(estado["texto"])},
        {"nome": "caracteres_sem_espaco", "valor": contar_caracteres(estado["texto"])},
        {"nome": "chars_por_palavra", "valor": calcular_media_palavra(estado["texto"])},
        {"nome": "total_caracteres", "valor": len(estado["texto"])},
    ]

    for m in novas_metricas:
        log(f"{m['nome']}: {m['valor']}")

    return {
        # O reducer operator.add vai ACUMULAR essas métricas (não sobrescrever)
        "metricas": novas_metricas,
        "logs": [f"{len(novas_metricas)} métricas calculadas"],
        "resumo": {"total_metricas": len(novas_metricas)},
    }


def gerar_relatorio(estado: AnaliseState) -> dict:
    print("\n📄 [gerar_relatorio] Gerando relatório...")

    # Lemos TODO o estado acumulado pelos nós anteriores
    palavras_metrica = next(
        (m for m in estado["metricas"] if m["nome"] == "palavras"), None
    )
    chars_metrica = next(
        (m for m in estado["metricas"] if m["nome"] == "caracteres_sem_espaco"), None
    )

    log(f"Total de métricas disponíveis: {len(estado['metricas'])}")
    log(f"Logs acumulados até agora: {len(estado['logs'])}")

    return {
        "status": "concluido",
        "logs": ["Relatório gerado com sucesso"],
        "resumo": {
            "palavras": palavras_metrica["valor"] if palavras_metrica else None,
            "caracteres_sem_espaco": chars_metrica["valor"] if chars_metrica else None,
            "status_final": "concluido",
        },
    }


# ─────────────────────────────────────────────
# 5. GRAFO
# ─────────────────────────────────────────────

grafo = (
    StateGraph(AnaliseState)
    .add_node("analisar", analisar)
    .add_node("calcular_metricas", calcular_metricas)
    .add_node("gerar_relatorio", gerar_relatorio)
    .add_edge(START, "analisar")
    .add_edge("analisar", "calcular_metricas")
    .add_edge("calcular_metricas", "gerar_relatorio")
    .add_edge("gerar_relatorio", END)
    .compile()
)


# ─────────────────────────────────────────────
# 6. EXECUÇÃO E INSPEÇÃO DO ESTADO
# ─────────────────────────────────────────────

def main():
    print("═══════════════════════════════════════")
    print("  MÓDULO 02 — GERENCIAMENTO DE ESTADO (Python)")
    print("═══════════════════════════════════════")

    texto_exemplo = (
        "O LangGraph permite criar agentes de IA complexos usando grafos de estado. "
        "Cada nó do grafo recebe o estado atual e retorna atualizações parciais."
    )

    resultado = grafo.invoke({
        "texto": texto_exemplo,
        "metricas": [],
        "logs": [],
        "resumo": {},
    })

    print("\n─────────────────────────────────────")
    print("📊 ESTADO FINAL:")
    print("─────────────────────────────────────")
    print(f"Status: {resultado['status']}")

    print("\nMétricas acumuladas (via reducer):")
    for m in resultado["metricas"]:
        print(f"  • {m['nome']:<25} = {m['valor']}")

    print("\nResumo (via merge reducer):")
    for k, v in resultado["resumo"].items():
        print(f"  {k}: {v}")

    print("\nLogs do pipeline:")
    for i, entrada in enumerate(resultado["logs"], 1):
        print(f"  {i}. {entrada}")


if __name__ == "__main__":
    main()
