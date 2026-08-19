"""Version 1 JSON API for PharmaTrack."""

from flask import Blueprint


api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Import route modules after the Blueprint exists so their decorators attach
# endpoints to this single, versioned API namespace.
from api import auth, movements, products, reports  # noqa: E402, F401
