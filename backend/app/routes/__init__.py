"""
Flask blueprints for the backend API.
Exposes blueprint variables for registration in app.__init__.
"""

from .health import blp as health_blp  # Health blueprint
from .tests import blp as tests_blp  # Tests blueprint
from .analytics import blp as analytics_blp  # Analytics blueprint
from .users import blp as users_blp  # Users blueprint

__all__ = ["health_blp", "tests_blp", "analytics_blp", "users_blp"]
