import os
import sys
import urllib.parse

# Ensure project root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

class VercelPathMiddleware:
    """
    WSGI Middleware to restore original request paths from Vercel's edge rewrites.
    vercel.json rewrites incoming requests:
      source: /(.*) -> destination: /api/index?path=$1
    This middleware extracts the real intended path from ?path= and sets PATH_INFO,
    cleaning the query string so Flask and Jinja2 route correctly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        if 'path=' in query_string:
            qs = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            requested_path = qs.get('path', [''])[0]
            if requested_path:
                environ['PATH_INFO'] = requested_path if requested_path.startswith('/') else '/' + requested_path
            else:
                environ['PATH_INFO'] = '/'
            
            # Clean internal 'path' query param so it doesn't pollute request.args
            cleaned_params = [(k, v) for k, vs in qs.items() if k != 'path' for v in vs]
            environ['QUERY_STRING'] = urllib.parse.urlencode(cleaned_params)
        elif environ.get('PATH_INFO') in ('/api/index', '/api/index/'):
            environ['PATH_INFO'] = '/'

        return self.wsgi_app(environ, start_response)

# Export WSGI callable for Vercel Python runtime
handler = VercelPathMiddleware(app)
app = handler
