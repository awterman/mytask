from sqlalchemy.ext.asyncio import AsyncSession

from mytask.common.table import BaseTable
from mytask.models.tao import TaoDividendDAO, TaoDividendModel


class TaoDividendTable(BaseTable[TaoDividendDAO, TaoDividendModel]):
    def __init__(self, session: AsyncSession | None = None):
        super().__init__(TaoDividendDAO, TaoDividendModel, session)
