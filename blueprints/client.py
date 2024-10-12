from dependency_injector.wiring import Provide
from flask import Blueprint, Response
from flask.views import MethodView

from containers import Container
from repositories import ClientRepository

from .util import class_route, error_response, is_valid_uuid4, json_response

blp = Blueprint('Clients', __name__)


@class_route(blp, '/api/v1/clients')
class ListClients(MethodView):
    init_every_request = False

    def get(self, client_repo: ClientRepository = Provide[Container.client_repo]) -> Response:
        clients = [
            {
                'id': client.id,
                'name': client.name,
            }
            for client in client_repo.get_all()
        ]

        return json_response(clients, 200)


@class_route(blp, '/api/v1/clients/<client_id>')
class RetrieveClient(MethodView):
    init_every_request = False

    def get(self, client_id: str, client_repo: ClientRepository = Provide[Container.client_repo]) -> Response:
        if is_valid_uuid4(client_id) is False:
            return error_response('Invalid client ID.', 400)

        client = client_repo.get(client_id)

        if client is None:
            return error_response('Client not found.', 404)

        resp = {
            'id': client.id,
            'name': client.name,
        }

        return json_response(resp, 200)
