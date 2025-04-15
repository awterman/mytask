# {
#   "netuid": 1,
#   "hotkey": "5GrwvaEF...ABC",
#   "dividend": 123456789,
#   "cached": true,
#   "stake_tx_triggered": true,
#   "sentiment_score": 75,
#   "task_id": "abc-123"
# }

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Float, Integer, String

from mytask.common.base import MyTaskBaseDAO, MyTaskBaseModel


class TaoDividendModel(MyTaskBaseModel):
    __tablename__ = "tao_dividends"

    netuid = Column(Integer)
    hotkey = Column(String)
    dividend = Column(Integer)


class TaoDividendBase(BaseModel):
    netuid: int
    hotkey: str
    dividend: int


class TaoDividendDAO(TaoDividendBase, MyTaskBaseDAO):
    pass


class TaoDividendResponseItem(TaoDividendBase):
    cached: bool
    stake_tx_triggered: bool


class GetTaoDividendsResponse(BaseModel):
    dividends: list[TaoDividendResponseItem]
