import { describe, it, expect, vi } from "vitest";
import {
  criarGrafo,
  SupervisorInterface,
  Estado,
  ProximoAgente,
} from "../challenges/challenge-04.js";

// ─────────────────────────────────────────────
// MOCKS DE SUPERVISOR
// ─────────────────────────────────────────────

// Supervisor "correto": toma decisões na ordem certa
function criarSupervisorCorreto(): SupervisorInterface {
  const sequencia: ProximoAgente[] = ["revisor", "formatador", "publicador"];
  let i = 0;

  return {
    async decidir(_estado: Estado) {
      const proximo = sequencia[Math.min(i++, sequencia.length - 1)];
      return { proximo, motivo: `Passo ${i} da sequência` };
    },
  };
}

// Supervisor "malicioso": tenta pular etapas
function criarSupervisorMalicioso(): SupervisorInterface {
  return {
    async decidir(_estado: Estado) {
      // Sempre tenta ir para publicador (pula revisor e formatador)
      return { proximo: "publicador", motivo: "Tentando pular etapas" };
    },
  };
}

// Supervisor configurável para testes específicos
function criarSupervisorSequencia(sequencia: ProximoAgente[]): SupervisorInterface {
  let i = 0;
  return {
    async decidir(_estado: Estado) {
      const proximo = sequencia[Math.min(i++, sequencia.length - 1)];
      return { proximo, motivo: `Decisão ${i}` };
    },
  };
}

// ─────────────────────────────────────────────
// TESTES
// ─────────────────────────────────────────────

describe("Desafio 04 — Orquestrador com Guardrails", () => {
  const threadConfig = { configurable: { thread_id: "test-001" } };

  it("completa o pipeline na ordem correta: revisor → formatador → publicador", async () => {
    const grafo = criarGrafo(criarSupervisorCorreto());
    const resultado = await grafo.invoke(
      { conteudoOriginal: "Artigo sobre LangGraph", historico: [] },
      threadConfig
    );

    expect(resultado.revisao).toBeTruthy();
    expect(resultado.formatacao).toBeTruthy();
    expect(resultado.publicado).toBe(true);
    expect(resultado.urlPublicacao).toBeTruthy();
  });

  it("guardrail corrige supervisor que tenta pular para publicador sem revisar", async () => {
    const consoleSpy = vi.spyOn(console, "log");

    const grafo = criarGrafo(criarSupervisorMalicioso());
    const resultado = await grafo.invoke(
      { conteudoOriginal: "Artigo teste", historico: [] },
      { configurable: { thread_id: "test-malicioso" } }
    );

    // Mesmo com supervisor malicioso, o pipeline deve completar na ordem certa
    expect(resultado.revisao).toBeTruthy();
    expect(resultado.formatacao).toBeTruthy();
    expect(resultado.publicado).toBe(true);

    // Verifica que o guardrail foi acionado (deve ter logado um aviso)
    const logsGuardrail = consoleSpy.mock.calls
      .flat()
      .filter((arg) => String(arg).includes("Guardrail") || String(arg).includes("⚠️"));
    expect(logsGuardrail.length).toBeGreaterThan(0);

    consoleSpy.mockRestore();
  });

  it("guardrail impede ir para formatador sem revisão", async () => {
    // Supervisor tenta formatador → publicador sem revisar
    const grafo = criarGrafo(
      criarSupervisorSequencia(["formatador", "publicador", "publicador"])
    );
    const resultado = await grafo.invoke(
      { conteudoOriginal: "Artigo", historico: [] },
      { configurable: { thread_id: "test-sem-revisao" } }
    );

    // Mesmo assim, deve ter revisão no final
    expect(resultado.revisao).toBeTruthy();
    expect(resultado.formatacao).toBeTruthy();
    expect(resultado.publicado).toBe(true);
  });

  it("o histórico acumula todas as etapas", async () => {
    const grafo = criarGrafo(criarSupervisorCorreto());
    const resultado = await grafo.invoke(
      { conteudoOriginal: "Artigo com histórico", historico: [] },
      { configurable: { thread_id: "test-historico" } }
    );

    // Deve ter pelo menos 3 entradas (uma por agente)
    expect(resultado.historico.length).toBeGreaterThanOrEqual(3);
  });

  it("persiste estado entre invocações via checkpointer", async () => {
    const grafo = criarGrafo(criarSupervisorCorreto());
    const config = { configurable: { thread_id: "test-persistencia" } };

    // Primeira invocação — completa o pipeline
    await grafo.invoke(
      { conteudoOriginal: "Primeiro artigo", historico: [] },
      config
    );

    // Recupera o estado salvo pelo checkpointer
    const estadoSalvo = await grafo.getState(config);

    // O estado deve persistir com os dados da execução
    expect(estadoSalvo.values).toBeDefined();
    expect((estadoSalvo.values as Estado).publicado).toBe(true);
  });
});
