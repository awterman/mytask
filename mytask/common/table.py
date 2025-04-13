from functools import lru_cache
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

from mytask.common.base import MyTaskBaseDAO, MyTaskBaseModel
from mytask.common.settings import get_settings

T = TypeVar("T", bound=MyTaskBaseDAO)
S = TypeVar("S", bound=MyTaskBaseModel)

@lru_cache(maxsize=1)
def get_async_engine() -> AsyncEngine:
    # Convert the standard PostgreSQL URL to use the async driver
    dsn = get_settings().postgres_dsn
    # If URL starts with postgresql://, change to postgresql+psycopg:// 
    if dsn.startswith("postgresql://"):
        dsn = dsn.replace("postgresql://", "postgresql+psycopg://", 1)
    
    return create_async_engine(
        dsn,
        future=True,
        pool_pre_ping=True,
    )

@lru_cache(maxsize=1)
def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_async_engine())


class BaseTable(Generic[T, S]):
    def __init__(
        self,
        model: Type[T],
        table_model: Type[S],
        session: AsyncSession | None = None,
    ):
        self.model = model
        self.table_model = table_model
        self.session = session or get_async_session_factory()()
        self.is_session_managed = session is None

    async def create(self, data: T) -> T:
        self.session.add(data)
        await self.session.refresh(data)
        if self.is_session_managed:
            await self.session.commit()
            await self.session.close()
        return data

    async def get(self, id: int) -> Optional[T]:
        stmt = select(self.table_model).where(self.table_model.id == id)
        result = await self.session.execute(stmt)
        db_obj = result.scalars().first()
        if self.is_session_managed:
            await self.session.close()
        if db_obj is None:
            return None
        return self.model.model_validate(db_obj)

    async def get_all(self) -> List[T]:
        stmt = select(self.table_model)
        result = await self.session.execute(stmt)
        db_objects = result.scalars().all()
        if self.is_session_managed:
            await self.session.close()
        return [self.model.model_validate(obj) for obj in db_objects]

    async def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        stmt = (
            sa_update(self.table_model)
            .where(self.table_model.id == id)
            .values(**data)
            .returning(self.table_model)
        )
        result = await self.session.execute(stmt)
        db_obj = result.scalars().first()
        if self.is_session_managed:
            await self.session.commit()
            await self.session.close()
        if db_obj is None:
            return None
        return self.model.model_validate(db_obj)

    async def delete(self, id: int) -> bool:
        stmt = sa_delete(self.table_model).where(self.table_model.id == id)
        result = await self.session.execute(stmt)
        if self.is_session_managed:
            await self.session.commit()
            await self.session.close()
        return result.rowcount > 0

    async def filter(self, **kwargs) -> List[T]:
        stmt = select(self.table_model)
        for key, value in kwargs.items():
            if hasattr(self.table_model, key):
                stmt = stmt.where(getattr(self.table_model, key) == value)
        result = await self.session.execute(stmt)
        db_objects = result.scalars().all()
        if self.is_session_managed:
            await self.session.close()
        return [self.model.model_validate(obj) for obj in db_objects]
