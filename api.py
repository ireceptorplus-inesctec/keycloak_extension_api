import json
import jsonify
import requests
from flask import Flask, request, abort, jsonify
import psycopg2
import random
import string
import uuid
import time
import os

app = Flask(__name__)

SERVERS = ['immunedb', 'scireptor', 'turnkey']

POLICY_INSERT = "INSERT INTO resource_server_policy " + \
    "(id, name, type, resource_server_id, owner) " + \
    "VALUES " + \
    "('{0}', '{1}', 'uma', '{2}', '{3}')"

TICKET_INSERT = "INSERT INTO resource_server_perm_ticket " + \
    "(id, owner, requester, created_timestamp, granted_timestamp, resource_id, scope_id, resource_server_id, policy_id) " + \
    "VALUES " + \
    "('{0}', '{1}', '{2}', '{3}', '{3}', '{4}', '{5}', '{6}', '{7}')"

def start_connection():
    try:
        return psycopg2.connect(
            database=os.environ['DB_DATABASE'], user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'],
            host=os.environ['DB_HOST'], port=os.environ['DB_PORT']
        )
    except:
        abort(401, "Could not connect to DB")

def check_request_validity(auth_header, where):
    if auth_header == None:
        abort(401, 'No token')

    if where not in SERVERS:
        abort(401, 'Server does not exist')

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
        cursor.execute("SELECT id FROM user_entity WHERE email LIKE '{0}' OR username LIKE '{0}'".format(email_user))

        id = cursor.fetchone()[0]
    except:
        abort(401, "Could not find user")

    cursor.close()
    conn.close()

    return id

@app.route('/give_access/<where>', methods=['POST'])
def give_access(where):
    auth_header = request.headers.get('Authorization')

    check_request_validity(auth_header, where)

    conn = start_connection()

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM client WHERE client_id LIKE '{0}'".format(where))

        resource_server_id = cursor.fetchone()[0]
    except:
        abort(401, "Could not find client")

    policy_id = uuid.uuid1()

    try:
        cursor.execute(POLICY_INSERT.format(policy_id, uuid.uuid1(), resource_server_id, request.form['owner_id']))
    except:
        abort(401, "Could not create ticket, maybe permission already exists?")

    try:
        cursor.execute("SELECT id FROM resource_server_scope WHERE name LIKE '{0}' AND resource_server_id LIKE '{1}'".format(request.form['scope_name'], resource_server_id))

        scope_id = cursor.fetchone()[0]
    except:
        abort(401, "Could not find scope")

    current_time = int(round(time.time() * 1000))

    requester_id = get_user_id(request.form['requester'])

    try:
        cursor.execute(TICKET_INSERT.format(uuid.uuid1(), request.form['owner_id'], requester_id, current_time, request.form['resource_id'], scope_id, resource_server_id, policy_id))
    except:
        abort(401, "Could not create ticket, maybe permission already exists?")

    conn.commit()

    cursor.close()

    conn.close()

    return jsonify("Ticket created successfully")

@app.errorhandler(401)
def unauthorized(error):
    response = jsonify({'message': error.description})
    response.status_code = 401
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
