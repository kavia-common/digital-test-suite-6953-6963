from flask_smorest import Blueprint
from flask.views import MethodView

# Standardize naming and path as /api/health
blp = Blueprint("Health", "health", url_prefix="/api/health", description="Health check route")


@blp.route("")
class HealthCheck(MethodView):
    def get(self):
        """Health check endpoint to verify service availability."""
        return {"status": "ok", "message": "Healthy"}
