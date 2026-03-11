import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("datapulse.middleware")


class GlobalLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Log request parameters excluding sensitive info/body
        method = request.method
        url = request.url.path
        logger.info(f"Incoming Request: {method} {url}")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            status_code = response.status_code
            logger.info(
                f"Outgoing Response: {method} {url} - Status: {status_code} - Time: {process_time:.4f}s"
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request Failed: {method} {url} - Error: {str(e)} - Time: {process_time:.4f}s"
            )
            raise e
