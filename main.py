import os
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_finder")


class Ingredient(BaseModel):
    name: str = Field(..., min_length=1, description="Название продукта")
    quantity: float = Field(..., gt=0, description="Количество")


class RecipeCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Название рецепта")
    rating: float = Field(..., ge=0, le=5, description="Рейтинг от 0 до 5")
    ingredients: List[Ingredient] = Field(..., min_items=1)


class Recipe(RecipeCreate):
    id: str = Field(..., description="Уникальный идентификатор")


class Mongo:
    client: AsyncIOMotorClient | None = None
    db = None


mongo = Mongo()


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo.client = AsyncIOMotorClient(MONGO_URL)
    mongo.db = mongo.client[DB_NAME]
    await mongo.db.recipes.create_index("rating")
    yield
    mongo.client.close()


app = FastAPI(
    title="Recipe Finder API",
    description="Сервис для добавления рецептов и подбора блюд по ингредиентам",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", summary="Проверка работы сервера и БД")
async def root():
    try:
        await mongo.db.recipes.find_one({})
        return {"status": "ok", "db": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="База данных недоступна")


@app.post("/recipes", response_model=Recipe, status_code=201, summary="Добавить рецепт")
async def add_recipe(recipe: RecipeCreate):
    new_recipe = {
        "id": str(uuid.uuid4()),
        "name": recipe.name,
        "rating": recipe.rating,
        "ingredients": [ing.model_dump() for ing in recipe.ingredients],
    }
    await mongo.db.recipes.insert_one(new_recipe)
    return new_recipe


@app.post("/recipes/search", response_model=List[Recipe], summary="Подобрать рецепты")
async def search_recipes(user_ingredients: List[Ingredient]):
    if not user_ingredients:
        raise HTTPException(status_code=400, detail="Список ингредиентов не может быть пустым")

    user_dict = {ing.name.strip().lower(): ing.quantity for ing in user_ingredients}
    suitable = []

    cursor = mongo.db.recipes.find({}, {"_id": 0})
    async for doc in cursor:
        can_cook = True
        for req in doc["ingredients"]:
            req_name = req["name"].strip().lower()
            if req_name not in user_dict or user_dict[req_name] < req["quantity"]:
                can_cook = False
                break
        if can_cook:
            suitable.append(doc)

    suitable.sort(key=lambda x: x["rating"], reverse=True)
    return suitable