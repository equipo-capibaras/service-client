import uuid
from dataclasses import dataclass, field
from typing import Any

import marshmallow.validate
import marshmallow_dataclass
from dependency_injector.wiring import Provide
from flask import Blueprint, Response, request
from flask.views import MethodView
from marshmallow import ValidationError
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from containers import Container
from models import Employee, Role
from models.employee import InvitationStatus
from repositories import EmployeeRepository
from repositories.errors import DuplicateEmailError

from .util import class_route, error_response, json_response, requires_token, validation_error_response

blp = Blueprint('Employees', __name__)


def employee_to_dict(employee: Employee) -> dict[str, Any]:
    return {
        'id': employee.id,
        'clientId': employee.client_id,
        'name': employee.name,
        'email': employee.email,
        'role': employee.role.value,
        'invitationStatus': employee.invitation_status.value,
    }


# Employee validation class
@dataclass
class RegisterEmployeeBody:
    name: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=60)})
    email: str = field(metadata={'validate': [marshmallow.validate.Email(), marshmallow.validate.Length(min=1, max=60)]})
    password: str = field(metadata={'validate': marshmallow.validate.Length(min=8)})
    role: str = field(
        metadata={'validate': marshmallow.validate.OneOf([Role.ADMIN.value, Role.ANALYST.value, Role.AGENT.value])}
    )


@class_route(blp, '/api/v1/employees/me')
class EmployeeInfo(MethodView):
    init_every_request = False

    @requires_token
    def get(self, token: dict[str, Any], employee_repo: EmployeeRepository = Provide[Container.employee_repo]) -> Response:
        employee = employee_repo.get(employee_id=token['sub'], client_id=token['cid'])

        if employee is None:
            return error_response('Employee not found', 404)

        return json_response(employee_to_dict(employee), 200)


@class_route(blp, '/api/v1/employees')
class EmployeeRegister(MethodView):
    init_every_request = False

    def post(self, employee_repo: EmployeeRepository = Provide[Container.employee_repo]) -> Response:
        # Validate request body
        auth_schema = marshmallow_dataclass.class_schema(RegisterEmployeeBody)()
        req_json = request.get_json(silent=True)

        if req_json is None:
            return error_response('Request body must be a JSON object.', 400)

        # Validate request body
        try:
            data: RegisterEmployeeBody = auth_schema.load(req_json)
        except ValidationError as err:
            return validation_error_response(err)

        # Create employee
        employee = Employee(
            id=str(uuid.uuid4()),
            client_id=None,
            name=data.name,
            email=data.email,
            password=pbkdf2_sha256.hash(data.password),
            role=Role(data.role),
            invitation_status=InvitationStatus.UNINVITED,
        )

        # Save employee
        try:
            employee_repo.create(employee)
        except DuplicateEmailError:
            return error_response('Email already registered', 409)

        return json_response(employee_to_dict(employee), 201)
