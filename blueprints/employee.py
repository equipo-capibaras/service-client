import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import marshmallow.validate
import marshmallow_dataclass
from dependency_injector.wiring import Provide
from flask import Blueprint, Response, request
from flask.views import MethodView
from marshmallow import ValidationError
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from containers import Container
from models import Employee, InvitationResponse, InvitationStatus, Role
from repositories import EmployeeRepository
from repositories.errors import DuplicateEmailError

from .util import class_route, error_response, json_response, requires_token, validation_error_response

blp = Blueprint('Employees', __name__)

JSON_VALIDATION_ERROR = 'Request body must be a JSON object.'


def employee_to_dict(employee: Employee) -> dict[str, Any]:
    return {
        'id': employee.id,
        'clientId': employee.client_id,
        'name': employee.name,
        'email': employee.email,
        'role': employee.role.value,
        'invitationStatus': employee.invitation_status.value,
        'invitationDate': employee.invitation_date.isoformat(),
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


# Invitation validation class
@dataclass
class InviteEmployeeBody:
    email: str = field(metadata={'validate': [marshmallow.validate.Email(), marshmallow.validate.Length(min=1, max=60)]})


@dataclass
class ResponseInvitationBody:
    response: str = field(
        metadata={
            'response': marshmallow.validate.OneOf([InvitationResponse.ACCEPTED.value, InvitationResponse.DECLINED.value])
        }
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
            return error_response(JSON_VALIDATION_ERROR, 400)

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
            invitation_date=datetime.now(UTC).replace(microsecond=0),
        )

        # Save employee
        try:
            employee_repo.create(employee)
        except DuplicateEmailError:
            return error_response('Email already registered', 409)

        return json_response(employee_to_dict(employee), 201)


@class_route(blp, '/api/v1/employees')
class EmployeeList(MethodView):
    init_every_request = False

    @requires_token
    def get(self, token: dict[str, Any], employee_repo: EmployeeRepository = Provide[Container.employee_repo]) -> Response:
        # Verify if the user has administrator permissions
        if token['role'] != Role.ADMIN.value:
            return error_response('Forbidden: You do not have access to this resource.', 403)

        client_id = token['cid']

        # Optional pagination parameters
        page_size = request.args.get('page_size', default=5, type=int)
        page_number = request.args.get('page_number', default=1, type=int)

        # Validate the value of page_size
        allowed_page_sizes = [5, 10, 20]
        if page_size not in allowed_page_sizes:
            return error_response(f'Invalid page_size. Allowed values are {allowed_page_sizes}.', 400)

        # Validate the value of page_number
        if page_number < 1:
            return error_response('Invalid page_number. Page number must be 1 or greater.', 400)

        total_employees = employee_repo.count(client_id)
        total_pages = (total_employees + page_size - 1) // page_size

        # Retrieve employees and the total number of employees using the repository
        employees = employee_repo.get_all(
            client_id,
            offset=(page_number - 1) * page_size,
            limit=page_size,
        )

        # Create the response with employees and pagination information
        response_data = {
            'employees': [employee_to_dict(employee) for employee in employees],
            'totalPages': total_pages,
            'currentPage': page_number,
            'totalEmployees': total_employees,
        }

        return json_response(response_data, 200)


@class_route(blp, '/api/v1/employees/invite')
class EmployeeInvite(MethodView):
    init_every_request = False

    @requires_token
    def post(
        self,
        token: dict[str, Any],
        employee_repo: EmployeeRepository = Provide[Container.employee_repo],
    ) -> Response:
        # Validate if the requester has admin privileges and is linked to a company
        if token['role'] != Role.ADMIN.value or token['cid'] is None:
            return error_response('Forbidden: You do not have access to this resource or must be linked to a company.', 403)

        # Parse request body
        invite_schema = marshmallow_dataclass.class_schema(InviteEmployeeBody)()
        req_json = request.get_json(silent=True)

        if req_json is None:
            return error_response(JSON_VALIDATION_ERROR, 400)

        try:
            data: InviteEmployeeBody = invite_schema.load(req_json)
        except ValidationError as err:
            return validation_error_response(err)

        # Find employee by email
        employee = employee_repo.find_by_email(data.email)

        if employee is None:
            return error_response('Employee not found.', 404)

        # Validate employee state
        error_message = None
        if employee.client_id is not None and employee.client_id != token['cid']:
            error_message = 'Employee already linked to another company.'
        elif employee.client_id == token['cid']:
            error_message = 'Employee already linked to your company'
        elif employee.invitation_status != InvitationStatus.UNINVITED:
            error_message = 'Employee already invited.'

        if error_message:
            return error_response(error_message, 409)

        # Update employee invitation status and date
        employee.client_id = token['cid']
        employee.invitation_status = InvitationStatus.PENDING
        employee.invitation_date = datetime.now(UTC).replace(microsecond=0)

        # Save updated employee
        employee_repo.delete(employee_id=employee.id, client_id=None)
        employee_repo.create(employee)

        return json_response(
            {
                'message': 'Employee invited successfully',
                'employee': employee_to_dict(employee),
            },
            201,
        )


@class_route(blp, '/api/v1/employees/invitation')
class EmployeeInvitationResponse(MethodView):
    @requires_token
    def post(
        self,
        token: dict[str, Any],
        employee_repo: EmployeeRepository = Provide[Container.employee_repo],
    ) -> Response:
        respond_schema = marshmallow_dataclass.class_schema(ResponseInvitationBody)()
        req_json = request.get_json(silent=True)

        if req_json is None:
            return error_response(JSON_VALIDATION_ERROR, 400)

        try:
            data: ResponseInvitationBody = respond_schema.load(req_json)
        except ValidationError as err:
            return validation_error_response(err)

        # Get the employee from the token
        employee = employee_repo.get(employee_id=token['sub'], client_id=token['cid'])

        # Validations
        error_message = None
        error_code = None

        if employee is None:
            return error_response('Employee not found', 404)

        if employee.client_id is None:
            error_message = 'No invitation to respond to'
            error_code = 404
        if employee.invitation_status == InvitationStatus.ACCEPTED:
            error_message = 'You are already linked to the organization'
            error_code = 409
        if error_message and error_code:
            return error_response(error_message, error_code)

        # Process the invitation response
        if data.response == InvitationResponse.ACCEPTED.value:
            employee.invitation_status = InvitationStatus.ACCEPTED
            message = 'Invitation accepted successfully'
        elif data.response == InvitationResponse.DECLINED.value:
            employee.invitation_status = InvitationStatus.UNINVITED
            employee.client_id = None
            employee.invitation_date = datetime.now(UTC).replace(microsecond=0)
            message = 'Invitation declined successfully'
        else:
            return error_response('Invalid response', 400)

        # Save the updated employee
        employee_repo.delete(employee_id=employee.id, client_id=token['cid'])
        employee_repo.create(employee)

        return json_response(
            {
                'message': message,
                'employee': employee_to_dict(employee),
            },
            200,
        )
