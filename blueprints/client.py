import uuid
from dataclasses import dataclass, field
from typing import Any

import marshmallow.validate
import marshmallow_dataclass
from dependency_injector.wiring import Provide
from flask import Blueprint, Response, request
from flask.views import MethodView
from marshmallow import ValidationError

from containers import Container
from models import Client, Plan, Role
from repositories import ClientRepository
from repositories.errors import DuplicateEmailError

from .util import class_route, error_response, is_valid_uuid4, json_response, requires_token, validation_error_response

blp = Blueprint('Clients', __name__)


def client_to_dict(client: Client, *, include_plan: bool = False) -> dict[str, Any]:
    res: dict[str, Any] = {
        'id': client.id,
        'name': client.name,
        'emailIncidents': client.email_incidents,
    }

    if include_plan:
        res['plan'] = None if client.plan is None else client.plan.value

    return res


@class_route(blp, '/api/v1/clients')
class ListClients(MethodView):
    init_every_request = False

    def get(self, client_repo: ClientRepository = Provide[Container.client_repo]) -> Response:
        clients = [client_to_dict(client) for client in client_repo.get_all()]

        return json_response(clients, 200)


@dataclass
class RegisterClientBody:
    name: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=60)})
    prefixEmailIncidents: str = field(  # noqa: N815
        metadata={
            'validate': [
                marshmallow.validate.Length(min=1, max=60),
                marshmallow.validate.Regexp(r'^[a-zA-Z0-9._%+-]+$', error='Invalid email prefix'),
            ]
        }
    )


@class_route(blp, '/api/v1/clients')
class CreateClient(MethodView):
    init_every_request = False

    def post(self, client_repo: ClientRepository = Provide[Container.client_repo]) -> Response:
        client_schema = marshmallow_dataclass.class_schema(RegisterClientBody)()
        req_json = request.get_json(silent=True)

        if req_json is None:
            return error_response('The request body could not be parsed as valid JSON.', 400)

        # Validate request body
        try:
            data: RegisterClientBody = client_schema.load(req_json)
        except ValidationError as err:
            return validation_error_response(err)

        client = Client(
            id=str(uuid.uuid4()),
            name=data.name,
            email_incidents=data.prefixEmailIncidents + '@capibaras.io',
            plan=None,
        )

        try:
            client_repo.create(client)
        except DuplicateEmailError:
            return error_response('Email already registered.', 409)

        return json_response(client_to_dict(client, include_plan=True), 201)


@class_route(blp, '/api/v1/clients/me')
class ClientInfo(MethodView):
    init_every_request = False

    @requires_token
    def get(self, token: dict[str, Any], client_repo: ClientRepository = Provide[Container.client_repo]) -> Response:
        client = client_repo.get(token['cid'])

        if client is None:
            return error_response('Client not found.', 404)

        is_admin: bool = token['role'] == Role.ADMIN.value

        return json_response(client_to_dict(client, include_plan=is_admin), 200)


@class_route(blp, '/api/v1/clients/me/plan/<plan>')
class SelectPlan(MethodView):
    init_every_request = False

    @requires_token
    def post(
        self, plan: str, token: dict[str, Any], client_repo: ClientRepository = Provide[Container.client_repo]
    ) -> Response:
        if token['aud'] != Role.ADMIN:
            return error_response('You do not have access to this resource.', 403)

        try:
            plan = Plan(plan)
        except ValueError:
            return error_response('Invalid plan.', 400)

        client = client_repo.get(token['cid'])

        if client is None:
            return error_response('Client not found.', 404)

        client.plan = plan
        client_repo.update(client)

        return json_response(client_to_dict(client, include_plan=True), 200)


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
