# {
#   "netuid": 1,
#   "hotkey": "5GrwvaEF...ABC",
#   "dividend": 123456789,
#   "cached": true,
#   "stake_tx_triggered": true
# }

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Integer, String

from mytask.common.base import MyTaskBaseDAO, MyTaskBaseDTO, MyTaskBaseModel


class TaoDividendModel(MyTaskBaseModel):
    __tablename__ = "tao_dividends"

    netuid = Column(Integer)
    hotkey = Column(String)
    dividend = Column(Integer)
    cached = Column(Boolean)
    stake_tx_triggered = Column(Boolean)


class TaoDividendBase(BaseModel):
    netuid: int
    hotkey: str
    dividend: int
    cached: bool
    stake_tx_triggered: bool


class TaoDividendDAO(TaoDividendBase, MyTaskBaseDAO):
    pass


class TaoDividendDTO(TaoDividendBase, MyTaskBaseDTO):
    pass
