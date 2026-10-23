from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import uuid

app = FastAPI(
    title="Recipe Finder API",
    description="Сервис для добавления рецептов и подбора блюд по ингредиентам",
    version="1.0.0"
)


# --- Модели данных (Pydantic) ---

class Ingredient(BaseModel):
    name: str = Field(..., min_length=1, description="Название продукта")
    quantity: float = Field(..., gt=0, description="Количество (вес, штуки и т.д.)")


class RecipeCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Название рецепта")
    rating: float = Field(..., ge=0, le=5, description="Рейтинг от 0 до 5")
    ingredients: List[Ingredient] = Field(..., min_length=1, description="Список необходимых ингредиентов")


class Recipe(RecipeCreate):
    id: str = Field(..., description="Уникальный идентификатор рецепта")


# --- In-memory база данных ---
recipes_db: List[Recipe] = []


# --- Эндпоинты ---

@app.get("/", summary="Проверка работы сервера")
def root():
    return {"status": "ok", "message": "Recipe Finder API is running"}


@app.post("/recipes", response_model=Recipe, status_code=201, summary="Добавить рецепт")
def add_recipe(recipe: RecipeCreate):
    """
    Принимает название, рейтинг и список ингредиентов.
    Возвращает созданный рецепт с присвоенным UUID.
    """
    new_recipe = Recipe(
        id=str(uuid.uuid4()),
        name=recipe.name,
        rating=recipe.rating,
        ingredients=recipe.ingredients
    )
    recipes_db.append(new_recipe)
    return new_recipe


@app.post("/recipes/search", response_model=List[Recipe], summary="Подобрать рецепты")
def search_recipes(user_ingredients: List[Ingredient]):
    """
    Принимает список продуктов, которые есть у пользователя.
    Возвращает подходящие рецепты, отсортированные по убыванию рейтинга.
    """
    if not user_ingredients:
        raise HTTPException(status_code=400, detail="Список ингредиентов не может быть пустым")

    # Приводим ингредиенты пользователя к словарю для быстрого поиска (без учета регистра)
    user_dict = {ing.name.strip().lower(): ing.quantity for ing in user_ingredients}
    suitable_recipes = []

    for recipe in recipes_db:
        can_cook = True
        for req_ing in recipe.ingredients:
            req_name = req_ing.name.strip().lower()
            # Если ингредиента нет или его количество меньше требуемого
            if req_name not in user_dict or user_dict[req_name] < req_ing.quantity:
                can_cook = False
                break

        if can_cook:
            suitable_recipes.append(recipe)

    # Сортировка по рейтингу (от большего к меньшему)
    suitable_recipes.sort(key=lambda x: x.rating, reverse=True)
    return suitable_recipes