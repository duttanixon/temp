import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.utils.logger import get_logger

logger = get_logger("api")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request info
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            f"Request received: {request.method} {request.url.path} | "
            f"Client: {client_host} | ID: {request_id}"
        )
        
        # Record start time
        start_time = time.time()
        
        # Process the request and get the response
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response info
            logger.info(
                f"Request completed: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {process_time:.4f}s | ID: {request_id}"
            )
            
            # Add custom headers if needed
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log any unhandled exceptions
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} | "
                f"Error: {str(e)} | Duration: {process_time:.4f}s | ID: {request_id}",
                exc_info=True
            )
            raise