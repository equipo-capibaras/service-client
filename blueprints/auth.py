import datetime
import typing
from dataclasses import dataclass

import jwt
import marshmallow_dataclass
from dependency_injector.wiring import Provide, inject
from flask import Blueprint, Response, request
from flask.views import MethodView
from marshmallow import ValidationError
from passlib.hash import pbkdf2_sha256

from containers import Container
from models import Employee, InvitationStatus
from repositories import EmployeeRepository

from .util import class_route, error_response, json_response, requires_token, validation_error_response

blp = Blueprint('Authentication', __name__)


class JWTPayload(typing.TypedDict):
    iss: str
    sub: str
    cid: str | None
    email: str
    role: str
    aud: str
    iat: int
    exp: int


@dataclass
class AuthBody:
    username: str
    password: str


@inject
def issue_token(
    employee: Employee,
    jwt_issuer: str = Provide[Container.config.jwt.issuer.required()],
    jwt_private_key: str = Provide[Container.config.jwt.private_key.required()],
) -> str:
    time_issued = datetime.datetime.now(datetime.UTC)
    time_expiry = time_issued + datetime.timedelta(minutes=15)

    assigned = employee.client_id is not None and employee.invitation_status == InvitationStatus.ACCEPTED

    payload: JWTPayload = {
        'iss': jwt_issuer,
        'sub': employee.id,
        'cid': employee.client_id,
        'email': employee.email,
        'role': employee.role.value,
        'aud': ('' if assigned else 'unassigned_') + employee.role.value,
        'iat': int(time_issued.timestamp()),
        'exp': int(time_expiry.timestamp()),
    }

    return jwt.encode(typing.cast(dict[str, typing.Any], payload), jwt_private_key, algorithm='EdDSA')


@class_route(blp, '/api/v1/auth/employee')
class AuthEmployee(MethodView):
    init_every_request = False

    @inject
    def post(
        self,
        employee_repo: EmployeeRepository = Provide[Container.employee_repo],
    ) -> Response:
        auth_schema = marshmallow_dataclass.class_schema(AuthBody)()
        req_json = request.get_json(silent=True)
        if req_json is None:
            return error_response('The request body could not be parsed as valid JSON.', 400)

        try:
            data: AuthBody = auth_schema.load(req_json)
        except ValidationError as err:
            return validation_error_response(err)

        employee = employee_repo.find_by_email(data.username)

        if employee is None or not pbkdf2_sha256.verify(data.password, employee.password):
            return error_response('Invalid username or password.', 401)

        resp = {
            'token': issue_token(employee),
        }

        return json_response(resp, 200)


@class_route(blp, '/api/v1/auth/employee/refresh')
class AuthEmployeeRefresh(MethodView):
    init_every_request = False

    @requires_token
    def post(
        self, token: dict[str, typing.Any], employee_repo: EmployeeRepository = Provide[Container.employee_repo]
    ) -> Response:
        employee = employee_repo.find_by_email(token['email'])

        if employee is None:
            return error_response('Employee not found', 404)

        resp = {
            'token': issue_token(employee),
        }

        return json_response(resp, 200)
