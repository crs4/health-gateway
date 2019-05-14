API Methods
-----------

.. http:post:: /oauth2/token/

    Obtain an OAuth2 authorization token to be used to make request to the other API functions.
    The client will obtain a scope based on its registration in the HGW. This means that
    a client can specify in the request just a subset of the scopes it is registered for.
    The available scopes and the description of the operation that can be performed
    are the following:

    ``flow_request:read``: Read flow request belonging to the corrispondent destination
    ``flow_request:write``: Write scope. You can add, update or delete a flow_request
    ``flow_request:query``: Perform flow request query
    ``messages:read``: Can read messages
    ``sources:read``: Can get information about sources

    In case of error the response will be a json object with the key `error` and a description
    of the error. Possible errors' values are:

    * ``invalid_client``
    * ``unsupported_grant_type``

    :reqheader Content-Type: application/x-www-form-urlencoded
    :resheader Content-Type: application/json
    :formparam client_id: the oauth2 client id assigned during the enrollment phase
    :formparam client_secret: the oauth2 client secret assign during the enrollment phase
    :formparam grant_type: type of grant used. In our case is always client_credentials
    :formparam scope: Optional. A subset of possible scope for the client
    :statuscode 200: OK - The token has been created successfully
    :statuscode 400: Bad Request - ``grant_type`` missing or wrong (i.e., different from `client_credentials`)
    :statuscode 401: Unauthorized - one of client_id, client_secret missing or wrong
    :resjson string access_token: the value of the token
    :resjson string token_type: the type of the token. It is always `Bearer`
    :resjson int expires_in: number of seconds after which the token expires
    :resjson string scope: a string with whitespace-separated scopes assigned to the token.

    **Request example**

    .. sourcecode:: http

        POST /oauth2/token HTTP/1.1
        Content-Type: application/x-www-form-urlencoded
        Accept: application/json

        client_id: client_id
        client_secret: supersecretstring
        grant_type: client_credentials
        scope: flow_request:read

    **Success Response Example**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "access_token": "fNN8u8THUuG5KVkTRlTtxKe7mgF1aG",
            "token_type": "Bearer",
            "expires_in": 36000,
            "scope": "flow_request:read flow_request:write messages:read sources:rea"
        }

    **Error Response Example**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "error": "invalid_client"
        }

.. http:post:: /v1/flow_requests/

    Create a new flow request. It will be created and set in a PENDING status
    until the user confirms it. The client will receive a json object with a ``process_id`` and a ``confirm_id``.

    **N.B. The client needs an OAut2 token with the flow_request:write scope to perform this action**

    :reqjson string flow_id: the flow id that identifies the request for the client. The Health Gateway creates a corresponding
        id called ``process_id``
    :reqjson list sources: **(optional)** - a list of sources which is a subset of the available ones.
        If specified, the HGW will create channels only for these sources. Every item is an object with the
        field :source_id: specified
    :reqjson object profile: **(optional)** - the profile of the flow_request, indicating the medical specialty required
    :reqjson datetime start_validity: **(optional)** the start datetime of validity of the flow request. It is the lower datetime
        of the clinical documents of the person that the destination wants to be sent. It can be changed by the person during the
        consent authorization
    :reqjson datetime end_validity: **(optional)** the end datetime of validity of the flow request. It is the upper datetime
        of the clinical documents that the destination wants to be sent. It can be changed by the person during the
        consent authorization
    :resjson string process_id: the id that identifies the flow request in the health gateway.
        The client must maintain the mapping between the ``process_id`` and the ``flow_id`` to
        be used in subsequent process
    :resjson string confirm_id: the id to send to the confirmation url to activate the flow request
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 201: OK - flow request created succesfully
    :statuscode 400: Bad Request - ``flow_id`` not provided
    :statuscode 500: Internal Server Error - server error, error's detail are specified in the return response

    **Request Examples**

    .. sourcecode:: http

        POST /v1/flow_requests/ HTTP/1.1
        Content-Type: application/json
        Accept: application/json

        {
            "flow_id": "dq39rXdscfNiZuhVSAnHG3H65pnI44a6",
            "profile": {
                "code": "PROF_001",
                "version": "v1.0.0",
                "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
            },
            "start_validity": "2017-10-23T10:00:00",
            "expire_validity": "2017-10-23T18:00:00"
        }

    .. sourcecode:: http

        POST /v1/flow_requests/ HTTP/1.1
        Content-Type: application/json
        Accept: application/json

        {
            "flow_id": "dq39rXdscfNiZuhVSAnHG3H65pnI44a6",
            "sources": [{
                "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN"
            }]
            "start_validity": "2017-10-23T10:00:00",
            "expire_validity": "2017-10-23T18:00:00"
        }

    **Success response**

    .. sourcecode:: http

        HTTP/1.1 201 OK
        Vary: Authorization
        Content-Type: application/json

        {
            "process_id": "2Eko7Zw39wPWVNaBbwClzbFpjJ97nHHb",
            "confirm_id": "xdv5jlQiWNW3ZaFMvmyVev5A0AGOZEHC"
        }

    .. sourcecode:: http

        HTTP/1.1 401 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_authenticated"
        }]

