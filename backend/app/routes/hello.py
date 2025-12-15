from flask_smorest import Blueprint
from flask.views import MethodView

# Blueprint for simple hello endpoint
blp = Blueprint(
    "Hello",
    "hello",
    url_prefix="/api/hello",
    description="Simple hello endpoint for connectivity testing",
)

@blp.route("")
class HelloResource(MethodView):
    # PUBLIC_INTERFACE
    def get(self):
        """Return a simple hello message for connectivity verification."""
        return {"message": "Hello from backend"}
