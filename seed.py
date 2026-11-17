import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "recipe_finder"

RECIPES = [
    {"name": "Паста Карбонара", "rating": 4.8, "ingredients": [{"name": "Макароны", "quantity": 200, "unit": "г"},
                                                               {"name": "Бекон", "quantity": 100, "unit": "г"},
                                                               {"name": "Яйцо", "quantity": 2, "unit": "шт"},
                                                               {"name": "Сыр", "quantity": 50, "unit": "г"}]},
    {"name": "Оливье", "rating": 4.9, "ingredients": [{"name": "Картофель", "quantity": 4, "unit": "шт"},
                                                      {"name": "Морковь", "quantity": 2, "unit": "шт"},
                                                      {"name": "Яйцо", "quantity": 3, "unit": "шт"},
                                                      {"name": "Колбаса", "quantity": 200, "unit": "г"},
                                                      {"name": "Горошек", "quantity": 100, "unit": "г"},
                                                      {"name": "Майонез", "quantity": 150, "unit": "г"}]},
    {"name": "Борщ", "rating": 5.0,
     "ingredients": [{"name": "Свекла", "quantity": 2, "unit": "шт"}, {"name": "Капуста", "quantity": 200, "unit": "г"},
                     {"name": "Картофель", "quantity": 3, "unit": "шт"},
                     {"name": "Мясо", "quantity": 500, "unit": "г"}]},
    {"name": "Омлет с сыром", "rating": 4.2,
     "ingredients": [{"name": "Яйцо", "quantity": 3, "unit": "шт"}, {"name": "Молоко", "quantity": 50, "unit": "мл"},
                     {"name": "Сыр", "quantity": 40, "unit": "г"}]},
    {"name": "Греческий салат", "rating": 4.7,
     "ingredients": [{"name": "Огурец", "quantity": 2, "unit": "шт"}, {"name": "Помидоры", "quantity": 3, "unit": "шт"},
                     {"name": "Сыр Фета", "quantity": 100, "unit": "г"},
                     {"name": "Оливки", "quantity": 50, "unit": "г"}]},
    {"name": "Куриный суп", "rating": 4.5, "ingredients": [{"name": "Курица", "quantity": 500, "unit": "г"},
                                                           {"name": "Картофель", "quantity": 3, "unit": "шт"},
                                                           {"name": "Морковь", "quantity": 1, "unit": "шт"},
                                                           {"name": "Лук", "quantity": 1, "unit": "шт"}]},
    {"name": "Спагетти Болоньезе", "rating": 4.8,
     "ingredients": [{"name": "Макароны", "quantity": 250, "unit": "г"}, {"name": "Фарш", "quantity": 300, "unit": "г"},
                     {"name": "Помидоры", "quantity": 2, "unit": "шт"}, {"name": "Лук", "quantity": 1, "unit": "шт"}]},
    {"name": "Блины", "rating": 4.6,
     "ingredients": [{"name": "Мука", "quantity": 200, "unit": "г"}, {"name": "Молоко", "quantity": 500, "unit": "мл"},
                     {"name": "Яйцо", "quantity": 2, "unit": "шт"}]},
    {"name": "Сырники", "rating": 4.9,
     "ingredients": [{"name": "Творог", "quantity": 400, "unit": "г"}, {"name": "Яйцо", "quantity": 1, "unit": "шт"},
                     {"name": "Мука", "quantity": 100, "unit": "г"}]},
    {"name": "Цезарь с курицей", "rating": 4.7, "ingredients": [{"name": "Курица", "quantity": 200, "unit": "г"},
                                                                {"name": "Салат Айсберг", "quantity": 1, "unit": "шт"},
                                                                {"name": "Сухарики", "quantity": 50, "unit": "г"},
                                                                {"name": "Сыр", "quantity": 30, "unit": "г"}]},
    {"name": "Плов", "rating": 4.8,
     "ingredients": [{"name": "Рис", "quantity": 300, "unit": "г"}, {"name": "Мясо", "quantity": 500, "unit": "г"},
                     {"name": "Морковь", "quantity": 2, "unit": "шт"}, {"name": "Лук", "quantity": 2, "unit": "шт"}]},
    {"name": "Пюре с котлетой", "rating": 4.5, "ingredients": [{"name": "Картофель", "quantity": 5, "unit": "шт"},
                                                               {"name": "Молоко", "quantity": 100, "unit": "мл"},
                                                               {"name": "Фарш", "quantity": 300, "unit": "г"}]},
    {"name": "Творожная запеканка", "rating": 4.6,
     "ingredients": [{"name": "Творог", "quantity": 500, "unit": "г"}, {"name": "Яйцо", "quantity": 2, "unit": "шт"},
                     {"name": "Манка", "quantity": 50, "unit": "г"}]},
    {"name": "Грибной крем-суп", "rating": 4.7, "ingredients": [{"name": "Шампиньоны", "quantity": 300, "unit": "г"},
                                                                {"name": "Сливки", "quantity": 200, "unit": "мл"},
                                                                {"name": "Картофель", "quantity": 2, "unit": "шт"}]},
    {"name": "Паста с томатами", "rating": 4.3, "ingredients": [{"name": "Макароны", "quantity": 200, "unit": "г"},
                                                                {"name": "Помидоры", "quantity": 4, "unit": "шт"},
                                                                {"name": "Чеснок", "quantity": 2, "unit": "зуб"}]},
    {"name": "Шарлотка", "rating": 4.4,
     "ingredients": [{"name": "Яблоки", "quantity": 3, "unit": "шт"}, {"name": "Мука", "quantity": 200, "unit": "г"},
                     {"name": "Яйцо", "quantity": 3, "unit": "шт"}]},
    {"name": "Рис с овощами", "rating": 4.1,
     "ingredients": [{"name": "Рис", "quantity": 200, "unit": "г"}, {"name": "Морковь", "quantity": 1, "unit": "шт"},
                     {"name": "Горошек", "quantity": 100, "unit": "г"}]},
    {"name": "Сэндвич с тунцом", "rating": 4.2,
     "ingredients": [{"name": "Хлеб", "quantity": 2, "unit": "лом"}, {"name": "Тунец", "quantity": 100, "unit": "г"},
                     {"name": "Огурец", "quantity": 1, "unit": "шт"}]},
    {"name": "Наггетсы", "rating": 4.0,
     "ingredients": [{"name": "Курица", "quantity": 400, "unit": "г"}, {"name": "Мука", "quantity": 100, "unit": "г"},
                     {"name": "Яйцо", "quantity": 1, "unit": "шт"}]},
    {"name": "Фруктовый салат", "rating": 4.8,
     "ingredients": [{"name": "Яблоки", "quantity": 2, "unit": "шт"}, {"name": "Банан", "quantity": 2, "unit": "шт"},
                     {"name": "Апельсин", "quantity": 1, "unit": "шт"}]}
]


async def seed_db():
    print("Подключение к MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print("Очистка старых данных...")
    await db.recipes.delete_many({})

    docs = []
    for r in RECIPES:
        r["id"] = str(uuid.uuid4())
        docs.append(r)

    print("Добавление новых рецептов...")
    await db.recipes.insert_many(docs)
    print(f"✅ Успешно добавлено {len(docs)} рецептов с единицами измерения!")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_db())