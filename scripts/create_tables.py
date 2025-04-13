import asyncio
import importlib
import pkgutil
from pathlib import Path

import mytask.models
from mytask.common.base import MyTaskBaseModel
from mytask.common.table import get_async_engine

# Dynamically import all modules under mytask.models
for _, name, ispkg in pkgutil.iter_modules([str(Path(__file__).parent.parent / "mytask" / "models")]):
    if not ispkg and name != "__init__":
        importlib.import_module(f"mytask.models.{name}")

async def create_tables():
    # Get the engine directly
    engine = get_async_engine()
    # Create tables using the engine
    async with engine.begin() as conn:
        await conn.run_sync(MyTaskBaseModel.metadata.create_all)

asyncio.run(create_tables())
