import typing
import datetime
from dataclasses import dataclass
from flask import Blueprint, Response, request
from flask.views import MethodView
from marshmallow import ValidationError
import marshmallow_dataclass
from dependency_injector.wiring import inject, Provide
from passlib.hash import pbkdf2_sha256
import jwt
from .util import class_route, json_response, error_response, validation_error_response
from containers import Container
from repositories import EmployeeRepository

blp = Blueprint("Authentication", __name__)

JWTPayload = typing.TypedDict('JWTPayload', {
    'iss': str,
    'sub': str,
    'cid': str,
    'aud': str,
    'iat': int,
    'exp': int
})


@dataclass
class AuthBody:
    username: str
    password: str


@class_route(blp, "/api/v1/auth/employee")
class AuthEmployee(MethodView):
    init_every_request = False

    @inject
    def post(
        self,
        employee_repo: EmployeeRepository = Provide[Container.employee_repo],
        jwt_issuer: str = Provide[Container.config.jwt.issuer],
        jwt_private_key: str = Provide[Container.config.jwt.private_key]
    ) -> Response:
        auth_schema = marshmallow_dataclass.class_schema(AuthBody)()
        req_json = request.get_json(silent=True)
        if req_json is None:
            return error_response('The request body could not be parsed as valid JSON.', 400)

        try:
            data: AuthBody = auth_schema.load(req_json)
        except ValidationError as err:
            return validation_error_response(err)

        employee = employee_repo.find_employee_by_email(data.username)

        if employee is None or not pbkdf2_sha256.verify(data.password, employee.password):
            return error_response('Invalid username or password.', 401)

        time_issued = datetime.datetime.now(datetime.timezone.utc)
        time_expiry = time_issued + datetime.timedelta(minutes=15)

        payload: JWTPayload = {
            "iss": jwt_issuer,
            "sub": employee.id,
            "cid": employee.client_id,
            "aud": employee.role.lower(),
            "iat": int(time_issued.timestamp()),
            "exp": int(time_expiry.timestamp()),
        }

        resp = {
            'token': jwt.encode(typing.cast(dict[str, typing.Any], payload), jwt_private_key, algorithm="EdDSA")
        }

        return json_response(resp, 200)
