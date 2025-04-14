import logging
import time
import traceback
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request details
        logger.info(
            f"Request {request_id} started: {request.method} {request.url.path}"
            f"{f'?{request.query_params}' if request.query_params else ''}"
        )

        # Measure request processing time
        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add custom header with processing time and request ID
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            # Log response details
            logger.info(
                f"Request {request_id} completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Took: {process_time:.4f}s"
            )

            return response
        except Exception as e:
            # Calculate processing time in case of exception
            process_time = time.time() - start_time

            # Log exception details
            logger.error(
                f"Request {request_id} failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Took: {process_time:.4f}s"
            )
            # Print traceback
            logger.error(traceback.format_exc())

            # Re-raise the exception to be handled by FastAPI
            raise
