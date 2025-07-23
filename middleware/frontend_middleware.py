import logging
from fastapi import Request

logger = logging.getLogger("frontend")
logger.setLevel(logging.INFO)

async def frontend_middleware(request: Request, call_next):
    logger.info("Frontend Middleware: Request received for %s", request.url.path)
    response = await call_next(request)
    return response