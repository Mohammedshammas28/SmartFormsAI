import os
import sys
import json
import urllib.parse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        
        # Diagnostic endpoint to see exact Vercel WSGI environment
        if 'debug-check' in query_string or 'debug-check' in environ.get('PATH_INFO', ''):
            start_response('200 OK', [('Content-Type', 'application/json')])
            data = {
                'PATH_INFO': environ.get('PATH_INFO'),
                'QUERY_STRING': environ.get('QUERY_STRING'),
                'HTTP_X_MATCHED_PATH': environ.get('HTTP_X_MATCHED_PATH'),
                'all_http_headers': {k: v for k, v in environ.items() if k.startswith('HTTP_')}
            }
            return [json.dumps(data, indent=2).encode('utf-8')]

        if 'path=' in query_string:
            qs = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            requested_path = qs.get('path', [''])[0]
            if requested_path:
                environ['PATH_INFO'] = requested_path if requested_path.startswith('/') else '/' + requested_path
            else:
                environ['PATH_INFO'] = '/'
            
            cleaned_params = [(k, v) for k, vs in qs.items() if k != 'path' for v in vs]
            environ['QUERY_STRING'] = urllib.parse.urlencode(cleaned_params)
        elif environ.get('PATH_INFO') in ('/api/index', '/api/index/'):
            environ['PATH_INFO'] = '/'

        return self.wsgi_app(environ, start_response)

handler = VercelPathMiddleware(app)
app = handler
