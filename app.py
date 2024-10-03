import os
from flask import Flask
from gcp_microservice_utils import setup_cloud_logging, setup_cloud_trace, setup_apigateway
from containers import Container
from blueprints import BlueprintHealth, BlueprintAuth, BlueprintReset


class FlaskMicroservice(Flask):
    container: Container


def create_app() -> FlaskMicroservice:
    if os.getenv('ENABLE_CLOUD_LOGGING') == '1':
        setup_cloud_logging()

    app = FlaskMicroservice(__name__)
    app.container = Container()

    app.container.config.firestore.database.from_env("FIRESTORE_DATABASE", "(default)")

    if 'JWT_ISSUER' in os.environ:
        app.container.config.jwt.issuer.from_env("JWT_ISSUER")

    if 'JWT_PRIVATE_KEY' in os.environ:
        app.container.config.jwt.private_key.from_env(
            "JWT_PRIVATE_KEY",
            as_= lambda x: None if x is None else '-----BEGIN PRIVATE KEY-----\n' + x + '\n-----END PRIVATE KEY-----\n'
        )

    if os.getenv('ENABLE_CLOUD_TRACE') == '1':
        setup_cloud_trace(app)

    setup_apigateway(app)

    app.register_blueprint(BlueprintHealth)
    app.register_blueprint(BlueprintAuth)
    app.register_blueprint(BlueprintReset)

    return app
