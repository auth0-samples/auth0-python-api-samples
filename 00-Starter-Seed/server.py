"""Python Flask API Auth0 integration example
"""

from functools import wraps
import json
from os import environ as env
from six.moves.urllib.request import urlopen

from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, jsonify, _request_ctx_stack
from flask_cors import cross_origin
from jose import jwt
from flask_caching import Cache

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
AUTH0_DOMAIN = env.get("AUTH0_DOMAIN")
API_IDENTIFIER = env.get("API_IDENTIFIER")
AUTH0_ISSUER = "https://" + AUTH0_DOMAIN + "/"
AUTH0_JWKS = "https://" + AUTH0_DOMAIN + "/.well-known/jwks.json"
ALGORITHMS = ["RS256"]

app = Flask(__name__)

config = {
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 0
}

cache = Cache(app, config=config)


# Format error response and append status code.
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


def get_public_key(token, get_from_cache=True):
    """Obtain the public key from JWKS
    Args:
        token (str): Bearer token
        get_from_cache (Boolean): If It's True get public key from cache,
                                  otherwise fetch from JWKS
    Returns:
        dict: A dictionary with JWK
    """
    rsa_key = cache.get('rsa_key')
    if rsa_key is not None and get_from_cache:
        return rsa_key

    jwks_url = urlopen(AUTH0_JWKS)
    jwks = json.loads(jwks_url.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Invalid header. "
                             "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Invalid header. "
                             "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }

    if rsa_key:
        cache.set('rsa_key', rsa_key)
        return rsa_key
    else:
        raise AuthError({"code": "invalid_header",
                         "description": "Unable to find appropriate key"}, 401)


def get_token_auth_header():
    """Obtains the access token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                        "description":
                            "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must start with"
                            " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must be"
                            " Bearer token"}, 401)

    token = parts[1]
    return token


def requires_scope(required_scope):
    """Determines if the required scope is present in the access token
    Args:
        required_scope (str): The scope required to access the resource
    """
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("scope"):
        token_scopes = unverified_claims["scope"].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
    return False


def decode_jwt(token, rsa_key):
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_IDENTIFIER,
            issuer=AUTH0_ISSUER
        )
    except jwt.ExpiredSignatureError:
        raise AuthError({"code": "token_expired",
                         "description": "token is expired"}, 401)
    except jwt.JWTClaimsError:
        raise AuthError({"code": "invalid_claims",
                         "description":
                             "incorrect claims,"
                             " please check the audience and issuer"}, 401)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_signature",
                         "description": "The signature is invalid"}, 401)
    except Exception:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Unable to parse authentication"
                             " token."}, 401)
    return payload


def requires_auth(f):
    """Determines if the access token is valid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        rsa_key = get_public_key(token)

        # Try to decode with the cached JWKS key.
        # If it fails, it could be because the JWKS key expired, so we retrieve it
        # from the JWKS endpoint and try decoding again.

        try:
            payload = decode_jwt(token, rsa_key)
        except AuthError as ex:
            if ex.error["code"] == "invalid_signature":
                rsa_key = get_public_key(token, False)
                payload = decode_jwt(token, rsa_key)

        _request_ctx_stack.top.current_user = payload

        return f(*args, **kwargs)
    return decorated


# Controllers API
@app.route("/api/public")
@cross_origin(headers=["Content-Type", "Authorization"])
def public():
    """No access token required to access this route
    """
    response = "Hello from a public endpoint! You don't need to be authenticated to see this."
    return jsonify(message=response)


@app.route("/api/private")
@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "*"])
@requires_auth
def private():
    """A valid access token is required to access this route
    """
    response = "Hello from a private endpoint! You need to be authenticated to see this."
    return jsonify(message=response)


@app.route("/api/private-scoped")
@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "*"])
@requires_auth
def private_scoped():
    """A valid access token and an appropriate scope are required to access this route
    """
    if requires_scope("read:messages"):
        response = "Hello from a private endpoint! You need to be authenticated and have a scope of read:messages to see this."
        return jsonify(message=response)
    raise AuthError({
        "code": "Unauthorized",
        "description": "You don't have access to this resource"
    }, 403)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3010))
