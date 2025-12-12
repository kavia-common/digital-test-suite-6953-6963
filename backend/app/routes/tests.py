from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import Schema, fields, validate, EXCLUDE

from ..models import Test, Submission

# Blueprint for tests and submissions
blp = Blueprint(
    "Tests",
    "tests",
    url_prefix="/api/tests",
    description="Endpoints for managing tests and related submissions",
)


# Schemas
class QuestionSchema(Schema):
    id = fields.String(required=True, description="Question identifier")
    prompt = fields.String(required=True, description="Question prompt")
    type = fields.String(
        required=True,
        validate=validate.OneOf(["single_choice", "multiple_choice", "short_answer"]),
        description="Question type",
    )
    options = fields.List(
        fields.String(), required=False, description="Options for choice questions"
    )
    answer = fields.Raw(required=False, description="Reference answer (author side)")


class TestSchema(Schema):
    id = fields.String(dump_only=True, description="Test ID")
    title = fields.String(required=True, description="Title of the test")
    description = fields.String(required=False, allow_none=True, description="Description")
    author_id = fields.String(required=True, description="Author (user) ID")
    questions = fields.List(fields.Nested(QuestionSchema), required=False)
    published = fields.Boolean(required=False)
    tags = fields.List(fields.String(), required=False)
    created_at = fields.String(dump_only=True)
    updated_at = fields.String(dump_only=True)

    class Meta:
        unknown = EXCLUDE


class TestCreateSchema(Schema):
    title = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)
    author_id = fields.String(required=True)
    questions = fields.List(fields.Nested(QuestionSchema), required=False)
    published = fields.Boolean(required=False)
    tags = fields.List(fields.String(), required=False)

    class Meta:
        unknown = EXCLUDE


class SubmissionSchema(Schema):
    id = fields.String(dump_only=True)
    test_id = fields.String(required=True)
    user_id = fields.String(required=True)
    answers = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False)
    score = fields.Float(required=False, allow_none=True)
    status = fields.String(
        required=False,
        validate=validate.OneOf(["in_progress", "submitted", "graded"]),
        missing="submitted",
    )
    evaluation_notes = fields.String(required=False, allow_none=True)
    duration_seconds = fields.Integer(required=False, allow_none=True)
    created_at = fields.String(dump_only=True)
    updated_at = fields.String(dump_only=True)

    class Meta:
        unknown = EXCLUDE


class EvaluateSchema(Schema):
    rubric = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False)
    notes = fields.String(required=False)


@blp.route("")
class TestsListResource(MethodView):
    @blp.response(200, TestSchema(many=True))
    @blp.doc(summary="List tests", description="Retrieve all tests")
    def get(self):
        """List all tests."""
        uow = current_app.config["UOW"]
        tests = uow.tests.list()
        return [t.to_dict() for t in tests]

    @blp.arguments(TestCreateSchema)
    @blp.response(201, TestSchema)
    @blp.doc(summary="Create test", description="Create a new test")
    def post(self, new_test_data):
        """Create a test."""
        uow = current_app.config["UOW"]
        t = Test(**new_test_data)
        try:
            created = uow.tests.create(t)
        except ValueError as e:
            abort(400, message=str(e))
        return created.to_dict()


@blp.route("/<string:test_id>")
class TestItemResource(MethodView):
    @blp.response(200, TestSchema)
    @blp.doc(summary="Get test", description="Retrieve a test by id")
    def get(self, test_id: str):
        """Get a test by id."""
        uow = current_app.config["UOW"]
        t = uow.tests.get(test_id)
        if not t:
            abort(404, message="Test not found")
        return t.to_dict()


@blp.route("/<string:test_id>/submissions")
class TestSubmissionsResource(MethodView):
    @blp.arguments(SubmissionSchema)
    @blp.response(201, SubmissionSchema)
    @blp.doc(
        summary="Create submission",
        description="Create a submission for a given test",
    )
    def post(self, submission_data, test_id: str):
        """Create a submission for test."""
        uow = current_app.config["UOW"]
        # enforce test_id from path
        submission_data["test_id"] = test_id
        s = Submission(**submission_data)
        try:
            created = uow.submissions.create(s)
        except ValueError as e:
            abort(400, message=str(e))
        return created.to_dict()


@blp.route("/<string:test_id>/evaluate")
class TestEvaluateResource(MethodView):
    @blp.arguments(EvaluateSchema)
    @blp.response(200, SubmissionSchema(many=True))
    @blp.doc(
        summary="Evaluate test",
        description="Perform a minimal mock evaluation: set score=100 for submitted submissions lacking score",
    )
    def post(self, eval_data, test_id: str):
        """Mock evaluation for all submissions on a test."""
        uow = current_app.config["UOW"]
        subs = uow.submissions.list_by_test(test_id)
        updated = []
        for s in subs:
            if s.score is None:
                patch = {
                    "score": 100.0,
                    "status": "graded",
                    "evaluation_notes": eval_data.get("notes") if eval_data else "Auto-graded",
                }
                u = uow.submissions.update(s.id, patch)
                if u:
                    updated.append(u.to_dict())
            else:
                updated.append(s.to_dict())
        return updated
