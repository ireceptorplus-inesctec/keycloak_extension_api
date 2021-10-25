import jsonify
import requests
from flask import Flask, request, abort, jsonify
import psycopg2
import os

app = Flask(__name__)

def start_connection():
    try:
        return psycopg2.connect(
            database=os.environ['DB_DATABASE'], user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'],
            host=os.environ['DB_HOST'], port=os.environ['DB_PORT']
        )
    except:
        abort(401, "Could not connect to DB")

def check_request_validity(auth_header):
    if auth_header == None:
        abort(401, 'No token')

    if get_user_info(auth_header[7:])['sub'] != request.form['owner_id']:
        abort(401, 'Request can only be made by the resource owner')

def get_user_info(token):
    url = os.environ['KEYCLOAK_URL'] \
        + 'realms/' \
        + os.environ['REALM'] \
        + '/protocol/openid-connect/userinfo'

    headers = {
        'Authorization': 'Bearer ' + token
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        abort(401, 'Invalid token')

    return response.json()

def get_user_id(email_user):
    conn = start_connection()

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM user_entity WHERE email LIKE '{0}' OR username LIKE '{0}' OR id LIKE '{0}'".format(email_user))

        id = cursor.fetchone()[0]
    except:
        abort(401, "Could not find user")

    cursor.close()
    conn.close()

    return id

def get_scope_id(scope_name):
    conn = start_connection()

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM resource_server_scope WHERE name LIKE '{0}'".format(scope_name))

        id = cursor.fetchone()[0]
    except:
        abort(401, "Could not find scope")

    cursor.close()
    conn.close()

    return id

@app.route('/get_user_scope_id/<email_user>', methods=['POST'])
def get_user_scope_id(email_user):
    auth_header = request.headers.get('Authorization')

    check_request_validity(auth_header)

    user_id = get_user_id(email_user)

    scope_id = get_scope_id(request.form['scope_name'])

    return jsonify([user_id, scope_id])

@app.route('/change_owner/<resource_id>/<new_owner>', methods=['POST'])
def change_owner(resource_id, new_owner):
    auth_header = request.headers.get('Authorization')

    check_request_validity(auth_header)

    conn = start_connection()

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT owner FROM resource_server_resource WHERE id LIKE '{0}'".format(resource_id))

        resource_owner_id = cursor.fetchone()[0]
    except:
        abort(404, "Could not find resource")

    if resource_owner_id != get_user_info(auth_header[7:])['sub']:
        abort(401, "Not owner of resource")

    try:
        cursor.execute("SELECT id FROM user_entity WHERE email LIKE '{0}' OR username LIKE '{0}' OR id LIKE '{0}'".format(new_owner))

        new_owner_id = cursor.fetchone()[0]
    except:
        abort(401, "Could not find user")

    try:
        owner_update = "UPDATE resource_server_resource " + \
            "SET owner = '{0}' " + \
            "WHERE id LIKE '{1}'"
        cursor.execute(owner_update.format(new_owner_id, resource_id))
    except:
        abort(401, "Update failed")
    
    conn.commit()
    
    cursor.close()

    conn.close()

    return jsonify("Owner changed successfully")

@app.errorhandler(401)
def unauthorized(error):
    response = jsonify({'message': error.description})
    response.status_code = 401
    return response

@app.errorhandler(500)
def internal_error(error):
    return "Uncaught exception: is keycloak reachable?"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
