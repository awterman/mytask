from fastapi import APIRouter

router = APIRouter()


@router.get("/tao_dividends")
async def get_tao_dividends(
    netuid: int | None = None,
    hotkey: str | None = None,
    trade: bool = False,
):
    return {"message": "Hello, World!"}