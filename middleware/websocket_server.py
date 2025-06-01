from fastapi import WebSocket, WebSocketDisconnect
import logging
from config.settings import settings

logger = logging.getLogger("websocket")
logger.setLevel(logging.INFO)

async def websocket_middleware_wrapper(websocket: WebSocket, endpoint):
    if not settings.ENABLE_WEBSOCKETS:
        logger.info("WebSocket connections are disabled. Closing connection: %s", websocket.url)
        await websocket.close()
        return
    logger.info("WebSocket connection started: %s", websocket.url)
    await websocket.accept()
    try:
        await endpoint(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected: %s", websocket.client)\

def authentication():
    print("Blank middleware")