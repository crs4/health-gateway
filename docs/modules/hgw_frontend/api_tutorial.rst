Adding a Flow request
*********************

The workflow to add or delete a new flow request is described in the following image

.. image:: _static/flow_requests_workflow.svg

Obtaining a token
-----------------

Before creating a flow request a client needs to authenticate to the Health Gateway. Authentication is performed using
two-legged [OAuth2](https://oauth.net/2/)  protocol with the `client_credentials` grant type.
Before trying to authenticate and to use
the API, the client has to be registered in the Health Gateway in order to obtain a pair of ``client_id/client_secret``

After being registered, to obtain an access token, the client has to make `POST` request to the url `/oauth2/token/`
passing as data `client_id`, `client_secret` and `grant_type` with value `client_credentials`.
This request will return a Bearer access token to be used in the subsequent REST calls

Using the token to create a flow request
----------------------------------------

After gaining the token, the client can use it to create a flow request by calling, using POST, /v1/flow_requests/.
This function creates a flow request and returns three arguments:

  * `process_id`: which is the flow request id assigned by the health gateway
  * `confirm_id`: which is an id to be used to confirm the flow request

Obtaining user authorization
----------------------------

The previous call created a flow request which is not actived immediately, since it needs user authorization.
To do that the client has to redirect the user to `/v1/flow_requests/confirm/` specifying the ``confirm_id``,
``action=add`` and a ``callback_url``. This page asks the user to login and to confirm. After that the flow
request will be activated and the user will be redirected to the ``callback_url`` specified.

Deleting a flow request
-----------------------

The flow request deletion uses the same workflow as the creation. The difference is that it has to be called
`/v1/flow_requests/<process_id>/` using DELETE HTTP method

