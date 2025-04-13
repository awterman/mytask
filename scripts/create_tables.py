import asyncio
import importlib
import pkgutil

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

import mytask.models
from mytask.common.base import MyTaskBaseModel
from mytask.common.table import get_async_engine, get_async_session_factory

for _, module_name, _ in pkgutil.iter_modules(mytask.models.__path__):
    full_module_name = f"{mytask.models.__name__}.{module_name}"
    importlib.import_module(full_module_name)

async def create_tables():
    async with get_async_session_factory()() as session:
        await session.run_sync(MyTaskBaseModel.metadata.create_all)

asyncio.run(create_tables())
