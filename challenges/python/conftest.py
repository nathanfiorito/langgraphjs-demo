import pytest

# Configura pytest-asyncio para modo automático
# (permite usar async def em testes sem @pytest.mark.asyncio explícito)

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
