from dependency_injector.wiring import Provide
from flask import Blueprint, Response
from flask.views import MethodView

from containers import Container
from repositories import ClientRepository

from .util import class_route, json_response

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
