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

    # Ищем с достаточным количеством (и проверяем регистронезависимость)
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

    # Даем только 2 яйца вместо 3
    response = client.post("/recipes/search", json=[
        {"name": "Яйцо", "quantity": 2}
    ])
    assert response.status_code == 200
    assert len(response.json()) == 0  # Рецепт не должен подойти


def test_search_sorting():
    # Добавляем два рецепта с разным рейтингом
    client.post("/recipes",
                json={"name": "Низкий рейтинг", "rating": 2.0, "ingredients": [{"name": "Вода", "quantity": 1}]})
    client.post("/recipes",
                json={"name": "Высокий рейтинг", "rating": 5.0, "ingredients": [{"name": "Вода", "quantity": 1}]})

    response = client.post("/recipes/search", json=[{"name": "Вода", "quantity": 10}])
    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Высокий рейтинг"  # Должен быть первым
    assert data[1]["name"] == "Низкий рейтинг"

def test_search_partial_match_break():
    # Добавляем рецепт с ДВУМЯ ингредиентами
    client.post("/recipes", json={
        "name": "Сложный рецепт",
        "rating": 4.0,
        "ingredients": [
            {"name": "Мука", "quantity": 500},
            {"name": "Сахар", "quantity": 200}
        ]
    })
    # Пользователь дает муку, но НЕ ДАЕТ сахар.
    # Код должен прервать проверку (break) на сахаре.
    response = client.post("/recipes/search", json=[{"name": "Мука", "quantity": 500}])
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_search_mixed_results():
    # Рецепт, который подойдет
    client.post("/recipes", json={"name": "Вода", "rating": 4.0, "ingredients": [{"name": "Вода", "quantity": 1}]})
    # Рецепт, который НЕ подойдет
    client.post("/recipes", json={"name": "Огонь", "rating": 5.0, "ingredients": [{"name": "Огонь", "quantity": 1}]})

    # Ищем, имея только воду
    response = client.post("/recipes/search", json=[{"name": "Вода", "quantity": 5}])

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Вода"


def test_search_strict_break():
    # Добавляем рецепт, где ИМЕННО КОЛИЧЕСТВА не хватает (чтобы сработала вторая часть условия)
    client.post("/recipes", json={
        "name": "Много сахара",
        "rating": 4.0,
        "ingredients": [{"name": "Сахар", "quantity": 100}]
    })

    # Даем сахар, но мало (50 вместо 100)
    response = client.post("/recipes/search", json=[{"name": "Сахар", "quantity": 50}])

    # Проверяем, что рецепт не подошел
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_search_complex_recipe_branches():
    # Добавляем сложный рецепт из двух ингредиентов
    client.post("/recipes", json={
        "name": "Сложный рецепт",
        "rating": 4.0,
        "ingredients": [
            {"name": "Мука", "quantity": 500},
            {"name": "Сахар", "quantity": 200}
        ]
    })

    # Сценарий 1: Муки хватает, а сахара вообще нет (сработает 1-я часть условия)
    response1 = client.post("/recipes/search", json=[{"name": "Мука", "quantity": 500}])
    assert len(response1.json()) == 0

    # Сценарий 2: Муки хватает, сахар есть, но его мало (сработает 2-я часть условия)
    response2 = client.post("/recipes/search", json=[
        {"name": "Мука", "quantity": 500},
        {"name": "Сахар", "quantity": 100}
    ])
    assert len(response2.json()) == 0

    # Сценарий 3: Всего хватает (успешный сценарий)
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