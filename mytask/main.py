from fastapi import FastAPI

from mytask.middlewares.auth import AuthMiddleware
from mytask.routers import routers

app = FastAPI()

# Add authentication middleware
app.add_middleware(AuthMiddleware)

app.include_router(routers.router, prefix="/api")