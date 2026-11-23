import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from main import app, mongo


@pytest_asyncio.fixture(autouse=True)
async def setup_mongo():
    mongo.client = AsyncMongoMockClient()
    mongo.db = mongo.client["test_db"]
    yield
    mongo.client.close()
    mongo.client = None
    mongo.db = None


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_add_recipe(client):
    response = await client.post(
        "/recipes",
        json={
            "name": "Паста",
            "rating": 4.5,
            "ingredients": [
                {"name": "Макароны", "quantity": 200, "unit": "г"}
            ],
            "instructions": "Отварите макароны в подсоленной воде 8 минут.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["instructions"] == (
        "Отварите макароны в подсоленной воде 8 минут."
    )


@pytest.mark.asyncio
async def test_add_recipe_default_instructions(client):
    response = await client.post(
        "/recipes",
        json={
            "name": "Тост",
            "rating": 4.0,
            "ingredients": [{"name": "Хлеб", "quantity": 2, "unit": "шт"}],
        },
    )
    assert response.status_code == 201
    assert response.json()["instructions"] == (
        "Инструкция по приготовлению не указана."
    )


@pytest.mark.asyncio
async def test_get_recipes_by_name(client):
    await client.post(
        "/recipes",
        json={
            "name": "Пицца 4 сыра",
            "rating": 4.8,
            "ingredients": [{"name": "Тесто", "quantity": 200, "unit": "г"}],
            "instructions": "Раскатайте тесто, добавьте сыры и запеките.",
        },
    )
    await client.post(
        "/recipes",
        json={
            "name": "Борщ",
            "rating": 5.0,
            "ingredients": [{"name": "Свекла", "quantity": 2, "unit": "шт"}],
            "instructions": "Сварите бульон и добавьте овощи.",
        },
    )

    response = await client.get("/recipes", params={"name": "пиц"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Пицца 4 сыра"


@pytest.mark.asyncio
async def test_search_success(client):
    await client.post(
        "/recipes",
        json={
            "name": "Салат",
            "rating": 5.0,
            "ingredients": [{"name": "Огурец", "quantity": 1, "unit": "шт"}],
            "instructions": "Нарежьте огурец и заправьте маслом.",
        },
    )
    response = await client.post(
        "/recipes/search",
        json=[{"name": "огурец", "quantity": 2, "unit": "шт"}],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["instructions"] == "Нарежьте огурец и заправьте маслом."


@pytest.mark.asyncio
async def test_search_partial_match(client):
    await client.post(
        "/recipes",
        json={
            "name": "Омлет",
            "rating": 4.0,
            "ingredients": [{"name": "Яйцо", "quantity": 3, "unit": "шт"}],
            "instructions": "Взбейте яйца и пожарьте на сковороде.",
        },
    )
    response = await client.post(
        "/recipes/search",
        json=[{"name": "Яйцо", "quantity": 2, "unit": "шт"}],
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Омлет"


@pytest.mark.asyncio
async def test_search_empty(client):
    response = await client.post("/recipes/search", json=[])
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Список ингредиентов не может быть пустым"
    )


@pytest.mark.asyncio
async def test_search_sorting(client):
    await client.post(
        "/recipes",
        json={
            "name": "Низкий",
            "rating": 2.0,
            "ingredients": [{"name": "Вода", "quantity": 1, "unit": "л"}],
        },
    )
    await client.post(
        "/recipes",
        json={
            "name": "Высокий",
            "rating": 5.0,
            "ingredients": [{"name": "Вода", "quantity": 1, "unit": "л"}],
        },
    )
    response = await client.post(
        "/recipes/search",
        json=[{"name": "Вода", "quantity": 10, "unit": "л"}],
    )
    data = response.json()
    assert data[0]["name"] == "Высокий"
    assert data[1]["name"] == "Низкий"


@pytest.mark.asyncio
async def test_add_recipe_validation(client):
    response = await client.post(
        "/recipes",
        json={
            "name": "",
            "rating": 10,
            "ingredients": [],
        },
    )
    assert response.status_code == 422