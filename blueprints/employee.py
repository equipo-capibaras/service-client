from typing import Any

from dependency_injector.wiring import Provide
from flask import Blueprint, Response
from flask.views import MethodView

from containers import Container
from models import Employee
from repositories import EmployeeRepository

from .util import class_route, error_response, json_response, requires_token

blp = Blueprint('Employees', __name__)


def employee_to_dict(employee: Employee) -> dict[str, Any]:
    return {
        'id': employee.id,
        'clientId': employee.client_id,
        'name': employee.name,
        'email': employee.email,
        'role': employee.role.value,
    }


@class_route(blp, '/api/v1/employees/me')
class EmployeeInfo(MethodView):
    init_every_request = False

    @requires_token
    def get(self, token: dict[str, Any], employee_repo: EmployeeRepository = Provide[Container.employee_repo]) -> Response:
        employee = employee_repo.get(employee_id=token['sub'], client_id=token['cid'])

        if employee is None:
            return error_response('Employee not found', 404)

        return json_response(employee_to_dict(employee), 200)
