import json
import unittest
from unittest.mock import patch
from os import environ as env
from six.moves.urllib.request import urlopen

from jose import jwt
from dotenv import load_dotenv, find_dotenv

from server import app, get_public_key

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
AUTH0_DOMAIN = env.get("AUTH0_DOMAIN")
API_IDENTIFIER = env.get("API_IDENTIFIER")
AUTH0_ISSUER = "https://" + AUTH0_DOMAIN + "/"
AUTH0_JWKS = "https://" + AUTH0_DOMAIN + "/.well-known/jwks.json"

jwks_url = urlopen(AUTH0_JWKS)
jwks = json.loads(jwks_url.read())
public_key = {}
for key in jwks["keys"]:
    public_key = {
        "kty": key["kty"],
        "kid": key["kid"],
        "use": key["use"],
        "n": key["n"],
        "e": key["e"]
    }

new_public_key = {
    "kty": "RSA",
    "use": "sig",
    "n": "ms_PVSS-I8C4jktuFWejUG0rE5u_kYrNQTH9vaaet3zqjOy7_d3AMA2DbIenQBUy5oPwcN7ePPEcxmiKiSY0n-"
         "XsvBHEWl89hto84azMI_V_55OEFEmvdMAvkgtAzpGyNd0sD1xb7dATphKZ7iMprhy3YjfGmJD2cfVyOSW71LTF"
         "GN2jzSfSelqPrmKmxzGRONTHdv2zNeqvftOMIMKVqXCddxdHPHf-dPOoG2-3epexcOi34rN_FMcKVFF5vODOQG"
         "INiKOFvGFBD18WK0fPT7FOoSQ4ttUfHhzjW9Sw2vZLBdk131CqH9LmvTnG3Gh6RRKBynIW0IjEVjAKzh3YNw",
    "e": "AQAB",
    "kid": "keyid"
}


def mock_get_public_key():
    return [public_key, new_public_key]


def mock_cache_get():
    return [None, new_public_key, new_public_key, new_public_key]


class JWKRotationTestCase(unittest.TestCase):

    def setUp(self):
        # Setup Flask test app test client
        app.testing = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        # Test private key for signin tokens
        private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAms/PVSS+I8C4jktuFWejUG0rE5u/kYrNQTH9v" \
                      "aaet3zqjOy7/d3AMA2DbIenQBUy5oPwcN7ePPEcxmiKiSY0n+XsvBHEWl89hto84azMI/V/55OEFEmvdMAvkgt" \
                      "AzpGyNd0sD1xb7dATphKZ7iMprhy3YjfGmJD2cfVyOSW71LTFGN2jzSfSelqPrmKmxzGRONTHdv2zNeqvftOMI" \
                      "MKVqXCddxdHPHf+dPOoG2+3epexcOi34rN/FMcKVFF5vODOQGINiKOFvGFBD18WK0fPT7FOoSQ4ttUfHhzjW9S" \
                      "w2vZLBdk131CqH9LmvTnG3Gh6RRKBynIW0IjEVjAKzh3YNwIDAQABAoIBADZ+YfAJn/h71TsZaCWWtpEP7HLZh" \
                      "yRXJIsHatcAOKxEB1gV2NKy5PzFNPbWBVR0YddsqA1DFh2Djep1UBaY4TtLtvo4ktJw5fp7BaU2qyEZQK2man6" \
                      "ttVo2cEhLN8O+22lEckbx7tYWQWRa9d4yeHB2YULseTapCGbyzAM7uhNUBkgtbMZBMbNIkRk2w8MJpJnTYJ7fK" \
                      "AXm1lCCBf32M03VGHZwFQlbqWN4qcbv7/BIRELWgtlRwyGqjDMV7o2wg9KRqx5lgnJnjHDP7qORP1fL6Vc2zad" \
                      "wsg5pY20jABiOr86G2dW9sjDljIhGWHuISaBqD7c8FiIfFFDgukbyRckCgYEAyRl/Ccc2umy8fkdwOTpInQPbE" \
                      "pNWJnmgRPikHoATXnrLCyZwQ7pTUZmhESW3SJLvOHAqKUPA67l6rNp/OnsiIQ9yxIdSt9rl8BOCzcpDU2npxX2" \
                      "qatukvjcM2ntOkpJCUE3MIEHW1DcJa+Htuni+Q3jr4yuXK+Yn0nuLiKAJ4+UCgYEAxRNWKEJEJT4Ns3TGifvG7" \
                      "EoayEBDO5TaXaijXZqDJVZvyqCLuHbwQVAWECf7if2YSXkBssQjbmurjtQ0v9UgDzM/ocgUqNE5dN40bB4JUsV" \
                      "lKHKhT7ku9rOlBtcnNoOTZ7wjfyR0p2q0RLzhkvGLX5JZa794yui5DRvwDl+ywesCgYEApaY63vMaQbYQDnUKH" \
                      "BnGdpAWhNaYwFivjCDED9uwGMNNPYIMN73jo/PImTdYIo/mPbcnA5ar84B1bK0O4D1Nf64Z+4j8ujW18mwf8yQ" \
                      "JEUzNI8DAAAWtToJKNC4eKt4PgdaTrn6NV4F+YT9Zc6DCGRIiPJ5Lh/2uD9N0vLYXb4ECgYEAol4jDvpBwNlWW" \
                      "nMsnESXCNipJjFj8zPZkW6+YgFKabnEUxJg6zL7ESSVeOwoHvGTxXzv/EQC2RfWec+2QhKq3jsgAv+gndH7X6E" \
                      "vWaCJl+tQQ7nl05RD8DfkEDW1dgGDseTc7gSwI7sTGMrxoqplZPFjwRU4xRxmUjmhV4Za9c8CgYBB+LOjcyJkC" \
                      "lZEZQ1haPg1uCldxhB41sovuCvsPTu8SzaDL6f2xlQWXpiVLNwsaO2NDhyFg8aUDPJTOUxnxJwaJMDDgL2hhlh" \
                      "RvfW+7uyxXYa8oKOlhILk4njTRbb8cYWx8x0sYqf7WrN/Q8Oko1zK1KeWkmMKkkeQhcsdUiq1kQ==\n-----EN" \
                      "D RSA PRIVATE KEY-----"

        payload = {
            'key': 'value',
            'iss': AUTH0_ISSUER,
            'aud': API_IDENTIFIER
        }

        self.token = jwt.encode(payload, private_key, algorithm='RS256')
        headers = {'kid': public_key.get('kid')}
        self.token1 = jwt.encode(payload, private_key, algorithm='RS256', headers=headers)

    def tearDown(self):
        self.app_context.pop()

    @patch('server.get_public_key', side_effect=mock_get_public_key)
    def test_private_endpoint(self, mock_public_key):
        mock_public_key.side_effect = mock_get_public_key()

        rv = self.app.get('/api/private', headers={'Authorization': 'Bearer ' + self.token})
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Hello from a private endpoint! You need to be authenticated to see this.', rv.data)

    @patch('server.Cache.get', side_effect=mock_cache_get)
    def test_get_public_key(self, mock_cache):
        mock_cache.side_effect = mock_cache_get()

        pk = get_public_key(self.token1)
        self.assertEqual(pk, public_key)

        pk = get_public_key(self.token)
        self.assertEqual(pk, new_public_key)

        pk = get_public_key(self.token1, False)
        self.assertEqual(pk, public_key)


if __name__ == '__main__':
    unittest.main()
