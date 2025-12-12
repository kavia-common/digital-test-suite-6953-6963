from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import Schema, fields, validate, EXCLUDE

from ..models import User

blp = Blueprint(
    "Users",
    "users",
    url_prefix="/api/users",
    description="User management endpoints",
)


class UserSchema(Schema):
    id = fields.String(dump_only=True)
    email = fields.Email(required=True)
    name = fields.String(required=True)
    role = fields.String(validate=validate.OneOf(["author", "student", "admin"]), required=True)
    active = fields.Boolean(required=False)
    created_at = fields.String(dump_only=True)
    updated_at = fields.String(dump_only=True)

    class Meta:
        unknown = EXCLUDE


class UserCreateSchema(Schema):
    email = fields.Email(required=True)
    name = fields.String(required=True)
    role = fields.String(validate=validate.OneOf(["author", "student", "admin"]), required=True)
    active = fields.Boolean(required=False)

    class Meta:
        unknown = EXCLUDE


class UserUpdateSchema(Schema):
    name = fields.String(required=False)
    role = fields.String(validate=validate.OneOf(["author", "student", "admin"]), required=False)
    active = fields.Boolean(required=False)

    class Meta:
        unknown = EXCLUDE


@blp.route("")
class UsersListResource(MethodView):
    @blp.response(200, UserSchema(many=True))
    @blp.doc(summary="List users", description="Retrieve all users")
    def get(self):
        """List all users."""
        uow = current_app.config["UOW"]
        users = uow.users.list()
        return [u.to_dict() for u in users]

    @blp.arguments(UserCreateSchema)
    @blp.response(201, UserSchema)
    @blp.doc(summary="Create user", description="Create a new user")
    def post(self, new_user_data):
        """Create a user."""
        uow = current_app.config["UOW"]
        user = User(**new_user_data)
        try:
            created = uow.users.create(user)
        except ValueError as e:
            abort(400, message=str(e))
        return created.to_dict()


@blp.route("/<string:user_id>")
class UsersItemResource(MethodView):
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserSchema)
    @blp.doc(summary="Update user", description="Update a user by id")
    def put(self, update_data, user_id: str):
        """Update a user by id."""
        uow = current_app.config["UOW"]
        updated = uow.users.update(user_id, update_data)
        if not updated:
            abort(404, message="User not found")
        return updated.to_dict()

    @blp.response(204)
    @blp.doc(summary="Delete user", description="Delete a user by id")
    def delete(self, user_id: str):
        """Delete a user by id."""
        uow = current_app.config["UOW"]
        ok = uow.users.delete(user_id)
        if not ok:
            abort(404, message="User not found")
        return "", 204