.. http:get:: /v1/flow_requests/(str: process_id)

    Get the flow request with the process id specified. If everything is ok, the flow request is
    returned. If, otherwise, one or more errors occur, it is returned an array with the specified
    errors. Possible errors' values are:

    * ``not_authenticated`` in case of 401 and 403
    * ``not_found`` in case of 404

    **N.B. The client needs an OAut2 token with the flow_request:read scope to perform this action**

    :param process_id: the process id of the flow request. It is the one returned in creation phase
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :reqheader Content-Type: application/json
    :resheader Content-Type: application/json
    :statuscode 200: OK - the flow request was found and returned
    :statuscode 401: Unauthorized - the oauth2 token is invalid or expired
    :statuscode 403: Forbidden - the oauth2 token is missing
    :statuscode 404: Not Found - the flow request has not been found
    :resjson string flow_id: the id of the flow request generated by the destination when creating the flow request
    :resjson string process_id: the id of the flow request generated by the Health Gateway when creating the flow request
    :resjson string status: the status of the flow request. It can assume the values
        * PE: PENDING. The request has not been confirmed by the person yet
        * AC: ACTIVE. The request has been confirmed by the person
    :resjson obj profile: a json object representing the profile of the flow request
    :resjson list sources: the list of sources included in the flow request. If specified a subset in input,
        it will correspond to it, otherwise it contains all the sources available in the Health Gateway.
    :resjson string start_validity: the datetime of the start of the validity of the request. The format is the ISO-8601
    :resjson string expire_validity: the datetime of the end of the validity of the request

    **Request Example**

    .. sourcecode:: http

        GET /v1/flow_requests/12345/ HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    **Success Response Example**

    .. sourcecode:: http

        HTTP/1.1 201 OK
        Vary: Authorization
        Content-Type: application/json

        {
            "flow_id": "12345",
            "process_id": "54321",
            "status": "PE",
            "profile": {
                "code": "PROF_001",
                "version": "v1.0.0",
                "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
            },
            "sources": [{
                "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN",
                "name": "SOURCE_ENDPOINT",
                "profile": {
                    "code": "PROF_001",
                    "version": "v1.0.0",
                    "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                },
            }],
            "start_validity": "2017-10-23T10:00:00+02:00",
            "expire_validity": "2018-10-23T10:00:00+02:00"
        }

    **Error Response Example**

    .. sourcecode:: http

        HTTP/1.1 401 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_authenticated"
        }]

    .. sourcecode:: http

        HTTP/1.1 404 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_found"
        }]


