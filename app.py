import os

from flask import Flask
from gcp_microservice_utils import setup_apigateway, setup_cloud_logging, setup_cloud_trace

from blueprints import BlueprintAuth, BlueprintBackup, BlueprintClient, BlueprintEmployee, BlueprintHealth, BlueprintReset
from containers import Container


class FlaskMicroservice(Flask):
    container: Container


def create_app() -> FlaskMicroservice:
    if os.getenv('ENABLE_CLOUD_LOGGING') == '1':
        setup_cloud_logging()  # pragma: no cover

    app = FlaskMicroservice(__name__)
    app.container = Container()

    app.container.config.firestore.database.from_env('FIRESTORE_DATABASE', '(default)')

    if 'K_SERVICE' in os.environ:  # pragma: no cover
        import google.auth

        _, project_id = google.auth.default()  # type: ignore[no-untyped-call]
        app.container.config.project_id.from_value(project_id)

    if 'JWT_ISSUER' in os.environ:
        app.container.config.jwt.issuer.from_env('JWT_ISSUER')  # pragma: no cover

    if 'DOMAIN' in os.environ:
        app.container.config.domain.from_env('DOMAIN')  # pragma: no cover

    if 'JWT_PRIVATE_KEY' in os.environ:
        app.container.config.jwt.private_key.from_env(
            'JWT_PRIVATE_KEY',
            as_=lambda x: None if x is None else '-----BEGIN PRIVATE KEY-----\n' + x + '\n-----END PRIVATE KEY-----\n',
        )  # pragma: no cover

    if os.getenv('ENABLE_CLOUD_TRACE') == '1':
        setup_cloud_trace(app)  # pragma: no cover

    setup_apigateway(app)

    app.register_blueprint(BlueprintAuth)
    app.register_blueprint(BlueprintBackup)
    app.register_blueprint(BlueprintClient)
    app.register_blueprint(BlueprintEmployee)
    app.register_blueprint(BlueprintHealth)
    app.register_blueprint(BlueprintReset)

    return app
