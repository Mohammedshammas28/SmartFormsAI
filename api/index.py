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
    When Vercel rewrites requests to /api/index, the original path is provided via:
    1. HTTP_X_MATCHED_PATH header
    2. ?path=$1 query parameter
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get('HTTP_X_MATCHED_PATH')
        if matched_path and matched_path != '/api/index':
            environ['PATH_INFO'] = matched_path.split('?')[0]
        elif 'QUERY_STRING' in environ and 'path=' in environ['QUERY_STRING']:
            qs = urllib.parse.parse_qs(environ['QUERY_STRING'])
            if 'path' in qs and qs['path'][0]:
                p = qs['path'][0]
                environ['PATH_INFO'] = p if p.startswith('/') else '/' + p
        elif environ.get('PATH_INFO') in ('/api/index', '/api/index/'):
            environ['PATH_INFO'] = '/'

        return self.wsgi_app(environ, start_response)

# Wrap app so Vercel forwards every route correctly
handler = VercelPathMiddleware(app)
app = handler
