import sys
import os

app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)
os.chdir(app_dir)

# Importar la app de FastAPI
from main import app

# Convertir ASGI a WSGI para cPanel/Passenger
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except ImportError:
    pass
