"""
Entry point interativo — chat no terminal.

Uso:
    pip install -r requirements.txt
    cp .env.example .env          # preencha as chaves
    python src/main.py
"""

import asyncio
import os
import uuid

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()

from agent import criar_agente  # noqa: E402 — importar após load_dotenv


def exibir_cabecalho() -> None:
    tracing_ativo = os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true"
    projeto = os.environ.get("LANGCHAIN_PROJECT", "—")
    modelo = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    print("=" * 55)
    print("  Agente Conversacional — LangGraph + OpenRouter")
    print("=" * 55)
    print(f"  Modelo  : {modelo}")
    print(f"  Tracing : {'LangSmith ON  (projeto: ' + projeto + ')' if tracing_ativo else 'desativado'}")
    print("=" * 55)
    print("  Digite 'sair' para encerrar.\n")


async def executar_chat() -> None:
    agente = criar_agente()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    exibir_cabecalho()

    while True:
        try:
            entrada = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            break

        if not entrada:
            continue

        if entrada.lower() in ("sair", "exit", "quit"):
            print("Até logo!")
            break

        resultado = await agente.ainvoke(
            {"messages": [HumanMessage(content=entrada)]},
            config=config,
        )

        resposta = resultado["messages"][-1].content
        print(f"\nAssistente: {resposta}\n")


def main() -> None:
    asyncio.run(executar_chat())


if __name__ == "__main__":
    main()
