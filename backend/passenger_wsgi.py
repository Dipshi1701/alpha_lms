import os
import sys

LIMIT_REQUEST_BODY = 209715200

BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
    
from a2wsgi import ASGIMiddleware
from app.main import app




application = ASGIMiddleware(app)