import json
import logging
from datetime import datetime, timedelta

import pytest
from flask import Flask
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.jose import JsonWebKey, jwt
from jwcrypto.jwk import JWK
from validator import Auth0JWTBearerTokenValidator

AUDIENCE = "my-audience"
DOMAIN = "my-domain.com"


@pytest.fixture()
def app():
    require_oauth = ResourceProtector()
    validator = Auth0JWTBearerTokenValidator(DOMAIN, AUDIENCE)
    require_oauth.register_token_validator(validator)

    app = Flask(__name__)

    @app.route("/me")
    @require_oauth(None)
    def me_api():
        return {"username": "foo"}

    yield app


@pytest.fixture(autouse=True)
def public_jwk(mocker):
    key = JWK.generate(
        kty="RSA", size=2048, alg="RSA-OAEP-256", use="sig", kid="12345"
    )
    urlopen = mocker.Mock()
    urlopen.read.side_effect = [
        json.dumps(
            {"keys": [json.loads(key.export_public())]}
        )
    ]
    mocker.patch("validator.urlopen", return_value=urlopen)

    yield JsonWebKey.import_key(json.loads(key.export_private()))


def generate_jwt(
    key,
    alg="RS256",
    kid="12345",
    iss=f"https://{DOMAIN}/",
    aud=AUDIENCE,
    exp=datetime.now() + timedelta(days=1),
):
    return jwt.encode(
        {"alg": alg, "kid": kid}, {"iss": iss, "aud": aud, "exp": exp}, key=key
    ).decode("utf-8")


def test_valid_jwt(app, public_jwk):
    token = generate_jwt(public_jwk)
    with app.test_client() as client:
        response = client.get(
            "/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


def test_none_alg(app, public_jwk, caplog):
    caplog.set_level(logging.DEBUG, logger="authlib.oauth2.rfc7523.validator")
    token = generate_jwt("", alg="none")
    response = app.test_client().get(
        "/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json["error"] == "invalid_token"
    assert "bad_signature" in caplog.text


def test_wrong_sig(app, public_jwk, caplog):
    key = JWK.generate(
        kty="RSA", size=2048, alg="RSA-OAEP-256", use="sig", kid="12345"
    )
    caplog.set_level(logging.DEBUG, logger="authlib.oauth2.rfc7523.validator")
    token = generate_jwt(
        JsonWebKey.import_key(json.loads(key.export_private()))
    )
    response = app.test_client().get(
        "/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json["error"] == "invalid_token"
    assert "bad_signature" in caplog.text


def test_invalid_iss(app, public_jwk, caplog):
    caplog.set_level(logging.DEBUG, logger="authlib.oauth2.rfc7523.validator")
    token = generate_jwt(public_jwk, iss="foo")
    response = app.test_client().get(
        "/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json["error"] == "invalid_token"
    assert 'invalid_claim' in caplog.text


def test_invalid_aud(app, public_jwk, caplog):
    caplog.set_level(logging.DEBUG, logger="authlib.oauth2.rfc7523.validator")
    token = generate_jwt(public_jwk, aud="foo")
    response = app.test_client().get(
        "/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json["error"] == "invalid_token"
    assert 'invalid_claim' in caplog.text


def test_expired_jwt(app, public_jwk, caplog):
    caplog.set_level(logging.DEBUG, logger="authlib.oauth2.rfc7523.validator")
    token = generate_jwt(public_jwk, exp=datetime.now() - timedelta(days=1))
    response = app.test_client().get(
        "/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json["error"] == "invalid_token"
    assert "expired_token" in caplog.text
