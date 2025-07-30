from flask import render_template, request
from . import main

@main.app_errorhandler(400)
def bad_request(e):
    print(f"400 Bad Request: {e}")
    print(f"Request URL: {request.url}")
    print(f"Request method: {request.method}")
    print(f"Request form: {request.form}")
    print(f"Request headers: {dict(request.headers)}")
    return render_template('400.html'), 400

@main.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500