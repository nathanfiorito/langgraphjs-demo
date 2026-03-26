# Challenges — Desafios Práticos de LangGraph

Quatro desafios progressivos para consolidar o aprendizado dos módulos de estudo.

## Como Usar

Cada desafio é um arquivo com:
- **Esqueleto** — estrutura pronta com `TODO`s marcando o que implementar
- **Testes** — validam automaticamente se sua implementação está correta

**Workflow recomendado:**
1. Leia o enunciado no arquivo do desafio
2. Implemente os `TODO`s
3. Rode os testes para validar
4. Se todos passarem, o desafio está completo!

---

## TypeScript

```bash
cd typescript
npm install
npm test           # Roda todos os desafios
npm run test:watch # Modo watch (recarrega ao salvar)
```

## Python

```bash
cd python
pip install -r requirements.txt
pytest             # Roda todos os desafios
pytest -v          # Modo verbose (mostra cada teste)
pytest tests/test_challenge_01.py  # Roda apenas um desafio
```

---

## Desafios

### Desafio 01 — Construa seu Pipeline
**Módulos:** 01, 02 | **Sem LLM**

Construa um pipeline de processamento de pedidos de e-commerce com:
- Estado com múltiplos tipos de reducer (lista acumulativa + merge de dict)
- 3 nós: `validar`, `calcular`, `formatar`
- Lógica de desconto e frete

**Arquivos:**
- TypeScript: `typescript/challenges/challenge-01.ts` + `typescript/tests/challenge-01.test.ts`
- Python: `python/challenges/challenge_01.py` + `python/tests/test_challenge_01.py`

---

### Desafio 02 — Roteamento Inteligente
**Módulos:** 03 | **Sem LLM**

Implemente um sistema de roteamento de notificações com:
- 6 canais de destino baseados em 2 critérios (urgência + tipo)
- Função de roteamento com `addConditionalEdges`
- Todos os caminhos convergindo para um nó de registro

**Arquivos:**
- TypeScript: `typescript/challenges/challenge-02.ts` + `typescript/tests/challenge-02.test.ts`
- Python: `python/challenges/challenge_02.py` + `python/tests/test_challenge_02.py`

---

### Desafio 03 — Ciclo ReAct Manual
**Módulos:** 04 | **LLM mockado (testes) + 🎯 Bônus com Claude real**

Implemente o loop ReAct com:
- Estado baseado em `BaseMessage[]` com `add_messages`
- Nó agente que chama o LLM
- Loop condicional: agente → ferramentas → agente → ...
- Ferramentas matemáticas prontas (somar, multiplicar, potência)

**Testes:** Usam LLM mockado — sem custo de API.
**Bônus:** Substitua o mock pelo Claude real e teste com perguntas livres.

**Arquivos:**
- TypeScript: `typescript/challenges/challenge-03.ts` + `typescript/tests/challenge-03.test.ts`
- Python: `python/challenges/challenge_03.py` + `python/tests/test_challenge_03.py`

---

### Desafio 04 — Orquestrador com Guardrails
**Módulos:** 05, 06 | **Supervisor mockado (testes) + 🎯 Bônus com Claude real**

Implemente um pipeline de publicação de artigos com:
- Padrão supervisor com 3 agentes especializados
- **Guardrails determinísticos** que corrigem decisões erradas do supervisor
- Checkpointer (`MemorySaver`) para persistência entre execuções
- Testes que verificam tanto o fluxo correto quanto a correção pelo guardrail

**Testes:** Supervisor mockado que tenta tomar decisões erradas — o guardrail deve corrigi-las.
**Bônus:** Use Claude real como supervisor com `with_structured_output`.

**Arquivos:**
- TypeScript: `typescript/challenges/challenge-04.ts` + `typescript/tests/challenge-04.test.ts`
- Python: `python/challenges/challenge_04.py` + `python/tests/test_challenge_04.py`

---

## Dicas Gerais

- Releia o módulo correspondente antes de começar cada desafio
- Os testes são a fonte da verdade — leia-os para entender o comportamento esperado
- Use `console.log` / `print` livremente para debugar
- Não modifique os arquivos de teste
