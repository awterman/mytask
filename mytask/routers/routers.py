from fastapi import APIRouter

from mytask.routers.v1 import tao

router = APIRouter()
router.include_router(tao.router, prefix="/v1")
