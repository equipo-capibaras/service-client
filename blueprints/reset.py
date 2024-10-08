import json

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, Response, request
from flask.views import MethodView

import demo
from containers import Container
from repositories import ClientRepository, EmployeeRepository

from .util import class_route

blp = Blueprint('Reset database', __name__)


@class_route(blp, '/api/v1/reset/client')
class ResetDB(MethodView):
    init_every_request = False

    @inject
    def post(
        self,
        employee_repo: EmployeeRepository = Provide[Container.employee_repo],
        client_repo: ClientRepository = Provide[Container.client_repo],
    ) -> Response:
        employee_repo.delete_all()
        client_repo.delete_all()

        if request.args.get('demo', 'false') == 'true':
            for client in demo.clients:
                client_repo.create(client)

            for employee in demo.employees:
                employee_repo.create(employee)

        return Response(json.dumps({'status': 'Ok'}), status=200, mimetype='application/json')
