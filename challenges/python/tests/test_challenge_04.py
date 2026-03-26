import pytest
from unittest.mock import patch
from challenges.challenge_04 import criar_grafo, SupervisorInterface, PublicacaoState


# ─────────────────────────────────────────────
# MOCKS DE SUPERVISOR
# ─────────────────────────────────────────────

class SupervisorCorreto:
    """Supervisor que toma decisões na ordem certa."""
    def __init__(self):
        self.sequencia = ["revisor", "formatador", "publicador"]
        self.i = 0

    async def decidir(self, estado: PublicacaoState) -> dict:
        proximo = self.sequencia[min(self.i, len(self.sequencia) - 1)]
        self.i += 1
        return {"proximo": proximo, "motivo": f"Passo {self.i} da sequência"}


class SupervisorMalicioso:
    """Supervisor que sempre tenta ir para publicador (pula etapas)."""
    async def decidir(self, estado: PublicacaoState) -> dict:
        return {"proximo": "publicador", "motivo": "Tentando pular etapas"}


class SupervisorSequencia:
    """Supervisor configurável para testes específicos."""
    def __init__(self, sequencia: list[str]):
        self.sequencia = sequencia
        self.i = 0

    async def decidir(self, estado: PublicacaoState) -> dict:
        proximo = self.sequencia[min(self.i, len(self.sequencia) - 1)]
        self.i += 1
        return {"proximo": proximo, "motivo": f"Decisão {self.i}"}


# ─────────────────────────────────────────────
# TESTES
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_completo_ordem_correta():
    grafo = criar_grafo(SupervisorCorreto())
    config = {"configurable": {"thread_id": "test-001"}}

    resultado = await grafo.ainvoke(
        {"conteudo_original": "Artigo sobre LangGraph", "historico": []},
        config,
    )

    assert resultado["revisao"]
    assert resultado["formatacao"]
    assert resultado["publicado"] is True
    assert resultado["url_publicacao"]


@pytest.mark.asyncio
async def test_guardrail_corrige_supervisor_malicioso():
    logs_guardrail = []

    original_print = print
    def print_captura(*args, **kwargs):
        msg = " ".join(str(a) for a in args)
        if "Guardrail" in msg or "⚠️" in msg:
            logs_guardrail.append(msg)
        original_print(*args, **kwargs)

    grafo = criar_grafo(SupervisorMalicioso())
    config = {"configurable": {"thread_id": "test-malicioso"}}

    with patch("builtins.print", side_effect=print_captura):
        resultado = await grafo.ainvoke(
            {"conteudo_original": "Artigo teste", "historico": []},
            config,
        )

    # Mesmo com supervisor malicioso, o pipeline deve completar corretamente
    assert resultado["revisao"]
    assert resultado["formatacao"]
    assert resultado["publicado"] is True

    # O guardrail deve ter sido acionado
    assert len(logs_guardrail) > 0


@pytest.mark.asyncio
async def test_guardrail_impede_pular_revisao():
    # Supervisor tenta ir direto para formatador sem revisar
    grafo = criar_grafo(SupervisorSequencia(["formatador", "publicador", "publicador"]))
    config = {"configurable": {"thread_id": "test-sem-revisao"}}

    resultado = await grafo.ainvoke(
        {"conteudo_original": "Artigo", "historico": []},
        config,
    )

    # Mesmo pulando, revisao deve existir no resultado
    assert resultado["revisao"]
    assert resultado["formatacao"]
    assert resultado["publicado"] is True


@pytest.mark.asyncio
async def test_historico_acumula_todas_etapas():
    grafo = criar_grafo(SupervisorCorreto())
    config = {"configurable": {"thread_id": "test-historico"}}

    resultado = await grafo.ainvoke(
        {"conteudo_original": "Artigo com histórico", "historico": []},
        config,
    )

    # Deve ter pelo menos 3 entradas (uma por agente)
    assert len(resultado["historico"]) >= 3


@pytest.mark.asyncio
async def test_persistencia_via_checkpointer():
    grafo = criar_grafo(SupervisorCorreto())
    config = {"configurable": {"thread_id": "test-persistencia"}}

    # Primeira invocação
    await grafo.ainvoke(
        {"conteudo_original": "Primeiro artigo", "historico": []},
        config,
    )

    # Recupera o estado salvo pelo checkpointer
    estado_salvo = grafo.get_state(config)

    assert estado_salvo.values is not None
    assert estado_salvo.values["publicado"] is True
