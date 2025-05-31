from flask import Flask, request, render_template
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
import uvicorn
import argparse

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

@flask_app.route("/sample/<name>", methods=["GET", "POST"])
def sample(name):
    if request.method == "POST":
        return render_template("sample.html", greeting=name, method="POST")
    return render_template("sample.html", greeting=name, method="GET")

# Custom 404 error handler
@flask_app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404

@flask_app.errorhandler(500)
def internal_server_error(e):
    return render_template("errors/500.html"), 500

# --- Setup FastAPI (JSON API, Middleware & WebSocket) ---
app = FastAPI()

# Add middleware only if enabled
if settings.ENABLE_MIDDLEWARE:
    app.middleware("http")(sample_middleware)

# Include API routes only if enabled
if settings.ENABLE_API:
    app.include_router(api_router, prefix="/api")

# Include the WebSocket route at /ws
if settings.ENABLE_WEBSOCKETS:
    app.include_router(websocket_router, prefix="/ws")

# Mount the Flask app if enabled
if settings.ENABLE_FRONTEND:
    app.mount("/", WSGIMiddleware(flask_app))

if __name__ == "__main__":
    # Parse CLI arguments for temporary overrides
    parser = argparse.ArgumentParser(description="Run Scientific-SQLite Server with temporary config overrides")
    parser.add_argument("--host", type=str, help="Override the host", default=settings.FASTAPI_HOST)
    parser.add_argument("--port", type=int, help="Override the port", default=settings.FASTAPI_PORT)
    parser.add_argument("--reload", action="store_true", help="Enable auto reload", default=settings.RELOAD)
    args = parser.parse_args()

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )