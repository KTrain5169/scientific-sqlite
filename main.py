from flask import Flask, request, render_template, abort
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
import argparse

from config.settings import settings
from utils.db import init_db
from middleware.sample_middleware import sample_middleware
from routes import api_router
from websocket.server import router as websocket_router  # Import the WebSocket router

# Import CMS config and parser
from content.cms_list import collections
from utils.cms_parser import parse_collection

# --- Initialize the database if enabled ---
if settings.ENABLE_DB_QUERIES:
    init_db()

# --- Setup Flask (Dynamic Frontend & CMS) ---
flask_app = Flask(__name__)  # Flask will use the './templates' folder by default

@flask_app.route("/")
def index():
    return render_template("index.html")

@flask_app.route("/sample/<name>", methods=["GET", "POST"])
def sample(name):
    if request.method == "POST":
        return render_template("sample.html", greeting=name, method="POST")
    return render_template("sample.html", greeting=name, method="GET")

@flask_app.route("/sample", methods=["GET", "POST"])
def sample_index():
    if request.method == "POST":
        return render_template("sample.html", greeting="there", method="POST")
    return render_template("sample.html", greeting="there", method="GET")

# CMS route: dynamic route for each content collection as defined in content/cms_list.py.
@flask_app.route("/cms/<collection_name>")
def cms_collection(collection_name):
    coll = collections.get(collection_name)
    if not coll:
        abort(404, description="Collection not found")
    docs = parse_collection(coll["path"])
    return render_template("cms/listing.html", docs=docs)

# Custom 404 error handler for Flask
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

# Include the WebSocket route at /ws
if settings.ENABLE_WEBSOCKETS:
    app.include_router(websocket_router, prefix="/ws")

# Include API routes only if enabled
if settings.ENABLE_API:
    app.include_router(api_router, prefix="/api")

# Mount the Flask app at root (HTTP requests via Flask, WebSocket via FastAPI)
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