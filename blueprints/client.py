from typing import Any

from dependency_injector.wiring import Provide
from flask import Blueprint, Response
from flask.views import MethodView

from containers import Container
from models import Client, Role
from repositories import ClientRepository

from .util import class_route, error_response, is_valid_uuid4, json_response, requires_token

blp = Blueprint('Clients', __name__)


def client_to_dict(client: Client, *, include_plan: bool = False) -> dict[str, Any]:
    res = {
        'id': client.id,
        'name': client.name,
        'emailIncidents': client.email_incidents,
    }

    if include_plan:
        res['plan'] = client.plan.value

    return res


@class_route(blp, '/api/v1/clients')
class ListClients(MethodView):
    init_every_request = False

    def get(self, client_repo: ClientRepository = Provide[Container.client_repo]) -> Response:
        clients = [client_to_dict(client) for client in client_repo.get_all()]

        return json_response(clients, 200)


@class_route(blp, '/api/v1/clients/me')
class UserInfo(MethodView):
    init_every_request = False

    @requires_token
    def get(self, token: dict[str, Any], client_repo: ClientRepository = Provide[Container.client_repo]) -> Response:
        client = client_repo.get(token['cid'])

        if client is None:
            return error_response('Client not found.', 404)

        is_admin: bool = token['role'] == Role.ADMIN.value

        return json_response(client_to_dict(client, include_plan=is_admin), 200)


@class_route(blp, '/api/v1/clients/<client_id>')
class RetrieveClient(MethodView):
    init_every_request = False

    def get(self, client_id: str, client_repo: ClientRepository = Provide[Container.client_repo]) -> Response:
        if is_valid_uuid4(client_id) is False:
            return error_response('Invalid client ID.', 400)

        client = client_repo.get(client_id)

        if client is None:
            return error_response('Client not found.', 404)

        return json_response(client_to_dict(client), 200)
