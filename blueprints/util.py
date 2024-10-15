import json
from collections.abc import Callable
from typing import Any, cast
from uuid import UUID

from flask import Blueprint, Request, Response, request
from flask.views import MethodView
from marshmallow import ValidationError
from tightwrap import wraps


class APIGatewayRequest(Request):
    user_token: dict[str, Any]


def class_route(blueprint: Blueprint, rule: str, **options: Any) -> Callable[[type[MethodView]], type[MethodView]]:  # noqa: ANN401
    def decorator(cls: type[MethodView]) -> type[MethodView]:
        blueprint.add_url_rule(rule, view_func=cls.as_view(cls.__name__), **options)
        return cls

    return decorator


def is_valid_uuid4(uuid: str) -> bool:
    try:
        UUID(uuid, version=4)
    except ValueError:
        return False

    return True


def json_response(data: dict[str, Any] | list[dict[str, Any]], status: int) -> Response:
    return Response(json.dumps(data), status=status, mimetype='application/json')


def error_response(msg: str, code: int) -> Response:
    return json_response({'message': msg, 'code': code}, code)


def validation_error_response(err: ValidationError) -> Response:
    if isinstance(err.messages, dict):
        msg = ' '.join([f'Invalid value for {k}: {" ".join(v)}' for k, v in err.messages.items()])
        return error_response(msg, 400)

    raise NotImplementedError('Validation error response for non-dict messages not implemented.')  # pragma: no cover


def requires_token(f: Callable[..., Response]) -> Callable[..., Response]:
    @wraps(f)
    def decorated_function(*args, **kwargs) -> Response:  # type: ignore[no-untyped-def] # noqa: ANN002, ANN003
        if hasattr(request, 'user_token') and cast(APIGatewayRequest, request).user_token is not None:
            req = cast(APIGatewayRequest, request)
            token: dict[str, Any] = req.user_token

            required_fields = ['sub', 'cid', 'role', 'aud']
            for field in required_fields:
                if field not in token:
                    return error_response(f'{field} is missing in token', 401)

            return f(*args, token=token, **kwargs)

        return error_response('Token is missing', 401)

    return decorated_function
