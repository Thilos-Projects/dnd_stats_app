"""Minimal REST API exposing the public functions documented in API.md.

Every function re-exported by `api.py` gets one POST route at
`/api/<functionName>`, taking a JSON body whose keys match the function's
parameter names exactly and returning the function's return value as JSON.
POST is used uniformly (including for read-only calls) because almost every
call carries a `password_hash` credential, which must not be sent as a URL
query parameter (logged in server/proxy access logs, browser history, etc.).

Two functions are wrapped instead of auto-exposed, purely for security reasons:
- `load_and_compute` normally takes a raw filesystem path. Accepting an
  arbitrary path from a client would allow path traversal / arbitrary file
  read, so the REST route instead takes a `character_id` and resolves the
  matching `StatSheet.json` path itself.
- The individual `validate_data.TestX` functions are chained internally
  (`TestForUserFolder` needs the return values of the others) and are not
  meant to be called standalone; only the combined `validate_all` entry
  point (as recommended by API.md) is exposed.

Run with: `python rest_api.py` (development server) or via a WSGI server
pointing at `rest_api:app`.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

from flask import Flask, jsonify, request

import api
import _global_resources
import stat_engine

app = Flask(__name__)

# Exposed only through the custom wrappers below, not auto-wired.
_CUSTOM_HANDLED = {"load_and_compute", "validate_all", "TestUsers", "TestForStatSheetTemplate", "TestForGlobalDocuments", "TestForUserFolder"}
# Not callable endpoints (classes / exception types).
_NOT_ENDPOINTS = {"StatSheetEngine", "FormulaError", "CircularReferenceError", "CouldNotReach"}


def _error_response(error: Exception) -> tuple[Any, int]:
    if isinstance(error, PermissionError):
        return jsonify({"error": str(error)}), 403
    if isinstance(error, (ValueError, TypeError)):
        return jsonify({"error": str(error)}), 400
    if isinstance(error, FileNotFoundError):
        return jsonify({"error": str(error)}), 404
    return jsonify({"error": str(error)}), 500


def _make_view(func: Callable[..., Any]) -> Callable[[], Any]:
    signature = inspect.signature(func)

    def view() -> Any:
        body = request.get_json(silent=True) or {}
        kwargs = {}
        for name, parameter in signature.parameters.items():
            if name in body:
                kwargs[name] = body[name]
            elif parameter.default is inspect.Parameter.empty:
                return jsonify({"error": f"Missing required parameter '{name}'"}), 400
        try:
            result = func(**kwargs)
        except Exception as error:  # noqa: BLE001 - deliberately broad, translated to HTTP status below
            return _error_response(error)
        return jsonify(result)

    return view


for _name in api.__all__:
    if _name in _NOT_ENDPOINTS or _name in _CUSTOM_HANDLED:
        continue
    _func = getattr(api, _name)
    if not callable(_func):
        continue
    app.add_url_rule(f"/api/{_name}", endpoint=_name, view_func=_make_view(_func), methods=["POST"])


@app.route("/api/load_and_compute", methods=["POST"])
def load_and_compute_view() -> Any:
    body = request.get_json(silent=True) or {}
    character_id = body.get("character_id")
    if not character_id:
        return jsonify({"error": "Missing required parameter 'character_id'"}), 400
    try:
        character_path, _, _ = _global_resources.find_character(character_id)
        result = stat_engine.load_and_compute(character_path / "StatSheet.json")
    except Exception as error:  # noqa: BLE001
        return _error_response(error)
    return jsonify(result)


@app.route("/api/validate_all", methods=["POST"])
def validate_all_view() -> Any:
    try:
        api.validate_all()
    except Exception as error:  # noqa: BLE001
        return _error_response(error)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=False)
