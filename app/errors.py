"""Uniform error format required by SAD section 4.4:
{ "error": { "code", "message", "details" } }
"""
from flask import jsonify, request
from werkzeug.exceptions import HTTPException


def error_response(code, message, details=None, status=400):
    body = {"error": {"code": code, "message": message, "details": details or {}}}
    return jsonify(body), status


def register_error_handlers(app, jwt):
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        if request.path.startswith("/api/"):
            code = exc.name.upper().replace(" ", "_")
            return error_response(code, exc.description, status=exc.code)
        return exc

    @jwt.unauthorized_loader
    def missing_token(reason):
        return error_response("UNAUTHORIZED", "Authentication required.",
                              {"reason": reason}, 401)

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error_response("UNAUTHORIZED", "Invalid token.", {"reason": reason}, 401)

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return error_response("UNAUTHORIZED", "Token has expired.", status=401)
