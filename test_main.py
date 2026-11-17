'''

''''''
import pytest
from fastapi.testclient import TestClient
from main import app, recipes_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Очищает базу данных перед каждым тестом, чтобы они не влияли друг на друга."""
    recipes_db.clear()
    yield


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_add_recipe():
    response = client.post("/recipes", json={
        "name": "Паста",
        "rating": 4.5,
        "ingredients": [
            {"name": "Макароны", "quantity": 200},
            {"name": "Помидоры", "quantity": 2}
        ]
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Паста"


def test_search_success():
    # Добавляем рецепт
    client.post("/recipes", json={
        "name": "Салат",
        "rating": 5.0,
        "ingredients": [{"name": "Огурец", "quantity": 1}]
    })

    # Ищем с достаточным количеством
    response = client.post("/recipes/search", json=[
        {"name": "огурец", "quantity": 2}
    ])
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Салат"


def test_search_fail_not_enough():
    client.post("/recipes", json={
        "name": "Омлет",
        "rating": 4.0,
        "ingredients": [{"name": "Яйцо", "quantity": 3}]
    })

    response = client.post("/recipes/search", json=[
        {"name": "Яйцо", "quantity": 2}
    ])
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_search_sorting():
    # Добавляем два рецепта с разным рейтингом
    client.post("/recipes",
                json={"name": "Низкий рейтинг", "rating": 2.0, "ingredients": [{"name": "Вода", "quantity": 1}]})
    client.post("/recipes",
                json={"name": "Высокий рейтинг", "rating": 5.0, "ingredients": [{"name": "Вода", "quantity": 1}]})

    response = client.post("/recipes/search", json=[{"name": "Вода", "quantity": 10}])
    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Высокий рейтинг"
    assert data[1]["name"] == "Низкий рейтинг"

def test_search_partial_match_break():
    client.post("/recipes", json={
        "name": "Сложный рецепт",
        "rating": 4.0,
        "ingredients": [
            {"name": "Мука", "quantity": 500},
            {"name": "Сахар", "quantity": 200}
        ]
    })
    response = client.post("/recipes/search", json=[{"name": "Мука", "quantity": 500}])
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_search_mixed_results():
    client.post("/recipes", json={"name": "Вода", "rating": 4.0, "ingredients": [{"name": "Вода", "quantity": 1}]})
    # Рецепт, который НЕ подойдет
    client.post("/recipes", json={"name": "Огонь", "rating": 5.0, "ingredients": [{"name": "Огонь", "quantity": 1}]})

    response = client.post("/recipes/search", json=[{"name": "Вода", "quantity": 5}])

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Вода"


def test_search_strict_break():
    client.post("/recipes", json={
        "name": "Много сахара",
        "rating": 4.0,
        "ingredients": [{"name": "Сахар", "quantity": 100}]
    })

    response = client.post("/recipes/search", json=[{"name": "Сахар", "quantity": 50}])

    assert response.status_code == 200
    assert len(response.json()) == 0


def test_search_complex_recipe_branches():
    client.post("/recipes", json={
        "name": "Сложный рецепт",
        "rating": 4.0,
        "ingredients": [
            {"name": "Мука", "quantity": 500},
            {"name": "Сахар", "quantity": 200}
        ]
    })

    # Сценарий 1: Муки хватает, а сахара вообще нет
    response1 = client.post("/recipes/search", json=[{"name": "Мука", "quantity": 500}])
    assert len(response1.json()) == 0

    # Сценарий 2: Муки хватает, сахар есть, но его мало
    response2 = client.post("/recipes/search", json=[
        {"name": "Мука", "quantity": 500},
        {"name": "Сахар", "quantity": 100}
    ])
    assert len(response2.json()) == 0

    # Сценарий 3: Всего хватает
    response3 = client.post("/recipes/search", json=[
        {"name": "Мука", "quantity": 600},
        {"name": "Сахар", "quantity": 300}
    ])
    assert len(response3.json()) == 1


def test_search_empty_ingredients():
    # Отправляем пустой список ингредиентов
    response = client.post("/recipes/search", json=[])

    # Проверяем, что сервер вернул 400 ошибку
    assert response.status_code == 400
    assert response.json()["detail"] == "Список ингредиентов не может быть пустым"
///

'''
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
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_add_recipe(client):
    response = await client.post("/recipes", json={
        "name": "Паста", "rating": 4.5,
        "ingredients": [{"name": "Макароны", "quantity": 200}],
    })
    assert response.status_code == 201
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_search_success(client):
    await client.post("/recipes", json={
        "name": "Салат", "rating": 5.0,
        "ingredients": [{"name": "Огурец", "quantity": 1}],
    })
    response = await client.post("/recipes/search", json=[{"name": "огурец", "quantity": 2}])
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_search_not_enough(client):
    await client.post("/recipes", json={
        "name": "Омлет", "rating": 4.0,
        "ingredients": [{"name": "Яйцо", "quantity": 3}],
    })
    response = await client.post("/recipes/search", json=[{"name": "Яйцо", "quantity": 2}])
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_search_empty(client):
    response = await client.post("/recipes/search", json=[])
    assert response.status_code == 400
    assert response.json()["detail"] == "Список ингредиентов не может быть пустым"


@pytest.mark.asyncio
async def test_search_sorting(client):
    await client.post("/recipes", json={
        "name": "Низкий", "rating": 2.0,
        "ingredients": [{"name": "Вода", "quantity": 1}],
    })
    await client.post("/recipes", json={
        "name": "Высокий", "rating": 5.0,
        "ingredients": [{"name": "Вода", "quantity": 1}],
    })
    response = await client.post("/recipes/search", json=[{"name": "Вода", "quantity": 10}])
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