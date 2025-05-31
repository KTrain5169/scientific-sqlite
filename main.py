from flask import Flask, request, render_template
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
import uvicorn

from config.settings import settings
from utils.db import init_db
from middleware.sample_middleware import sample_middleware
from routes import api_router
from websocket.server import router as websocket_router  # Import the WebSocket router

# --- Initialize the database if enabled ---
if settings.ENABLE_DB_QUERIES:
    init_db()

# --- Setup Flask (Dynamic Frontend) ---
flask_app = Flask(__name__)  # Flask will use the './templates' folder by default

@flask_app.route("/")
def index():
    return render_template("index.html")

@flask_app.route("/sample", methods=["GET", "POST"])
def sample():
    if request.method == "POST":
        return "Data received (Flask POST)"
    return "Sample GET route from Flask"

# Custom 404 error handler
@flask_app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# --- Setup FastAPI (JSON API, Middleware & WebSocket) ---
app = FastAPI()

# Add middleware only if enabled
if settings.ENABLE_MIDDLEWARE:
    app.middleware("http")(sample_middleware)

# Include API routes only if enabled
if settings.ENABLE_API:
    app.include_router(api_router, prefix="/api")

# Include the WebSocket route at /ws
app.include_router(websocket_router, prefix="/ws")

# Mount the Flask app if enabled
if settings.ENABLE_FRONTEND:
    app.mount("/", WSGIMiddleware(flask_app))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.RELOAD
    )