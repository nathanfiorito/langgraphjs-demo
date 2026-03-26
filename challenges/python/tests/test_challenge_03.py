import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from challenges.challenge_03 import criar_grafo, LLMInterface, ferramentas


# ─────────────────────────────────────────────
# LLM MOCK
# ─────────────────────────────────────────────

class LLMMock:
    """Simula o comportamento do LLM sem chamar a API real."""

    def __init__(self, respostas: list[AIMessage]):
        self.respostas = respostas
        self.indice = 0

    async def ainvoke(self, messages):
        resposta = self.respostas[self.indice]
        self.indice = min(self.indice + 1, len(self.respostas) - 1)
        return resposta


def criar_tool_call(nome: str, args: dict, tool_id: str = "tc_001") -> AIMessage:
    """Cria uma AIMessage que simula uma chamada de ferramenta."""
    return AIMessage(
        content="",
        tool_calls=[{"id": tool_id, "name": nome, "args": args, "type": "tool_call"}],
    )


# ─────────────────────────────────────────────
# TESTES
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_executa_uma_ferramenta_e_responde():
    mock = LLMMock([
        criar_tool_call("somar", {"a": 3, "b": 4}),
        AIMessage(content="O resultado é 7"),
    ])

    grafo = criar_grafo(mock)
    resultado = await grafo.ainvoke({
        "messages": [HumanMessage(content="Quanto é 3 + 4?")],
    })

    ultima = resultado["messages"][-1]
    assert ultima.content == "O resultado é 7"
    # Human + AI(tool_call) + ToolMessage + AI(resposta)
    assert len(resultado["messages"]) == 4


@pytest.mark.asyncio
async def test_acumula_multiplas_mensagens():
    mock = LLMMock([
        criar_tool_call("multiplicar", {"a": 5, "b": 6}),
        AIMessage(content="5 multiplicado por 6 é 30"),
    ])

    grafo = criar_grafo(mock)
    resultado = await grafo.ainvoke({
        "messages": [HumanMessage(content="Quanto é 5 * 6?")],
    })

    assert isinstance(resultado["messages"][0], HumanMessage)
    ultima = resultado["messages"][-1]
    assert isinstance(ultima, AIMessage)
    assert not getattr(ultima, "tool_calls", [])


@pytest.mark.asyncio
async def test_responde_sem_ferramentas():
    mock = LLMMock([
        AIMessage(content="Dois mais dois é quatro."),
    ])

    grafo = criar_grafo(mock)
    resultado = await grafo.ainvoke({
        "messages": [HumanMessage(content="Quanto é 2 + 2?")],
    })

    # Apenas HumanMessage + AIMessage
    assert len(resultado["messages"]) == 2
    assert resultado["messages"][1].content == "Dois mais dois é quatro."


@pytest.mark.asyncio
async def test_executa_multiplas_ferramentas_em_sequencia():
    mock = LLMMock([
        criar_tool_call("somar", {"a": 10, "b": 5}, "tc_001"),
        criar_tool_call("potencia", {"base": 15.0, "exp": 2}, "tc_002"),
        AIMessage(content="Primeiro somei 10+5=15, depois elevei ao quadrado: 225"),
    ])

    grafo = criar_grafo(mock)
    resultado = await grafo.ainvoke({
        "messages": [HumanMessage(content="Qual é (10+5) ao quadrado?")],
    })

    # Human + AI(tool1) + Tool + AI(tool2) + Tool + AI(resposta)
    assert len(resultado["messages"]) == 6
    assert "225" in resultado["messages"][-1].content


@pytest.mark.asyncio
async def test_ferramenta_retorna_resultado_correto():
    mock = LLMMock([
        criar_tool_call("potencia", {"base": 2.0, "exp": 10.0}, "tc_pot"),
        AIMessage(content="2^10 = 1024"),
    ])

    grafo = criar_grafo(mock)
    resultado = await grafo.ainvoke({
        "messages": [HumanMessage(content="2 elevado a 10?")],
    })

    # Encontra a ToolMessage no histórico
    tool_messages = [m for m in resultado["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert tool_messages[0].content == "1024.0"