.. http:get:: /v1/flow_requests/(str: process_id)/channels/

    Get the channels associated to a specific Flow Request, identified by the `process_id`.
    It is possible to filter by status of the channels using the query parameter `status`. If something
    wrong happens. it returns a json with specified an error status. Possible error values are:

    * ``not_authenticated`` in case of 401 and 403
    * ``not_found`` in case of 404

    **N.B. The client needs an OAut2 token with the flow_request:read scope to perform this action**

    :param process_id: the process id of the flow request. It is the one returned in creation phase
    :query status: filter channels by status. The status must be AC (ACTIVE) or CR (CONSENT_REQUESTED)
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :reqheader Content-Type: application/json
    :resheader Content-Type: application/json
    :statuscode 200: OK - the flow request was found and returned
    :statuscode 400: Bad Request - the status query parameter has an invalid value
    :statuscode 401: Unauthorized - the oauth2 token is invalid or expired
    :statuscode 403: Forbidden - the oauth2 token is missing
    :statuscode 404: Not Found - the flow request has not been found
    :resjson string channel_id: the id of the flow request generated by the destination when creating the flow request
    :resjson string destination_id: the id of the flow request generated by the Health Gateway when creating the flow request
    :resjson string status: the status of the flow request. It can assume the values
        * CR: CONSENT_REQUESTED. The consent for the channels has been requested but not confirmed yet by the user
        * AC: ACTIVE. The channel is active
    :resjson obj source: a json object representing the source endpoint of the channel
    :resjson obj profile: a json object representing the profile of the channel

    **Request Examples**

    .. sourcecode:: http

        GET /v1/flow_requests/12345/channels/ HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    .. sourcecode:: http

        GET /v1/flow_requests/12345/channels/?status=AC HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    **Success Response Example**

    .. sourcecode:: http

        HTTP/1.1 201 OK
        Vary: Authorization
        Content-Type: application/json

        [
            {
                "channel_id": "zcRVwZjoYJsRivaFq4xOdpEi4r8Hy7Gw",
                "status": "AC",
                "destination_id": "zb2WTuyHyK7I1QGngt1Y7I4YnVMBRZ8Y",
                "source": {
                    "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN",
                    "name": "SOURCE_ENDPOINT",
                    "profile": {
                        "code": "PROF_001",
                        "version": "v1.0.0",
                        "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                    }
                },
                "profile": {
                    "code": "PROF_001",
                    "version": "v1.0.0",
                    "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                }
            },
            {
                "channel_id": "JyUUH5Av20HI18ty81aTKHoaH26nQYuk",
                "status": "CR",
                "destination_id": "zb2WTuyHyK7I1QGngt1Y7I4YnVMBRZ8Y",
                "source": {
                    "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN",
                    "name": "SOURCE_ENDPOINT",
                    "profile": {
                        "code": "PROF_001",
                        "version": "v1.0.0",
                        "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                    }
                },
                "profile": {
                    "code": "PROF_001",
                    "version": "v1.0.0",
                    "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                }
            }
        ]

    **Error Response Example**

    .. sourcecode:: http

        HTTP/1.1 400 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "invalid_query_params"
        }]

    .. sourcecode:: http

        HTTP/1.1 401 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_authenticated"
        }]

    .. sourcecode:: http

        HTTP/1.1 404 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_found"
        }]

.. http:get:: /v1/flow_requests/confirm/

    This is the link where the user has to be redirected to confirm the creation or deletion of a flow_request

    :query confirm_id: the confirm id obtained with POST or DELETE /v1/flow_requests calls
    :query callback_url: the url where the user will be redirected after the confirmation
    :query action: add or delete

