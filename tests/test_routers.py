import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_check(ac: AsyncClient):
    response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "detail": "ok",
        "result": "working",
    }
