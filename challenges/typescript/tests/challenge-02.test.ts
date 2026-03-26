import { describe, it, expect } from "vitest";
import { criarGrafo } from "../challenges/challenge-02.js";

const invocar = async (urgencia: string, tipo: string, titulo = "Teste") => {
  const grafo = criarGrafo();
  return grafo.invoke({ titulo, mensagem: "Mensagem de teste", urgencia, tipo });
};

describe("Desafio 02 — Roteamento de Notificações", () => {
  it("urgente + sistema → canal incidente", async () => {
    const resultado = await invocar("urgente", "sistema");
    expect(resultado.canal).toBe("incidente");
    expect(resultado.enviado).toBe(true);
    expect(resultado.destinatarios.length).toBeGreaterThan(0);
    expect(resultado.timestampEnvio).toBeTruthy();
  });

  it("urgente + negocio → canal escalada", async () => {
    const resultado = await invocar("urgente", "negocio");
    expect(resultado.canal).toBe("escalada");
    expect(resultado.enviado).toBe(true);
  });

  it("urgente + outro → canal urgencia", async () => {
    const resultado = await invocar("urgente", "outro");
    expect(resultado.canal).toBe("urgencia");
    expect(resultado.enviado).toBe(true);
  });

  it("normal + sistema → canal tecnico", async () => {
    const resultado = await invocar("normal", "sistema");
    expect(resultado.canal).toBe("tecnico");
    expect(resultado.enviado).toBe(true);
  });

  it("normal + negocio → canal comercial", async () => {
    const resultado = await invocar("normal", "negocio");
    expect(resultado.canal).toBe("comercial");
    expect(resultado.enviado).toBe(true);
  });

  it("normal + outro → canal padrao", async () => {
    const resultado = await invocar("normal", "outro");
    expect(resultado.canal).toBe("padrao");
    expect(resultado.enviado).toBe(true);
  });

  it("todos os canais marcam enviado=true e têm destinatários", async () => {
    const combinacoes = [
      ["urgente", "sistema"],
      ["urgente", "negocio"],
      ["urgente", "outro"],
      ["normal", "sistema"],
      ["normal", "negocio"],
      ["normal", "outro"],
    ];

    for (const [urgencia, tipo] of combinacoes) {
      const resultado = await invocar(urgencia, tipo);
      expect(resultado.enviado).toBe(true);
      expect(Array.isArray(resultado.destinatarios)).toBe(true);
      expect(resultado.destinatarios.length).toBeGreaterThan(0);
    }
  });
});
