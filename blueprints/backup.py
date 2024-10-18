from datetime import UTC, datetime

import requests
from dependency_injector.wiring import Provide
from flask import Blueprint, Response, current_app
from flask.views import MethodView

from containers import Container

from .util import class_route, json_response

blp = Blueprint('Backup', __name__)


@class_route(blp, '/api/v1/backup/client')
class Backup(MethodView):
    init_every_request = False

    def post(
        self,
        project_id: str = Provide[Container.config.project_id],
        database: str = Provide[Container.config.firestore.database],
        access_token: str = Provide[Container.access_token],
    ) -> Response:
        timestamp = datetime.now(UTC).replace(hour=7, minute=0, second=0, microsecond=0).isoformat().replace('+00:00', 'Z')

        res = requests.post(
            f'https://firestore.googleapis.com/v1/projects/{project_id}/databases/{database}:exportDocuments',
            json={
                'outputUriPrefix': f'gs://{project_id}-backup/firestore/{database}/{timestamp}',
                'snapshotTime': timestamp,
            },
            headers={
                'Authorization': f'Bearer {access_token}',
            },
            timeout=10,
        )

        if res.status_code != requests.codes.ok:
            current_app.logger.error(res.json())
            return json_response({'status': 'Error'}, 500)

        return json_response({'status': 'Ok'}, 200)
