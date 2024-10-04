import json
from flask import Blueprint, Response, request
from flask.views import MethodView
from dependency_injector.wiring import inject, Provide
from .util import class_route
from containers import Container
from repositories import ClientRepository

blp = Blueprint("Reset database", __name__)


@class_route(blp, "/api/v1/reset/client")
class ResetDB(MethodView):
    init_every_request = False

    @inject
    def post(self, client_repo: ClientRepository = Provide[Container.client_repo],) -> Response:
        client_repo.reset(request.args.get('demo', '0') == '1')
        return Response(json.dumps({'status': 'Ok'}), status=200, mimetype='application/json')
