import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "recipe_finder"

# Наши 20 рецептов
RECIPES = [
    {"name": "Паста Карбонара", "rating": 4.8,
     "ingredients": [{"name": "Макароны", "quantity": 200}, {"name": "Бекон", "quantity": 100},
                     {"name": "Яйцо", "quantity": 2}, {"name": "Сыр", "quantity": 50}]},
    {"name": "Оливье", "rating": 4.9,
     "ingredients": [{"name": "Картофель", "quantity": 4}, {"name": "Морковь", "quantity": 2},
                     {"name": "Яйцо", "quantity": 3}, {"name": "Колбаса", "quantity": 200},
                     {"name": "Горошек", "quantity": 100}, {"name": "Майонез", "quantity": 150}]},
    {"name": "Борщ", "rating": 5.0,
     "ingredients": [{"name": "Свекла", "quantity": 2}, {"name": "Капуста", "quantity": 200},
                     {"name": "Картофель", "quantity": 3}, {"name": "Мясо", "quantity": 500}]},
    {"name": "Омлет с сыром", "rating": 4.2,
     "ingredients": [{"name": "Яйцо", "quantity": 3}, {"name": "Молоко", "quantity": 50},
                     {"name": "Сыр", "quantity": 40}]},
    {"name": "Греческий салат", "rating": 4.7,
     "ingredients": [{"name": "Огурец", "quantity": 2}, {"name": "Помидоры", "quantity": 3},
                     {"name": "Сыр Фета", "quantity": 100}, {"name": "Оливки", "quantity": 50}]},
    {"name": "Куриный суп", "rating": 4.5,
     "ingredients": [{"name": "Курица", "quantity": 500}, {"name": "Картофель", "quantity": 3},
                     {"name": "Морковь", "quantity": 1}, {"name": "Лук", "quantity": 1}]},
    {"name": "Спагетти Болоньезе", "rating": 4.8,
     "ingredients": [{"name": "Макароны", "quantity": 250}, {"name": "Фарш", "quantity": 300},
                     {"name": "Помидоры", "quantity": 2}, {"name": "Лук", "quantity": 1}]},
    {"name": "Блины", "rating": 4.6,
     "ingredients": [{"name": "Мука", "quantity": 200}, {"name": "Молоко", "quantity": 500},
                     {"name": "Яйцо", "quantity": 2}]},
    {"name": "Сырники", "rating": 4.9,
     "ingredients": [{"name": "Творог", "quantity": 400}, {"name": "Яйцо", "quantity": 1},
                     {"name": "Мука", "quantity": 100}]},
    {"name": "Цезарь с курицей", "rating": 4.7,
     "ingredients": [{"name": "Курица", "quantity": 200}, {"name": "Салат Айсберг", "quantity": 1},
                     {"name": "Сухарики", "quantity": 50}, {"name": "Сыр", "quantity": 30}]},
    {"name": "Плов", "rating": 4.8, "ingredients": [{"name": "Рис", "quantity": 300}, {"name": "Мясо", "quantity": 500},
                                                    {"name": "Морковь", "quantity": 2},
                                                    {"name": "Лук", "quantity": 2}]},
    {"name": "Пюре с котлетой", "rating": 4.5,
     "ingredients": [{"name": "Картофель", "quantity": 5}, {"name": "Молоко", "quantity": 100},
                     {"name": "Фарш", "quantity": 300}]},
    {"name": "Творожная запеканка", "rating": 4.6,
     "ingredients": [{"name": "Творог", "quantity": 500}, {"name": "Яйцо", "quantity": 2},
                     {"name": "Манка", "quantity": 50}]},
    {"name": "Грибной крем-суп", "rating": 4.7,
     "ingredients": [{"name": "Шампиньоны", "quantity": 300}, {"name": "Сливки", "quantity": 200},
                     {"name": "Картофель", "quantity": 2}]},
    {"name": "Паста с томатами", "rating": 4.3,
     "ingredients": [{"name": "Макароны", "quantity": 200}, {"name": "Помидоры", "quantity": 4},
                     {"name": "Чеснок", "quantity": 2}]},
    {"name": "Шарлотка", "rating": 4.4,
     "ingredients": [{"name": "Яблоки", "quantity": 3}, {"name": "Мука", "quantity": 200},
                     {"name": "Яйцо", "quantity": 3}]},
    {"name": "Рис с овощами", "rating": 4.1,
     "ingredients": [{"name": "Рис", "quantity": 200}, {"name": "Морковь", "quantity": 1},
                     {"name": "Горошек", "quantity": 100}]},
    {"name": "Сэндвич с тунцом", "rating": 4.2,
     "ingredients": [{"name": "Хлеб", "quantity": 2}, {"name": "Тунец", "quantity": 100},
                     {"name": "Огурец", "quantity": 1}]},
    {"name": "Наггетсы", "rating": 4.0,
     "ingredients": [{"name": "Курица", "quantity": 400}, {"name": "Мука", "quantity": 100},
                     {"name": "Яйцо", "quantity": 1}]},
    {"name": "Фруктовый салат", "rating": 4.8,
     "ingredients": [{"name": "Яблоки", "quantity": 2}, {"name": "Банан", "quantity": 2},
                     {"name": "Апельсин", "quantity": 1}]}
]


async def seed_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Очищаем старые данные (чтобы не было дублей)
    await db.recipes.delete_many({})

    # Форматируем и добавляем ID
    docs = []
    for r in RECIPES:
        r["id"] = str(uuid.uuid4())
        docs.append(r)

    await db.recipes.insert_many(docs)
    print(f"Успешно добавлено {len(docs)} рецептов в MongoDB!")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_db())