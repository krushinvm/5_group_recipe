import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
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

@pytest.mark.asyncio
async def test_add_recipe(client):
    response = await client.post("/recipes", json={
        "name": "Паста", "rating": 4.5,
        "ingredients": [{"name": "Макароны", "quantity": 200, "unit": "г"}],
    })
    assert response.status_code == 201
    assert "id" in response.json()

@pytest.mark.asyncio
async def test_search_success(client):
    await client.post("/recipes", json={
        "name": "Салат", "rating": 5.0,
        "ingredients": [{"name": "Огурец", "quantity": 1, "unit": "шт"}],
    })
    response = await client.post("/recipes/search", json=[{"name": "огурец", "quantity": 2, "unit": "шт"}])
    assert response.status_code == 200
    assert len(response.json()) == 1

@pytest.mark.asyncio
async def test_search_partial_match(client):
    await client.post("/recipes", json={
        "name": "Омлет", "rating": 4.0,
        "ingredients": [{"name": "Яйцо", "quantity": 3, "unit": "шт"}],
    })
    response = await client.post("/recipes/search", json=[{"name": "Яйцо", "quantity": 2, "unit": "шт"}])
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Омлет"

@pytest.mark.asyncio
async def test_search_empty(client):
    response = await client.post("/recipes/search", json=[])
    assert response.status_code == 400
    assert response.json()["detail"] == "Список ингредиентов не может быть пустым"

@pytest.mark.asyncio
async def test_search_sorting(client):
    await client.post("/recipes", json={
        "name": "Низкий", "rating": 2.0,
        "ingredients": [{"name": "Вода", "quantity": 1, "unit": "л"}],
    })
    await client.post("/recipes", json={
        "name": "Высокий", "rating": 5.0,
        "ingredients": [{"name": "Вода", "quantity": 1, "unit": "л"}],
    })
    response = await client.post("/recipes/search", json=[{"name": "Вода", "quantity": 10, "unit": "л"}])
    data = response.json()
    assert data[0]["name"] == "Высокий"
    assert data[1]["name"] == "Низкий"

@pytest.mark.asyncio
async def test_add_recipe_validation(client):
    response = await client.post("/recipes", json={
        "name": "", "rating": 10,
        "ingredients": [],
    })
    assert response.status_code == 422