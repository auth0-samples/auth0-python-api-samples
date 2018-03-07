# Auth0 + Python + Flask API Seed

This is the seed project you need to use if you're going to create a Python + Flask API.
If you just want to create a Regular Python WebApp, please
check [this project](https://github.com/auth0-samples/auth0-python-web-app/tree/master/01-Login)

Please check our [Quickstart](https://auth0.com/docs/quickstart/backend/python) to better understand this sample.

# Running the example

In order to run the example you need to have `python` and `pip` installed.

You also need to set your Auth0 Domain and the API's audience as environment variables with the following names
respectively: `AUTH0_DOMAIN` and `API_IDENTIFIER`, which is the audience of your API. You can find an example in the
`env.example` file.

For that, if you just create a file named `.env` in the directory and set the values like the following,
the app will just work:

```bash
# .env file
AUTH0_DOMAIN=example.auth0.com
API_IDENTIFIER={API_IDENTIFIER}
```

Once you've set those 2 environment variables:

1. Install the needed dependencies with `pip install -r requirements.txt`
2. Start the server with `python server.py`
3. Try calling [http://localhost:3010/api/public](http://localhost:3010/api/public)

# Testing the API

You can then try to do a GET to [http://localhost:3010/api/private](http://localhost:3010/api/private) which will
throw an error if you don't send an access token signed with RS256 with the appropriate issuer and audience in the
Authorization header. 

You can also try to do a GET to 
[http://localhost:3010/api/private-scoped](http://localhost:3010/api/private-scoped) which will throw an error if
you don't send an access token with the scope `read:messages` signed with RS256 with the appropriate issuer and audience
in the Authorization header.

# Running the example with Docker

In order to run the sample with [Docker](https://www.docker.com/) you need to add the `AUTH0_DOMAIN` and `API_ID`
to the `.env` filed as explained [previously](#running-the-example) and then

1. Execute in command line `sh exec.sh` to run the Docker in Linux, or `.\exec.ps1` to run the Docker in Windows.
2. Try calling [http://localhost:3010/api/public](http://localhost:3010/api/public)