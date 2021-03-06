import asyncpg
from loguru import logger
from tortoise import Tortoise

__all__ = (
    "MODELS_DIR",
    "init_db",
    "models",
    "utils"
)

MODELS_DIR = "currency_converter.db.models"


async def init_db(username, password, host, port, db_name):
    logger.debug(f"Инициализация BD {host}")
    data = {
        "db_url": f"postgres://{username}:{password}@{host}:{port}/{db_name}",
        "modules": {"models": [MODELS_DIR]},
    }
    try:
        await Tortoise.init(**data)
    except asyncpg.exceptions.DuplicateDatabaseError as e:
        logger.critical(e)
        await Tortoise.init(
            **data,
            _create_db=True,
        )
    await Tortoise.generate_schemas()
    logger.debug(f"База данных {db_name} инициализирована")
