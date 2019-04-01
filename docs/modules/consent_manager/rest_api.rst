API Methods
-----------

.. http:post:: /oauth2/token/

    Obtain an OAuth2 authorization token to be used to make request to the other API functions

    :param client_id: the oauth2 client id assigned during the enrollment phase
    :param client_secret: the oauth2 client secret assign during the enrollment phase
    :param grant_type: type of grant used. In our case is alway client_credentials

    **Success Response**

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "access_token": "fNN8u8THUuG5KVkTRlTtxKe7mgF1aG",
                "token_type": "Bearer",
                "expires_in": 36000,
                "scope": "consent:read consent:write"
            }

.. http:post:: /v1/consents/

    Creates a new Consent/Channel which is set in a PENDING status until the user confirms it

    :param source_id: the id of the Source that will send data
    :param destination_id: the id of the Destination that will receive the data
    :param profile: the Profile object
    :param person_id: the person id

    :reqheader Authorization: Bearer <oauth2_authorization_token> The authorization token obtained before
    :resheader Content-Type: application/json

    :statuscode 201: The Consent/Channel has been created correctly
    :statuscode 400: Something wrong with the parameters
    :statuscode 500: Something wrong happened

    **Success Response**

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Type: application/json

            {
                "consent_id": "2Eko7Zw39wPWVNaBbwClzbFpjJ97nHHb",
                "confirm_id": "xdv5jlQiWNW3ZaFMvmyVev5A0AGOZEHC"
            }

.. http:get:: /v1/consents/

    Get a list of information about the Consents/Channels. In particular it returns the destination id and the status.

    :reqheader Authorization: Bearer <oauth2_authorization_token> The authorization token obtained before
    :resheader Content-Type: application/json

    :statuscode 200: Everything ok
    :statuscode 500: Something wrong happened

    **Success Response**

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            [{
                "status":"PE",
                "destination_id":"vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj"
            }]

.. http:get:: /v1/consents/(str: consent_id)/

    Get information about the Consent/Channel with id consent_id. In particular it returns the destination id and the status.

    :reqehader Authorization: Bearer <oauth2_authorization_token> The authorization token obtained before
    :resheader Content-Type: application/json

    :statuscode 200: Everything ok
    :statuscode 500: Something wrong happened

    **Success Response**

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status":"AC",
                "destination_id":"vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj"
            }

.. http::get:: /v1/consents/confirm

    This is not a REST function but it is the URL where the browser has to be redirect to confirm a Consent/Channel.
    It redirects to the Identity Service for  authentication before continuing.

    :query confirm_id: the consent confirmation id returned after the Consent creation
    :query callback_url: the URL where the browser is redirected after the Consent is activated
