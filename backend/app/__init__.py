import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_smorest import Api
from .models import InMemoryUnitOfWork

# Blueprints
from .routes.health import blp as health_blp
from .routes.tests import blp as tests_blp
from .routes.analytics import blp as analytics_blp
from .routes.users import blp as users_blp

# Initialize Flask application
app = Flask(__name__)
app.url_map.strict_slashes = False

# Enable CORS for all origins (adjust in production)
CORS(app, resources={r"/*": {"origins": "*"}})

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")
logger.info("Starting backend service")

# OpenAPI / Swagger configuration
app.config["API_TITLE"] = "AI Digitest Backend API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

openapi_tags = [
    {"name": "Health", "description": "Health check route"},
    {"name": "Tests", "description": "Test management endpoints"},
    {"name": "Analytics", "description": "Analytics endpoints"},
    {"name": "Users", "description": "User management endpoints"},
]
app.config["OPENAPI_TAGS"] = openapi_tags

# Initialize API
api = Api(app)

# Initialize in-memory data layer and seed basic demo data
uow = InMemoryUnitOfWork()
app.config["UOW"] = uow  # Expose for route access
try:
    uow.seed_demo_data()
except Exception:
    # Seeding should never crash the app; ignore in case of validation issues
    pass

# Error handlers
@app.errorhandler(400)
def handle_400(err):
    return jsonify({"code": 400, "status": "Bad Request", "message": str(err)}), 400


@app.errorhandler(404)
def handle_404(err):
    return jsonify({"code": 404, "status": "Not Found", "message": "Resource not found"}), 404


@app.errorhandler(500)
def handle_500(err):
    return jsonify({"code": 500, "status": "Internal Server Error", "message": "Unexpected error"}), 500


# Register blueprints
api.register_blueprint(health_blp)
api.register_blueprint(tests_blp)
api.register_blueprint(analytics_blp)
api.register_blueprint(users_blp)
