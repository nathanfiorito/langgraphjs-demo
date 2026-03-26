import { describe, it, expect } from "vitest";
import { criarGrafo } from "../challenges/challenge-01.js";

describe("Desafio 01 — Pipeline de Pedidos", () => {
  it("processa um pedido válido sem desconto, com frete", async () => {
    const grafo = criarGrafo();
    const resultado = await grafo.invoke({
      itens: [
        { nome: "Teclado", quantidade: 1, precoUnitario: 150 },
        { nome: "Mouse", quantidade: 2, precoUnitario: 80 },
      ],
      codigoDesconto: "",
      erros: [],
      resumo: {},
    });

    expect(resultado.valido).toBe(true);
    expect(resultado.subtotal).toBe(310);      // 150 + 2*80
    expect(resultado.desconto).toBe(0);
    expect(resultado.frete).toBe(0);           // >= 200: frete grátis
    expect(resultado.total).toBe(310);
    expect(resultado.resumo.status).toBe("aprovado");
    expect(resultado.resumo.totalItens).toBe(3); // 1 + 2
  });

  it("processa um pedido válido com desconto DESC10 e frete", async () => {
    const grafo = criarGrafo();
    const resultado = await grafo.invoke({
      itens: [{ nome: "Cabo USB", quantidade: 1, precoUnitario: 50 }],
      codigoDesconto: "DESC10",
      erros: [],
      resumo: {},
    });

    expect(resultado.valido).toBe(true);
    expect(resultado.subtotal).toBe(50);
    expect(resultado.desconto).toBe(5);        // 10% de 50
    expect(resultado.frete).toBe(15);          // < 200: frete fixo
    expect(resultado.total).toBe(60);          // 50 - 5 + 15
    expect(resultado.resumo.status).toBe("aprovado");
  });

  it("processa um pedido válido com desconto DESC20 e frete grátis", async () => {
    const grafo = criarGrafo();
    const resultado = await grafo.invoke({
      itens: [{ nome: "Monitor", quantidade: 1, precoUnitario: 800 }],
      codigoDesconto: "DESC20",
      erros: [],
      resumo: {},
    });

    expect(resultado.valido).toBe(true);
    expect(resultado.subtotal).toBe(800);
    expect(resultado.desconto).toBe(160);      // 20% de 800
    expect(resultado.frete).toBe(0);           // >= 200: grátis
    expect(resultado.total).toBe(640);         // 800 - 160 + 0
  });

  it("rejeita pedido com lista de itens vazia", async () => {
    const grafo = criarGrafo();
    const resultado = await grafo.invoke({
      itens: [],
      codigoDesconto: "",
      erros: [],
      resumo: {},
    });

    expect(resultado.valido).toBe(false);
    expect(resultado.erros.length).toBeGreaterThan(0);
    expect(resultado.resumo.status).toBe("rejeitado");
  });

  it("rejeita pedido com item de quantidade zero", async () => {
    const grafo = criarGrafo();
    const resultado = await grafo.invoke({
      itens: [{ nome: "Produto Inválido", quantidade: 0, precoUnitario: 100 }],
      codigoDescunto: "",
      erros: [],
      resumo: {},
    });

    expect(resultado.valido).toBe(false);
    expect(resultado.erros.length).toBeGreaterThan(0);
  });

  it("acumula erros de múltiplos itens inválidos", async () => {
    const grafo = criarGrafo();
    const resultado = await grafo.invoke({
      itens: [
        { nome: "Item A", quantidade: 0, precoUnitario: 10 },
        { nome: "Item B", quantidade: 1, precoUnitario: -5 },
      ],
      codigoDesconto: "",
      erros: [],
      resumo: {},
    });

    expect(resultado.valido).toBe(false);
    // Deve ter pelo menos 1 erro para cada item inválido
    expect(resultado.erros.length).toBeGreaterThanOrEqual(2);
  });

  it("o campo resumo acumula dados de múltiplos nós (merge)", async () => {
    const grafo = criarGrafo();
    const resultado = await grafo.invoke({
      itens: [{ nome: "Produto", quantidade: 2, precoUnitario: 100 }],
      codigoDesconto: "",
      erros: [],
      resumo: {},
    });

    // O resumo deve ter campos de múltiplos nós (calcular + formatar)
    expect(resultado.resumo).toHaveProperty("subtotal");
    expect(resultado.resumo).toHaveProperty("desconto");
    expect(resultado.resumo).toHaveProperty("frete");
    expect(resultado.resumo).toHaveProperty("total");
    expect(resultado.resumo).toHaveProperty("status");
    expect(resultado.resumo).toHaveProperty("totalItens");
  });
});