.. http:get:: /v1/channels/

    Get the all the channels for a destination. The destination is implicit in the OAuth2 token.
    It is possible to filter by status of the channels using the query parameter `status`. If something
    wrong happens. it returns a json with specified an error status. Possible error values are:

    * ``not_authenticated`` in case of 401 and 403
    * ``not_found`` in case of 404

    **N.B. The client needs an OAut2 token with the flow_request:read scope to perform this action**

    :param process_id: the process id of the flow request. It is the one returned in creation phase
    :query status: filter channels by status. The status must be AC (ACTIVE) or CR (CONSENT_REQUESTED)
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :reqheader Content-Type: application/json
    :resheader Content-Type: application/json
    :statuscode 200: OK - the flow request was found and returned
    :statuscode 400: Bad Request - the status query parameter has an invalid value
    :statuscode 401: Unauthorized - the oauth2 token is invalid or expired
    :statuscode 403: Forbidden - the oauth2 token is missing
    :statuscode 404: Not Found - the flow request has not been found
    :resjson string channel_id: the id of the flow request generated by the destination when creating the flow request
    :resjson string destination_id: the id of the flow request generated by the Health Gateway when creating the flow request
    :resjson string status: the status of the flow request. It can assume the values
        * CR: CONSENT_REQUESTED. The consent for the channels has been requested but not confirmed yet by the user
        * AC: ACTIVE. The channel is active
    :resjson obj source: a json object representing the source endpoint of the channel
    :resjson obj profile: a json object representing the profile of the channel

    **Request Example**

    .. sourcecode:: http

        GET /v1/flow_requests/12345/channels/ HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    **Success Response Example**

    .. sourcecode:: http

        HTTP/1.1 201 OK
        Vary: Authorization
        Content-Type: application/json

        [
            {
                "channel_id": "zcRVwZjoYJsRivaFq4xOdpEi4r8Hy7Gw",
                "status": "AC",
                "destination_id": "zb2WTuyHyK7I1QGngt1Y7I4YnVMBRZ8Y",
                "source": {
                    "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN",
                    "name": "SOURCE_ENDPOINT",
                    "profile": {
                        "code": "PROF_001",
                        "version": "v1.0.0",
                        "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                    }
                },
                "profile": {
                    "code": "PROF_001",
                    "version": "v1.0.0",
                    "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                }
            },
            {
                "channel_id": "JyUUH5Av20HI18ty81aTKHoaH26nQYuk",
                "status": "CR",
                "destination_id": "zb2WTuyHyK7I1QGngt1Y7I4YnVMBRZ8Y",
                "source": {
                    "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN",
                    "name": "SOURCE_ENDPOINT",
                    "profile": {
                        "code": "PROF_001",
                        "version": "v1.0.0",
                        "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                    }
                },
                "profile": {
                    "code": "PROF_001",
                    "version": "v1.0.0",
                    "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                }
            }
        ]

    **Error Response Example**

    .. sourcecode:: http

        HTTP/1.1 400 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "invalid_query_params"
        }]

    .. sourcecode:: http

        HTTP/1.1 401 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_authenticated"
        }]

    .. sourcecode:: http

        HTTP/1.1 404 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_found"
        }]

.. http:get:: /v1/messages/(int: message_id})

    Gets messages for a specific Destination. If everything is correct it return the message, if
    something wrong happens it returns a json response with the list of possible errors. They can be:

    * ``not_authenticated``
    * ``not_found``

    **N.B. The client needs an OAut2 token with the messages:read scope to perform this action**

    :parameter message_id: the id of the message to get
    :resjson string process_id: the process_id of the Flow Request that the message belongs to.
    :resjson int message_id: the message_id: it is the same as the one in the request url
    :resjson string message_id: a base64 encoded string representing the encrypted message arrived from the source
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :reqheader Accept: application/json
    :resheader Content-Type: application/json
    :statuscode 200: OK - The request was successfull and the message is returned
    :statuscode 401: Unauthorized - the OAuth2 token was invalid or expired
    :statuscode 403: Forbidden - the OAuth2 token was missing
    :statuscode 404: Not Found - The message with id `message_id` does not exist

    **Request Example**

    .. sourcecode:: http

        GET /v1/messages/1/ HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    **Success Response Example**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Authorization
        Content-Type: application/json

        {
            "process_id": "£2Eko7Zw39wPWVNaBbwClzbFpjJ97nHHb",
            "message_id": 1,
            "data": "<lot_of_data>"
        }

    **Error Response Example**

    .. sourcecode:: http

        HTTP/1.1 401 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_authenticated"
        }]

    .. sourcecode:: http

        HTTP/1.1 404 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_found"
        }]

.. http:get:: /v1/messages/

    Gets a list of messages for a specific Destination. If `start` query parameter is specified the list starts
    from the message with `start` as id. If the `limit` parameter is specified the list will have that amount of
    items. If something wrong happens it returns a json response with the list of possible errors. They can be:

    * ``not_authenticated``
    * ``not_found``

    **N.B. The client needs an OAut2 token with the messages:read scope to perform this action**

    :query start: optional - The `message_id` of the first message
    :query limit: optional - The maximum number of messages to return (DEFAULT: 5, MAX: 10)
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :resheader X-Skipped: number of record skipped
    :resheader X-Total-Count: number of records present
    :statuscode 200: The request was successfull
    :statuscode 401: Unauthorized - the OAuth2 token was invalid or expired
    :statuscode 403: Forbidden - the OAuth2 token was missing

    **Request Examples**

    .. sourcecode:: http

        GET /v1/messages/?start=10&limit=10 HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    .. sourcecode:: http

        GET /v1/messages/ HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    **Success Response Example**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "process_id": "£2Eko7Zw39wPWVNaBbwClzbFpjJ97nHHb",
            "message_id": 1,
            "data": "<lot_of_data>"
        },
        {
            "process_id": "gkd34uaSPgjs20xznsbpdmvqDPQ5105GG",
            "message_id": 2,
            "data": "<lot_of_data>"
        }]

    **Error Response Example**

    .. sourcecode:: http

        HTTP/1.1 401 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_authenticated"
        }]

