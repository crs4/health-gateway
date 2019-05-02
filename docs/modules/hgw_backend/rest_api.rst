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

    **Request Example**

    .. sourcecode:: http

            HTTP/1.1
            Content-Type: multipart/form-data

            'channel_id': 'channel_id',
            'payload': '\xdf\xbb \x02\x10\xbd\x91\xc0g\xb9\xba\xdd2\x1f\x8c\x9b\xb9H\xd6\xbc\x9c3\x02\x13\xcaN\x08\xa7:5\xe3\xbd@\xf9\xf1\xc5\x97\x90\xb4G\xb57\x8fb\xff\x05D\xcc\x9e\n\x8e\xa3\xa8\xbf\xd8\xcb\xc6\xbb\xb2\xcb\xe1;\xc1\x15\xef\xf15/\x08q1#\xbf\xb62\xdf\xacD){\xb5\x83@\xef\xc5i\xf1~fLs\x80\xcb(\x95\x88\x01C\x1d\xeaIA\xd2~\xce\x92\x18\xd6\xa6\xf9E\xd2\x7f\x9d5M"\xa4\x00,~T!{l3\'\x0c*\xd3\xb3\xeb\xec2\x8a\xf2\xc2j\xb7\xa0\xa0\xe1,\x17\x1aN\xbb\x88l\xd2\xe6K\xbb7\xb6o\xec\xd4\x0bM\xd7\xcf9\xa4\x9c\xadgx\n\'m\xad\xa3=\x11\x1e\x8b\x13\x80\xf7\x87e\x03\xeb\xc0,\xebW\x0e\xa0\xbf\xd4#:Y-F\xf5}o\xff\xd4\xa7\x91"M*\x8f\xe4\xa7>\x06y\x9ak,\x07N\xe0\xa0*6\xcby\xbd\xfb\xd59\xe3g\xd2\x08\xc1\xc1\xb1\xf8=\x1a\x02\xe9]Y\xb1\x12\x03\xd1y\xee\x93f;\xc9\xe3\x1e\x97\x93&`\n8\x0c\\ \xb3\xaa)\x07\x8e\xc0\x0f\x8fJ\x93H\xb2ZEL\x9d\x1c\xebEG\xd2\xce\xf0!\x18\xb8\x93\xad\x8dy\x19\xd7\xd9\x81\xb2\xf2Z\x15\x0b\xa5\x87\xa0\xc9#\x8f6\xdeBz\xafk6\x00\xb5\xbfd\x81\xe2\xc1>q\x83'
