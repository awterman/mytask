from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from pydantic import (BaseModel, BeforeValidator, ConfigDict, Field,
                      PlainSerializer)
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class MyTaskBaseModel(Base):
    __abstract__ = True

    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


def validate_datetime(dt: str | datetime) -> datetime:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)

    if dt.tzinfo is None:
        raise ValueError("Datetime is not timezone aware")
    return dt.astimezone(tz=timezone.utc)


MyTaskDatetime = Annotated[
    datetime,
    BeforeValidator(validate_datetime),
    PlainSerializer(
        lambda dt: str(dt),
        return_type=str,
        when_used="json-unless-none",
    ),
]


class MyTaskBaseDAO(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: MyTaskDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: MyTaskDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)