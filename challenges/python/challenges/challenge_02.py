"""
DESAFIO 02 — ROTEAMENTO INTELIGENTE
=====================================

Conceitos testados: Módulo 03
  - add_conditional_edges com roteamento por múltiplos critérios
  - Funções de roteamento que retornam strings
  - Grafos com múltiplos caminhos convergindo

CENÁRIO:
Implemente um sistema de roteamento de notificações.
Com base no tipo e urgência, a notificação é enviada por canais diferentes.

REGRAS DE ROTEAMENTO (implemente em rotear):

  urgente + sistema   → "incidente"  (canal de incidentes — alerta imediato)
  urgente + negocio   → "escalada"   (canal de escalada — decisores)
  urgente + outro     → "urgencia"   (canal de urgência geral)
  normal  + sistema   → "tecnico"    (canal técnico)
  normal  + negocio   → "comercial"  (canal comercial)
  normal  + outro     → "padrao"     (canal padrão)

FLUXO DO GRAFO:

  START → [classificar] ──(condicional)──→ [incidente]  ──┐
                                         → [escalada]   ──┤
                                         → [urgencia]   ──┤
                                         → [tecnico]    ──┤
                                         → [comercial]  ──┤
                                         → [padrao]     ──┤
                                                           ↓
                                              [registrar_envio] → END
"""

import operator
from datetime import datetime
from typing import TypedDict, Annotated, Literal

from langgraph.graph import StateGraph, START, END


# ─────────────────────────────────────────────
# TIPOS
# ─────────────────────────────────────────────

Urgencia = Literal["urgente", "normal"]
TipoNotificacao = Literal["sistema", "negocio", "outro"]
Canal = Literal["incidente", "escalada", "urgencia", "tecnico", "comercial", "padrao"]


# ─────────────────────────────────────────────
# ESTADO (já definido)
# ─────────────────────────────────────────────

class NotificacaoState(TypedDict):
    titulo: str
    mensagem: str
    urgencia: Urgencia
    tipo: TipoNotificacao
    canal: Canal
    destinatarios: list[str]
    enviado: bool
    timestamp_envio: str


# ─────────────────────────────────────────────
# NÓ CLASSIFICAR (já implementado)
# ─────────────────────────────────────────────

def classificar(estado: NotificacaoState) -> dict:
    print(f"\n📋 [classificar] {estado['urgencia'].upper()} | {estado['tipo']}")
    return {}


# ─────────────────────────────────────────────
# TODO 1: Implemente a função de roteamento
# ─────────────────────────────────────────────
#
# Recebe o estado e retorna o nome do canal como string.
# Use as combinações de urgencia + tipo descritas acima.
#

def rotear(estado: NotificacaoState) -> Canal:
    # TODO: implemente o roteamento baseado em urgencia + tipo
    raise NotImplementedError("TODO: implemente a função rotear")


# ─────────────────────────────────────────────
# TODO 2: Implemente os handlers de canal
# ─────────────────────────────────────────────
#
# Cada handler deve:
#   - Definir o campo `canal` com o canal correspondente
#   - Definir `destinatarios` com uma lista de emails fictícios relevantes
#   - Definir `enviado` como True
#   - Definir `timestamp_envio` com datetime.now().isoformat()
#

def handle_incidente(estado: NotificacaoState) -> dict:
    # TODO: canal "incidente" — alertar equipe de plantão + oncall
    raise NotImplementedError("TODO: implemente handle_incidente")


def handle_escalada(estado: NotificacaoState) -> dict:
    # TODO: canal "escalada" — alertar diretoria + gerentes
    raise NotImplementedError("TODO: implemente handle_escalada")


def handle_urgencia(estado: NotificacaoState) -> dict:
    # TODO: canal "urgencia" — equipe geral de urgência
    raise NotImplementedError("TODO: implemente handle_urgencia")


def handle_tecnico(estado: NotificacaoState) -> dict:
    # TODO: canal "tecnico" — equipe técnica
    raise NotImplementedError("TODO: implemente handle_tecnico")


def handle_comercial(estado: NotificacaoState) -> dict:
    # TODO: canal "comercial" — equipe comercial
    raise NotImplementedError("TODO: implemente handle_comercial")


def handle_padrao(estado: NotificacaoState) -> dict:
    # TODO: canal "padrao" — fila de notificações padrão
    raise NotImplementedError("TODO: implemente handle_padrao")


# ─────────────────────────────────────────────
# NÓ REGISTRAR (já implementado)
# ─────────────────────────────────────────────

def registrar_envio(estado: NotificacaoState) -> dict:
    n = len(estado.get("destinatarios", []))
    print(f"\n✅ [registrar] Canal: {estado.get('canal')} | Destinatários: {n}")
    return {}


# ─────────────────────────────────────────────
# TODO 3: Monte o grafo
# ─────────────────────────────────────────────
#
# DICA: Use add_conditional_edges com um mapa que cobre todos os 6 canais.
# Todos os handlers devem convergir para "registrar_envio".
#

def criar_grafo():
    # TODO: monte e retorne o grafo compilado
    raise NotImplementedError("TODO: monte o grafo")
