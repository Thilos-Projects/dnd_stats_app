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

Run with:
  python rest_api.py                 — uses waitress (production) if installed,
                                       otherwise Flask's built-in dev server.
  Set DEBUG=1 to enable debug mode (Flask dev server only, never in production).
  Set HOST / PORT env vars to override the listening address / port.
"""

from __future__ import annotations

import inspect
import os
import traceback
from typing import Any, Callable

from flask import Flask, jsonify, request, send_from_directory

import api
import _global_resources
import stat_engine

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Describes every exposed route for the HTML test client (see static/index.html).
_ENDPOINT_META: list[dict[str, Any]] = []

# Exposed only through the custom wrappers below, not auto-wired.
_CUSTOM_HANDLED = {"load_and_compute", "validate_all", "TestUsers", "TestForStatSheetTemplate", "TestForGlobalDocuments", "TestForUserFolder"}
# Not callable endpoints (classes / exception types).
_NOT_ENDPOINTS = {"StatSheetEngine", "FormulaError", "CircularReferenceError", "CouldNotReach"}


_DEBUG = os.environ.get("DEBUG", "").strip() not in ("", "0", "false", "False")


def _error_response(error: Exception) -> tuple[Any, int]:
    if isinstance(error, PermissionError):
        status = 403
    elif isinstance(error, FileNotFoundError):
        status = 404
    elif isinstance(error, (ValueError, TypeError)):
        status = 400
    else:
        status = 500
    payload: dict[str, Any] = {
        "error": str(error),
        "exception": type(error).__name__,
    }
    if _DEBUG:
        # Expose full details only when running locally in debug mode.
        # Never send tracebacks over the internet – they reveal internal paths
        # and code structure that attackers can exploit.
        payload["exception_module"] = type(error).__module__
        payload["args"] = [repr(argument) for argument in error.args]
        payload["traceback"] = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        if error.__cause__ is not None or error.__context__ is not None:
            cause = error.__cause__ or error.__context__
            payload["cause"] = f"{type(cause).__name__}: {cause}"
    return jsonify(payload), status


def _describe(name: str, func: Callable[..., Any] | None, parameters: list[dict[str, Any]] | None = None) -> None:
    if parameters is None:
        parameters = []
        for param_name, parameter in inspect.signature(func).parameters.items():
            parameters.append(
                {
                    "name": param_name,
                    "required": parameter.default is inspect.Parameter.empty,
                    "default": None if parameter.default is inspect.Parameter.empty else repr(parameter.default),
                }
            )
    _ENDPOINT_META.append({"name": name, "parameters": parameters})


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
    _describe(_name, _func)


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


_describe("load_and_compute", None, [{"name": "character_id", "required": True, "default": None}])
_describe("validate_all", None, [])
_ENDPOINT_META.sort(key=lambda entry: entry["name"].lower())


@app.route("/api/_endpoints", methods=["GET"])
def endpoints_view() -> Any:
    return jsonify(_ENDPOINT_META)


@app.route("/", methods=["GET"], strict_slashes=False)
def index_view() -> Any:
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))

    try:
        from waitress import serve  # type: ignore[import-untyped]

        # waitress is a production-grade pure-Python WSGI server: multi-threaded,
        # no debug reloader, no sensitive error pages – safe for internet use.
        threads = int(os.environ.get("THREADS", "8"))
        print(f"Starting waitress on {host}:{port} (threads={threads})")
        serve(app, host=host, port=port, threads=threads)
    except ImportError:
        # Fall back to Flask's built-in server for local development only.
        # It is single-threaded and not suitable for public internet exposure.
        print("waitress not installed – falling back to Flask development server (not for production use)")
        app.run(host=host, port=port, debug=_DEBUG)
