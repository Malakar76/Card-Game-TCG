"""MongoDB connection management using Beanie and Motor."""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from card_game_tcg.config import settings
from card_game_tcg.models.card import Card

# All Beanie document models must be listed here for initialization.
DOCUMENT_MODELS = [
    Card,
]


async def init_db() -> AsyncIOMotorClient:
    """Initialize the MongoDB connection and Beanie ODM.

    Returns the Motor client so it can be closed on shutdown.
    """
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=DOCUMENT_MODELS,
    )
    return client
