import os
import logging
import argparse
import uvicorn
from typing import List
from datetime import datetime

from flask import Flask, request, render_template, abort
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

from config.settings import settings
from utils.db import init_db
from middleware.sample_middleware import sample_middleware
from routes import api_router
from websocket.server import router as websocket_router

# Import CMS config and parser
from content.cms_list import collections
from utils.cms_parser import parse_collection

# Create a logger but delay the handler configuration until after CLI args are parsed.
logger = logging.getLogger("frontend")
logger.setLevel(logging.INFO)

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

# CMS route: dynamic route for each content collection defined in content/cms_list.py.
@flask_app.route("/cms/<collection_name>")
def cms_collection(collection_name):
    # Find the collection key by comparing lower-case values
    collection_key = next((k for k in collections.keys() if k.lower() == collection_name.lower()), None)
    if not collection_key:
        abort(404, description="Collection not found")
    coll = collections[collection_key]
    # Use the CMS parser to load the documents for this collection.
    docs = parse_collection(coll["path"])
    # Filter docs: require that if a 'published' field exists in metadata it must be True.
    filtered_docs = [doc for doc in docs if doc.get("metadata", {}).get("published", True)]
    # Automatically compute collection_base from the collection path.
    collection_base = os.path.basename(os.path.normpath(coll["path"]))
    return render_template("cms/listing.html",
                           docs=filtered_docs,
                           collection_name=collection_key,
                           collection_base=collection_base)

# Custom error handlers for Flask
@flask_app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404

@flask_app.errorhandler(500)
def internal_server_error(e):
    return render_template("errors/500.html"), 500

# --- Setup FastAPI (JSON API, Middleware & WebSocket) ---
app = FastAPI()

if settings.ENABLE_MIDDLEWARE:
    from middleware.frontend_middleware import frontend_middleware
    app.middleware("http")(frontend_middleware)
    app.middleware("http")(sample_middleware)

if settings.ENABLE_WEBSOCKETS:
    ws_prefix = "/ws"
    app.include_router(websocket_router, prefix=ws_prefix)
    logger.info("Route %s specified as WebSocket Route", ws_prefix)

if settings.ENABLE_API:
    api_prefix = "/api"
    app.include_router(api_router, prefix=api_prefix)
    logger.info("Route %s specified as API Route", api_prefix)

if settings.ENABLE_FRONTEND:
    from fastapi.middleware.wsgi import WSGIMiddleware
    app.mount("/", WSGIMiddleware(flask_app))
    logger.info("Mounted Flask app at '/' specified as Dynamic/CMS Route")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Scientific SQLite Server with temporary config overrides")
    parser.add_argument("--host", type=str, help="Override the host", default=settings.FASTAPI_HOST)
    parser.add_argument("--port", type=int, help="Override the port", default=settings.FASTAPI_PORT)
    parser.add_argument("--reload", action="store_true", help="Enable auto reload", default=settings.RELOAD)
    parser.add_argument("--log-to-file", action="store_true", help="Log output to a file", default=settings.LOG_TO_FILE)
    args = parser.parse_args()

    # Reconfigure logging based on the CLI flag (or setting)
    # Clear any pre-existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Explicitly annotate the handlers list
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    if args.log_to_file:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        # Create a file name with the current date and time
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(logs_dir, f"app_{timestamp}.log")
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_excludes=[".git",".github",".*","logs","*.db","README.md","LICENSE","requirements.txt"]
    )