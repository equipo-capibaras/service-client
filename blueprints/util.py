import json
from collections.abc import Callable
from typing import Any

from flask import Blueprint, Response
from flask.views import MethodView
from marshmallow import ValidationError


def class_route(blueprint: Blueprint, rule: str, **options: Any) -> Callable[[type[MethodView]], type[MethodView]]:  # noqa: ANN401
    def decorator(cls: type[MethodView]) -> type[MethodView]:
        blueprint.add_url_rule(rule, view_func=cls.as_view(cls.__name__), **options)
        return cls

    return decorator


def json_response(data: dict[str, Any], status: int) -> Response:
    return Response(json.dumps(data), status=status, mimetype='application/json')


def error_response(msg: str, code: int) -> Response:
    return json_response({'message': msg, 'code': code}, code)


def validation_error_response(err: ValidationError) -> Response:
    if isinstance(err.messages, dict):
        msg = ' '.join([f'Invalid value for {k}: {" ".join(v)}' for k, v in err.messages.items()])
        return error_response(msg, 400)

    raise NotImplementedError('Validation error response for non-dict messages not implemented.')
