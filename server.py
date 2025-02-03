from functools import wraps
from os import environ as env
import logging
from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
from werkzeug.routing import Rule
from server_config import Config

from security import (
    requires_auth,
    requires_scope,
    get_user_permissions,
    AuthError
)

"""
Flask app to host routes for mobile client and the UI
to interact with.
The app is single-threaded and therefore relies on global variables
to store the running sums.
"""
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

#log_file = app.config['LOG_FILE']
#logging.basicConfig(filename=log_file, encoding='utf-8', level=logging.DEBUG)

tasks = ["get_eta_data", "post_eta_data"]

data = list()

# dynamic_endpoints = {}

@app.errorhandler(AuthError)
def handle_auth_error(ex: AuthError) -> Response:
    """
    serializes the given AuthError as json and sets the response status code accordingly.
    :param ex: an auth error
    :return: json serialized ex response
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

@app.route("/api/all/get_permissions", methods=["GET", "OPTIONS"])
@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "*"])
@requires_auth
def get_permissions():
    print("Getting permissions...")
    permissions = get_user_permissions()
    print(permissions)

    return jsonify(message="Successful", permissions=permissions, status=200)


@app.route("/api/dev/create_endpoint", methods=["POST", "OPTIONS"])
@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "*"])
@requires_auth
def create_endpoint():
    if requires_scope("create:endpoint"):
        endpoint_name = request.get_json().get("endpoint")
        input_task = request.get_json().get("task")
        
        for endpoint in app.view_functions:
            if endpoint == endpoint_name:
                return "<h1> This endpoint already exists </h1>"

        for task in tasks:
            if input_task == task:
                dynamic_endpoint_handler(endpoint_name, input_task)                
                return "<h1> Success </h1>"
        
        return "<h1> Invalid task or no task provided in the request </h1>"

    else:
        response = "You are not a developer! Please contact the admins to give you developer permissions"
        logging.error(response)
        return jsonify(message=response)


def dynamic_endpoint_handler(endpoint_name, task):
    if task == "get_eta_data":
        rule = Rule(f"/api/scientist/{endpoint_name}", endpoint=endpoint_name, methods=["GET", "OPTIONS"])
        app.url_map.add(rule)
        app.view_functions[endpoint_name] = get_eta_data
    if task == "post_eta_data":
        rule = Rule(f"/api/user/{endpoint_name}", endpoint=endpoint_name, methods=["POST", "OPTIONS"])
        app.url_map.add(rule)
        app.view_functions[endpoint_name] = post_eta_data


@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "*"])
@requires_auth
def get_eta_data():
    global data
    if requires_scope("get:eta-data"):
        return jsonify(message=data)
    else:
        response = "You don't have access to this resource"
        logging.error(response)
        return jsonify(message=response)


# @app.route("/<endpoint_name>", methods=["POST"])
@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "*"])
@requires_auth
def post_eta_data():
    if requires_scope("post:eta-data"):
        global data
        if len(data) == 0:
            data = request.get_json().get("data")
            return jsonify({"message": "Data received successfully"})
        else:
            client_data = request.get_json()["data"]
            data = [a + b for a, b in zip(client_data, data)]
            return jsonify({"message": "Data received successfully"})
    else:
        error = AuthError({
            "code": "Unauthorized",
            "description": "You don't have access to this resource"
        }, 403)

        logging.erro(error)
        
        raise error
    

@app.route("/api/admin/clear", methods=["POST"])
@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "*"])
@requires_auth
def clear_data():
    if requires_scope("admin:tasks"):
        data.clear()
        return jsonify({"message": "Data cleared successfully"})
    else:
        return jsonify({"message": "You don't have admin accessibility"})
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT"), debug=True)
