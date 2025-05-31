from fastapi import APIRouter, WebSocket
import logging
from middleware.websocket_server import websocket_logging_wrapper

router = APIRouter()

async def echo_endpoint(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        logging.getLogger("websocket").info("Received message: %s", data)
        await websocket.send_text(f"Message received: {data}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_logging_wrapper(websocket, echo_endpoint)