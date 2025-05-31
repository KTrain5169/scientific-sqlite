from fastapi import Request
import logging
from config.settings import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def sample_middleware(request: Request, call_next):
    logger.info("Request received: %s", request.url)
    # If middleware is disabled, simply pass through
    if not settings.ENABLE_MIDDLEWARE:
        return await call_next(request)
    response = await call_next(request)
    return response