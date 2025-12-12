from flask import Flask
from flask_cors import CORS
from .routes.health import blp
from flask_smorest import Api
from .models import InMemoryUnitOfWork

# Initialize Flask application
app = Flask(__name__)
app.url_map.strict_slashes = False

# Enable CORS for all origins (adjust in production)
CORS(app, resources={r"/*": {"origins": "*"}})

# OpenAPI / Swagger configuration
app.config["API_TITLE"] = "My Flask API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

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

# Register blueprints
api.register_blueprint(blp)
