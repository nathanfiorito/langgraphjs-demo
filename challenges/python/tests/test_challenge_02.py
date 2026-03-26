import pytest
from challenges.challenge_02 import criar_grafo


@pytest.fixture
def grafo():
    return criar_grafo()


def invocar(grafo, urgencia: str, tipo: str, titulo: str = "Teste"):
    return grafo.invoke({
        "titulo": titulo,
        "mensagem": "Mensagem de teste",
        "urgencia": urgencia,
        "tipo": tipo,
    })


def test_urgente_sistema_vai_para_incidente(grafo):
    resultado = invocar(grafo, "urgente", "sistema")
    assert resultado["canal"] == "incidente"
    assert resultado["enviado"] is True
    assert len(resultado["destinatarios"]) > 0
    assert resultado["timestamp_envio"]


def test_urgente_negocio_vai_para_escalada(grafo):
    resultado = invocar(grafo, "urgente", "negocio")
    assert resultado["canal"] == "escalada"
    assert resultado["enviado"] is True


def test_urgente_outro_vai_para_urgencia(grafo):
    resultado = invocar(grafo, "urgente", "outro")
    assert resultado["canal"] == "urgencia"
    assert resultado["enviado"] is True


def test_normal_sistema_vai_para_tecnico(grafo):
    resultado = invocar(grafo, "normal", "sistema")
    assert resultado["canal"] == "tecnico"
    assert resultado["enviado"] is True


def test_normal_negocio_vai_para_comercial(grafo):
    resultado = invocar(grafo, "normal", "negocio")
    assert resultado["canal"] == "comercial"
    assert resultado["enviado"] is True


def test_normal_outro_vai_para_padrao(grafo):
    resultado = invocar(grafo, "normal", "outro")
    assert resultado["canal"] == "padrao"
    assert resultado["enviado"] is True


def test_todos_canais_tem_enviado_e_destinatarios(grafo):
    combinacoes = [
        ("urgente", "sistema"),
        ("urgente", "negocio"),
        ("urgente", "outro"),
        ("normal", "sistema"),
        ("normal", "negocio"),
        ("normal", "outro"),
    ]

    for urgencia, tipo in combinacoes:
        resultado = invocar(grafo, urgencia, tipo)
        assert resultado["enviado"] is True, f"Falhou para {urgencia}+{tipo}"
        assert isinstance(resultado["destinatarios"], list), f"Falhou para {urgencia}+{tipo}"
        assert len(resultado["destinatarios"]) > 0, f"Falhou para {urgencia}+{tipo}"
