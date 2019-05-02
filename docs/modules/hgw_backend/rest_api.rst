API Methods
-----------

.. http:post:: /oauth2/token/

    Obtain an OAuth2 authorization token to be used by the Source Endpoint to make request to the
    other API functions. The token will have a `message:write` scope, which is the one that allows
    to send messages, or a `sources:read` scope, which is the one that to read sources.

    :query client_id: the oauth2 client id assigned to a Source Endpoint during the enrollment phase
    :query client_secret: the oauth2 client secret assign during the enrollment phase
    :query grant_type: type of grant used. In our case is always `client_credentials`

    **Success Response**

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "access_token": "fNN8u8THUuG5KVkTRlTtxKe7mgF1aG",
                "token_type": "Bearer",
                "expires_in": 36000,
                "scope": "messages:write"
            }

.. http:get:: /v1/sources/

    Gets the list of sources with their associated profiles

    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 200: The request was successfull
    :statuscode 401: Unauthorized - The client has not provide a valid token or the token has expired
    :statuscode 403: Forbidden - The client token has not the right scope for the operation
    :statuscode 500: Internal Server Error - Something wrong happened

    **Success response**

        .. sourcecode:: http

            HTTP/1.1 202 OK
            Vary: Authorization
            Content-Type: application/json

            [{
                "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN",
                "name": "SOURCE_ENDPOINT",
                "profile": {
                    "code": "PROF_001",
                    "version": "v0",
                    "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                }
            }]

.. http:get:: /v1/sources/{str: source_id}

    Gets the source with id `source_id` and its associated profiles

    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 200: The request was successfull
    :statuscode 401: Unauthorized - The client has not provide a valid token or the token has expired
    :statuscode 403: Forbidden - The client token has not the right scope for the operation
    :statuscode 404: Not Found - The source with the specified id was not found
    :statuscode 500: Internal Server Error - Something wrong happened
    :parameter source_id: the id of the source to get

    **Success response**

        .. sourcecode:: http

            HTTP/1.1 202 OK
            Vary: Authorization
            Content-Type: application/json

            {
                "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN",
                "name": "SOURCE_ENDPOINT",
                "profile": {
                    "code": "PROF_001",
                    "version": "v0",
                    "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                }
            }

.. http:post:: /v1/messages/

    Creates (i.e., sends) a new message. The Source Endpoint must include the `channel_id` the
    message refers to and the `payload` which is an encrypted string. To use this endpoint
    the client needs a token with `messages:write` scope

    :query channel_id: The channel id the message refers to
    :query message: The encrypted message
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :reqheader Content-Type: multipart/form-data
    :resheader Content-Type: application/json
    :statuscode 200: Success - Message sent correctly
    :statuscode 400: Bad Request - Missing parameters or payload not encrypted
    :statuscode 401: Unauthorized - The client has not provide a valid token or the token has expired
    :statuscode 403: Forbidden - The client token has not the right scope for the operation
    :statuscode 500: Internal Server Error - Something wrong happened sending the message
        (e.g., broker was unreachable)
