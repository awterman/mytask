from fastapi import FastAPI

from mytask.middlewares.auth import AuthMiddleware
from mytask.middlewares.logging import LoggingMiddleware
from mytask.routers import routers

app = FastAPI()

# Add logging middleware (should be added first to log all requests)
app.add_middleware(LoggingMiddleware)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

app.include_router(routers.router, prefix="/api")

