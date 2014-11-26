daybed-fxa
##########

.. image:: https://travis-ci.org/spiral-project/daybed-fxa.png
    :target: https://travis-ci.org/spiral-project/daybed-fxa

This is an utility that allows you to connect to daybed using your FxA
credentials, using OAuth.

All the APIs are prefixed by `/tokens/<prefix>/` by default. You can configure
this.

Here is a list of endpoints which allow integration with Firefox Accounts. For more
information on how to integrate with Firefox Accounts, `have a look at the
Firefox Accounts documentation on MDN
<https://developer.mozilla.org/en-US/Firefox_Accounts#Login_with_the_FxA_OAuth_HTTP_API>`_

POST /<prefix>/params
~~~~~~~~~~~~~~~~~~~~~~

    Provide the client with the parameters needed for the OAuth dance.

    - **client_id**, the client id used by the server;
    - **content_uri**, URI of the content server (to get account information);
    - **oauth_uri**, URI of the OAuth server;
    - **redirect_uri**, URI where the client should redirect once authenticated;
    - **scope**, The scope of the token returned;
    - **state**, A nonce used to check that the session matches.

    ::

        http POST http://localhost:8000/v1/<prefix>/params redirect_uri=http://webapp-callback-uri/ -v

    .. code-block:: http

        POST /v1/<prefix>/params HTTP/1.1
        Accept: application/json
        Accept-Encoding: gzip, deflate
        Content-Type: application/json; charset=utf-8
        Host: localhost:5000
        User-Agent: HTTPie/0.8.0

        HTTP/1.1 200 OK
        Connection: keep-alive
        Timestamp: 1409052727
        + Session cookie

        {
            "client_id": "263ceaa5546dce83",
            "content_uri": "https://accounts.firefox.com",
            "oauth_uri": "https://oauth.accounts.firefox.com/v1",
            "redirect_uri": "urn:ietf:wg:oauth:2.0:fx:webchannel",
            "scope": "profile",
            "state": "b56b3753c15efdcae80ea208134ecd6ae97f27027ce9bb11f7c333be6ea7029c"
        }


POST /<prefix>/token
~~~~~~~~~~~~~~~~~~~~~

    **Requires session cookie**

    Trades an OAuth code with an OAuth bearer token::

        http POST http://localhost:5000/v1/<prefix>/token --verbose --json \
        state=b56b3753c15efdcae80ea208134ecd6ae97f27027ce9bb11f7c333be6ea7029c \
        code=12345

    Checks the validity of the given code and state and exchange it with a
    bearer token with the OAuth server.

    The token is returned in the **access_token** attribute. A few additional
    parameters are returned:

    - **scope** the scope of the token;
    - **token_type** the type of the token returned (here, it will be
      "bearer").

    ::

        {
          token_type: tokenType,
          access_token: token,
          scope: scope
        }


GET /<prefix>/redirect
~~~~~~~~~~~~~~~~~~~~

    Redirects the user to the app URL with the state and code.

        http GET http://localhost:8000/v1/<prefix>/redirect?state=<state>&code=<code>
