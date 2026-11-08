import os
import sys

# Ensure project root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app
from flask import request

@app.errorhandler(404)
def handle_404(e):
    return {
        "error": "404 Not Found",
        "request.path": request.path,
        "request.url": request.url,
        "environ.PATH_INFO": request.environ.get("PATH_INFO"),
        "environ.SCRIPT_NAME": request.environ.get("SCRIPT_NAME"),
        "x-matched-path": request.headers.get("x-matched-path"),
        "headers": dict(request.headers)
    }, 404

# Export both app and handler for maximum compatibility with Vercel's Python runtime
handler = app

