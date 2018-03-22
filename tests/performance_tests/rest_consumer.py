import requests
import time
import logging

logger = logging.getLogger('rest_consumer')
logger.setLevel(logging.INFO)


class Message(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value


class Consumer(object):
    def __init__(self, client_id, client_secret, server_uri):
        self.oauth_params = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        self.server_uri = server_uri
        self.access_token = None
        self.start_id = None

    def __iter__(self):
        return self

    def set_start_id(self, start_id):
        self.start_id = start_id

    def __next__(self):
        if self.access_token is None:
            res = requests.post('{}/oauth2/token/'.format(self.server_uri), data=self.oauth_params)
            self.access_token = res.json()['access_token']

        header = {"Authorization": "Bearer {}".format(self.access_token)}
        while self.start_id is None:
            try:
                info = requests.get('{}/v1/messages/info/'.format(self.server_uri), headers=header)
                self.start_id = info.json()['start_id']
            except Exception as ex:
                logger.exception(ex)

        current_id = self.start_id
        while True:
            try:
                msg = requests.get('{}/v1/messages/{}/'.format(self.server_uri, current_id), headers=header)
                logger.info("msg.status_code {}".format(msg.status_code ))
                if msg.status_code == 200:
                        res = msg.json()
                        logger.info("Received message with key {} and id {}".format(res['process_id'], res['message_id']))
                        value = res['data']
                        current_id += 1
                        return Message(res['process_id'], value)
                elif msg.status_code == 404:
                    time.sleep(6)
            except Exception as ex:
                logger.exception(ex)
