API Methods
-----------

.. http:post:: /oauth2/token/

    Obtain an OAuth2 authorization token to be used to make request to the other API functions

    :query client_id: the oauth2 client id assigned during the enrollment phase
    :query client_secret: the oauth2 client secret assign during the enrollment phase
    :query grant_type: type of grant used. In our case is alway client_credentials

    **Success Response**

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "access_token": "fNN8u8THUuG5KVkTRlTtxKe7mgF1aG",
                "token_type": "Bearer",
                "expires_in": 36000,
                "scope": "flow_request:read flow_request:write"
            }

.. http:get:: /v1/flow_requests/(str: process_id)

   Get the list of flow requests

   :reqheader Authorization: Bearer <oauth_2_access_token>

.. http:post:: /v1/flow_requests/

    Create a new flow request. It will be created but set in a pending status until the user confirms it.
    The call returns a json with two attributes:

    * ``process_id``: the id that identifies the flow request in the health gateway. The client must maintain the mapping between the ``process_id`` and the ``flow_id`` to be used in subsequent process
    * ``confirm_id``: the id to send to the confirmation url to activate the flow request

    :query flow_id: the flow id that identifies the request for the client. The Health Gateway creates a corresponding
        processing id
    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 201: flow request created succesfully
    :statuscode 400: no `flow_id` provided
    :statuscode 500: server error, error's detail are specified in the return response

    **Success response**

    .. sourcecode:: http

        HTTP/1.1 201 OK
        Vary: Authorization
        Content-Type: application/json

        {
            "process_id": "2Eko7Zw39wPWVNaBbwClzbFpjJ97nHHb",
            "confirm_id": "xdv5jlQiWNW3ZaFMvmyVev5A0AGOZEHC"
        }


.. http:delete:: /v1/flow_requests/{str: process_id}/

    Delete the flow request identified by (process_id). It will be set in a delete requested status until the user confirms it.
    The call returns a json with the ``confirm_id`` to send to the confirmation url to delete the flow request

    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 202: the requested to delete has been accepted
    :statuscode 500: server error, error's detail are specified in the return response

    **Success response**

    .. sourcecode:: http

        HTTP/1.1 202 OK
        Vary: Authorization
        Content-Type: application/json

        {
            "confirm_id": "xdv5jlQiWNW3ZaFMvmyVev5A0AGOZEHC"
        }

.. http:get:: /v1/flow_requests/confirm/

    This is the link where the user has to be redirected to confirm the creation or deletion of a flow_request

    :query confirm_id: the confirm id obtained with POST or DELETE /v1/flow_requests calls
    :query callback_url: the url where the user will be redirected after the confirmation
    :query action: add or delete

.. http:get:: /v1/messages/{int: message_id}/

    Gets messages for a specific Destination

    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 200: The request was successfull
    :statuscode 404: Not Found - The message with id `message_id` does not exist
        or if the start query parameter is minor than the first message_id available
    :parameter message_id: the id of the message to get

    **Success response**

    .. sourcecode:: http

        HTTP/1.1 202 OK
        Vary: Authorization
        Content-Type: application/json

        {
            "process_id": "£2Eko7Zw39wPWVNaBbwClzbFpjJ97nHHb",
            "message_id": 1,
            "data": "<lot_of_data>"
        }

.. http:get:: /v1/messages/

    Gets a list of messages for a specific Destination. If `start` query parameter is specified the list starts
    from the message with `start` as id. If the `limit` parameter is specified the list will have that amount of
    items.

    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :resheader X-Skipped: number of record skipped
    :resheader X-Total-Count: number of records present
    :statuscode 200: The request was successfull
    :statuscode 404: Not Found - The start query parameter is minor than the first `message_id` available
    :query start: optional - The message_id of the initial message
    :query limit: optional - The maximum number of messages to return (DEFAULT: 5, MAX: 10)

    **Success response**

    .. sourcecode:: http

        HTTP/1.1 202 OK
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

.. http:get:: /v1/messages/info

    Gets information about the messages available.
    The information returned are the number of records, the first and the last message_id available.

    :reqheader Authorization: Bearer <oauth_2_access_token>
    :resheader Content-Type: application/json
    :statuscode 200: The request was successfull

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
