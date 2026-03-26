import pytest
from challenges.challenge_01 import criar_grafo


@pytest.fixture
def grafo():
    return criar_grafo()


def test_pedido_valido_sem_desconto_com_frete_gratis(grafo):
    resultado = grafo.invoke({
        "itens": [
            {"nome": "Teclado", "quantidade": 1, "preco_unitario": 150},
            {"nome": "Mouse", "quantidade": 2, "preco_unitario": 80},
        ],
        "codigo_desconto": "",
        "erros": [],
        "resumo": {},
    })

    assert resultado["valido"] is True
    assert resultado["subtotal"] == 310       # 150 + 2*80
    assert resultado["desconto"] == 0
    assert resultado["frete"] == 0            # >= 200: frete grátis
    assert resultado["total"] == 310
    assert resultado["resumo"]["status"] == "aprovado"
    assert resultado["resumo"]["total_itens"] == 3  # 1 + 2


def test_pedido_valido_com_desc10_e_frete(grafo):
    resultado = grafo.invoke({
        "itens": [{"nome": "Cabo USB", "quantidade": 1, "preco_unitario": 50}],
        "codigo_desconto": "DESC10",
        "erros": [],
        "resumo": {},
    })

    assert resultado["valido"] is True
    assert resultado["subtotal"] == 50
    assert resultado["desconto"] == 5         # 10% de 50
    assert resultado["frete"] == 15           # < 200: frete fixo
    assert resultado["total"] == 60           # 50 - 5 + 15
    assert resultado["resumo"]["status"] == "aprovado"


def test_pedido_valido_com_desc20_e_frete_gratis(grafo):
    resultado = grafo.invoke({
        "itens": [{"nome": "Monitor", "quantidade": 1, "preco_unitario": 800}],
        "codigo_desconto": "DESC20",
        "erros": [],
        "resumo": {},
    })

    assert resultado["valido"] is True
    assert resultado["subtotal"] == 800
    assert resultado["desconto"] == 160       # 20% de 800
    assert resultado["frete"] == 0
    assert resultado["total"] == 640          # 800 - 160 + 0


def test_rejeita_pedido_sem_itens(grafo):
    resultado = grafo.invoke({
        "itens": [],
        "codigo_desconto": "",
        "erros": [],
        "resumo": {},
    })

    assert resultado["valido"] is False
    assert len(resultado["erros"]) > 0
    assert resultado["resumo"]["status"] == "rejeitado"


def test_rejeita_item_com_quantidade_zero(grafo):
    resultado = grafo.invoke({
        "itens": [{"nome": "Produto Inválido", "quantidade": 0, "preco_unitario": 100}],
        "codigo_desconto": "",
        "erros": [],
        "resumo": {},
    })

    assert resultado["valido"] is False
    assert len(resultado["erros"]) > 0


def test_acumula_erros_de_multiplos_itens_invalidos(grafo):
    resultado = grafo.invoke({
        "itens": [
            {"nome": "Item A", "quantidade": 0, "preco_unitario": 10},
            {"nome": "Item B", "quantidade": 1, "preco_unitario": -5},
        ],
        "codigo_desconto": "",
        "erros": [],
        "resumo": {},
    })

    assert resultado["valido"] is False
    assert len(resultado["erros"]) >= 2


def test_resumo_acumula_dados_de_multiplos_nos(grafo):
    resultado = grafo.invoke({
        "itens": [{"nome": "Produto", "quantidade": 2, "preco_unitario": 100}],
        "codigo_desconto": "",
        "erros": [],
        "resumo": {},
    })

    # O resumo deve ter campos de múltiplos nós (calcular + formatar)
    assert "subtotal" in resultado["resumo"]
    assert "desconto" in resultado["resumo"]
    assert "frete" in resultado["resumo"]
    assert "total" in resultado["resumo"]
    assert "status" in resultado["resumo"]
    assert "total_itens" in resultado["resumo"]
