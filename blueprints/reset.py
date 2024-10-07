import json

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, Response, request
from flask.views import MethodView

from containers import Container
from repositories import ClientRepository

from .util import class_route

blp = Blueprint('Reset database', __name__)


@class_route(blp, '/api/v1/reset/client')
class ResetDB(MethodView):
    init_every_request = False

    @inject
    def post(
        self,
        client_repo: ClientRepository = Provide[Container.client_repo],
    ) -> Response:
        client_repo.reset(load_demo_data=request.args.get('demo', 'false') == 'true')
        return Response(json.dumps({'status': 'Ok'}), status=200, mimetype='application/json')
