from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields

blp = Blueprint(
    "Analytics",
    "analytics",
    url_prefix="/api/analytics",
    description="Analytics endpoints for tests and overall metrics",
)


class SummarySchema(Schema):
    users = fields.Integer()
    tests = fields.Integer()
    submissions = fields.Integer()


class TestAnalyticsSchema(Schema):
    test_id = fields.String()
    average_score = fields.Float(allow_none=True)
    completion_rate = fields.Float()
    top_scores = fields.List(fields.Tuple((fields.String(), fields.Float())))


@blp.route("/summary")
class AnalyticsSummaryResource(MethodView):
    @blp.response(200, SummarySchema)
    @blp.doc(summary="Summary analytics", description="Return overall counts")
    def get(self):
        """Return overall counts for users, tests, and submissions."""
        uow = current_app.config["UOW"]
        return {
            "users": uow.users.count(),
            "tests": uow.tests.count(),
            "submissions": uow.submissions.count(),
        }


@blp.route("/tests/<string:test_id>")
class TestAnalyticsResource(MethodView):
    @blp.response(200, TestAnalyticsSchema)
    @blp.doc(
        summary="Test analytics",
        description="Return analytics for a specific test (average score, completion rate, top scores)",
    )
    def get(self, test_id: str):
        """Return analytics for a test."""
        uow = current_app.config["UOW"]
        avg = uow.submissions.average_score_for_test(test_id)
        rate = uow.submissions.completion_rate_for_test(test_id)
        top = uow.submissions.top_scores_for_test(test_id, n=5)
        return {
            "test_id": test_id,
            "average_score": avg,
            "completion_rate": rate,
            "top_scores": top,
        }
