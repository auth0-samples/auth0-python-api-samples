from flask import Flask, jsonify
from flask_jwt_simple import JWTManager, get_jwt_identity, jwt_required
from jwt.algorithms import RSAAlgorithm
from os import environ as env
import requests
import json

# if we have a jkws key file, we can use that for our public RSA key. Let's assume we need the first key.
if env.get('JWKS_FILE', False):
    with open(env.get('JWKS_FILE')) as jwks_file:
        key_jwk = json.dumps(json.load(jwks_file)['keys'][0])
# else, we download the jwks key file from our auth0 tenant and again, use the first key
else:
    if not env.get('AUTH0_DOMAIN'):
        print('AUTH0_DOMAIN not specified')
        exit(1)

    jwks = requests.get('https://{}/.well-known/jwks.json'.format(env.get('AUTH0_DOMAIN'))).json()
    key_jwk = json.dumps(jwks['keys'][0])

app = Flask(__name__)

# configure flask_jwt_simple
app.config['JWT_ALGORITHM'] = 'RS256'
app.config['JWT_PUBLIC_KEY'] = RSAAlgorithm.from_jwk(key_jwk)
app.config['JWT_DECODE_AUDIENCE'] = env.get('AUTH0_AUDIENCE')
jwt = JWTManager(app)


@app.route('/example', methods=['GET', 'POST', 'PUT'])
@jwt_required
def example_controller():
    """
    simple controller that requires a valid jwt auth header
    """
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


# start the server
app.run(host="0.0.0.0", port=env.get("PORT", 3010))
