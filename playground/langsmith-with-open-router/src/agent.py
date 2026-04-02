"""
Agente conversacional com LangGraph + OpenRouter + LangSmith.

Grafo:
    START -> chatbot -> END

O LangSmith é ativado automaticamente via variáveis de ambiente:
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_API_KEY=<sua chave>
    LANGCHAIN_PROJECT=<nome do projeto>
"""

import os
from typing import Annotated

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

class EstadoConversa(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ---------------------------------------------------------------------------
# LLM via OpenRouter
# ---------------------------------------------------------------------------

def criar_llm() -> ChatOpenAI:
    """Cria o cliente LLM apontando para a API do OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY não está definida no ambiente.")

    modelo = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    return ChatOpenAI(
        model=modelo,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            # Recomendado pelo OpenRouter para identificar a aplicação
            "HTTP-Referer": os.environ.get("APP_URL", "http://localhost"),
            "X-Title": os.environ.get("APP_TITLE", "LangGraph Demo"),
        },
    )


# ---------------------------------------------------------------------------
# Nós do grafo
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = SystemMessage(
    content=(
        "Você é um assistente útil e amigável. "
        "Responda sempre no mesmo idioma que o usuário usar."
    )
)


def criar_no_chatbot(llm: ChatOpenAI):
    """Retorna a função de nó que chama o LLM."""

    async def chatbot(state: EstadoConversa) -> dict:
        mensagens = [SYSTEM_PROMPT, *state["messages"]]
        resposta = await llm.ainvoke(mensagens)
        return {"messages": [resposta]}

    return chatbot


# ---------------------------------------------------------------------------
# Grafo
# ---------------------------------------------------------------------------

def criar_agente():
    """Monta e compila o grafo conversacional com checkpointing em memória."""
    llm = criar_llm()
    checkpointer = MemorySaver()

    grafo = (
        StateGraph(EstadoConversa)
        .add_node("chatbot", criar_no_chatbot(llm))
        .add_edge(START, "chatbot")
        .add_edge("chatbot", END)
        .compile(checkpointer=checkpointer)
    )

    return grafo