.. http:get:: /v1/messages/info

    Gets information about the messages available.
    The information returned are the number of records, the first and the last message_id available.
    If something wrong happens it returns a json response with the list of possible errors. They can be:

    * ``not_authenticated``
    * ``not_found``

    **N.B. The client needs an OAut2 token with the messages:read scope to perform this action**

    :resjson int start_id: the id of the first message available
    :resjson int last_id: the id of the last message available
    :resjson int count: the number of messages available
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 200: OK - The request was successfull
    :statuscode 401: Unauthorized - the OAuth2 token was invalid or expired
    :statuscode 403: Forbidden - the OAuth2 token was missing

    **Request Examples**

    .. sourcecode:: http

        GET /v1/messages/info HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    **Success response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Authorization
        Content-Type: application/json

        {
            "start_id": 5,
            "last_id": 30,
            "count": 26
        }

    **Error Response Example**

    .. sourcecode:: http

        HTTP/1.1 401 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_authenticated"
        }]

    .. sourcecode:: http

        HTTP/1.1 404 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_found"
        }]

.. http:get:: /v1/sources/

    Gets the list of sources with their associated profiles.
    If something wrong happens it returns a json response with the list of possible errors. They can be:

    * ``not_authenticated``
    * ``not_found``

    :resjson string source_id: The id of the Source
    :resjson string name: The name of the Source
    :resjson object profile: The profile that the Source supports
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 200: OK - The request was successfull
    :statuscode 401: Unauthorized - the OAuth2 token was invalid or expired
    :statuscode 403: Forbidden - the OAuth2 token was missing

    **Request Example**

    .. sourcecode:: http

        GET /v1/sources HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    **Success response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN",
            "name": "SOURCE_ENDPOINT",
            "profile": {
                "code": "PROF_001",
                "version": "v1.0.0",
                "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
            }
        }]

    **Error Response Example**

    .. sourcecode:: http

        HTTP/1.1 401 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_authenticated"
        }]

    .. sourcecode:: http

        HTTP/1.1 404 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_found"
        }]

.. http:get:: /v1/sources/(str: source_id)

    Gets the source with id `source_id` and its associated profiles.
    If something wrong happens it returns a json response with the listi of possible errors. They can be:

    * ``not_authenticated``
    * ``not_found``

    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 200: The request was successfull
    :statuscode 401: Unauthorized - The client has not provide a valid token or the token has expired
    :statuscode 403: Forbidden - The client token has not the right scope for the operation
    :statuscode 404: Not Found - The source with the specified id was not found
    :statuscode 500: Internal Server Error - Something wrong happened
    :parameter source_id: the id of the source to get

    **Request Example**

    .. sourcecode:: http

        GET /v1/sources/WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN HTTP/1.1
        Authorization: Bearer rhETLn6FyPWfnZ2chxgRfqqSx5YKIA
        Accept: application/json

    **Success Response Example**

        .. sourcecode:: http

            HTTP/1.1 202 OK
            Vary: Authorization
            Content-Type: application/json

            {
                "source_id": "WeiMaK8pjMQ6B9qxDRFm00EcFyi1NyFN",
                "name": "SOURCE_ENDPOINT",
                "profile": {
                    "code": "PROF_001",
                    "version": "v1.0.0",
                    "payload": "[{\"clinical_domain\": \"Laboratory\"}]"
                }
            }

    **Error Response Example**

    .. sourcecode:: http

        HTTP/1.1 401 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_authenticated"
        }]

    .. sourcecode:: http

        HTTP/1.1 404 OK
        Vary: Authorization
        Content-Type: application/json

        [{
            "errors": "not_found"
        }]
