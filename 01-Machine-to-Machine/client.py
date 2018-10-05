from auth0.v3.authentication import GetToken
from auth0.v3.management.rest import RestClient
from os import environ as env


class ExampleRestClient(RestClient):
    base_url = 'http://127.0.0.1:3010'

    @staticmethod
    def instance(domain, client_id, client_secret, audience):
        # get jwt token from auth0
        token = GetToken(domain).client_credentials(client_id, client_secret, audience)

        # return a new rest client instance with the jwt token we received from auth0
        return ExampleRestClient(token['access_token'])

    def example_get(self):
        """
        call our server /example endpoint with the jwt token auth header
        """
        response = self.get(self.base_url + '/example')
        print(response)


client = ExampleRestClient.instance(
    env.get('AUTH0_DOMAIN'),
    env.get('AUTH0_CLIENT_ID'),
    env.get('AUTH0_CLIENT_SECRET'),
    env.get('AUTH0_AUDIENCE'),
)

client.example_get()
