import os
from flask import Flask
from gcp_microservice_utils import setup_cloud_logging, setup_cloud_trace, setup_apigateway
from containers import Container
from blueprints import BlueprintHealth, BlueprintAuth, BlueprintReset


def create_app() -> Flask:
    if os.getenv('ENABLE_CLOUD_LOGGING') == '1':
        setup_cloud_logging()

    container = Container()
    container.config.firestore.database.from_env("FIRESTORE_DATABASE", "(default)")
    container.config.jwt.issuer.from_env("JWT_ISSUER", required=True)
    container.config.jwt.private_key.from_env(
        "JWT_PRIVATE_KEY",
        required=True,
        as_= lambda x: '-----BEGIN PRIVATE KEY-----\n' + x + '\n-----END PRIVATE KEY-----\n'
    )

    app = Flask(__name__)

    if os.getenv('ENABLE_CLOUD_TRACE') == '1':
        setup_cloud_trace(app)

    setup_apigateway(app)

    app.register_blueprint(BlueprintHealth)
    app.register_blueprint(BlueprintAuth)
    app.register_blueprint(BlueprintReset)

    return app
