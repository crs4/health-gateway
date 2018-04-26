# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import argparse
import logging
import os

import requests
import sys

import time

import yaml
from kafka import KafkaConsumer, TopicPartition, KafkaProducer
from kafka.errors import KafkaError
from oauthlib.oauth2 import BackendApplicationClient, InvalidClientError, TokenExpiredError
from requests_oauthlib import OAuth2Session

logger = logging.getLogger('dispatcher')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def get_path(base_path, file_path):
    return file_path if os.path.isabs(file_path) else os.path.join(base_path, file_path)


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# The order of the paths is important. We will give priority to the one in etc
_CONF_FILES_PATH = ['/etc/hgw_service/hgw_dispatcher_config.yml', get_path(BASE_DIR, './config.yml')]

cfg = None
_conf_file = None
for cf in _CONF_FILES_PATH:
    try:
        with open(cf, 'r') as f:
            cfg = yaml.load(f)
    except FileNotFoundError:
        continue
    else:
        _conf_file = cf
        break
if cfg is None:
    sys.exit("Config file not found")

BASE_CONF_DIR = os.path.dirname(os.path.abspath(_conf_file))

CONSENT_MANAGER_URI = cfg['consent_manager']['uri']
CONSENT_MANAGER_OAUTH_CLIENT_ID = cfg['consent_manager']['client_id']
CONSENT_MANAGER_OAUTH_CLIENT_SECRET = cfg['consent_manager']['client_secret']

HGW_FRONTEND_URI = cfg['hgw_frontend']['uri']
HGW_FRONTEND_OAUTH_CLIENT_ID = cfg['hgw_frontend']['client_id']
HGW_FRONTEND_OAUTH_CLIENT_SECRET = cfg['hgw_frontend']['client_secret']

HGW_BACKEND_URI = cfg['hgw_backend']['uri']

KAFKA_BROKER = cfg['kafka']['uri']
KAFKA_CA_CERT = get_path(BASE_CONF_DIR, cfg['kafka']['ca_cert'])
KAFKA_CLIENT_CERT = get_path(BASE_CONF_DIR, cfg['kafka']['client_cert'])
KAFKA_CLIENT_KEY = get_path(BASE_CONF_DIR, cfg['kafka']['client_key'])


class Dispatcher(object):
    def __init__(self, broker_url, ca_cert, client_cert, client_key):
        logger.debug("Querying for sources")
        self.consumer_topics = self._get_sources()
        logger.debug("Found {} sources: ".format(len(self.consumer_topics)))
        logger.debug("Sources ids are: {}".format(self.consumer_topics))
        logger.debug("broker_url: {}".format(broker_url))
        self.consumer = KafkaConsumer(bootstrap_servers=broker_url,
                                      security_protocol='SSL',
                                      ssl_check_hostname=True,
                                      ssl_cafile=ca_cert,
                                      ssl_certfile=client_cert,
                                      ssl_keyfile=client_key,
                                      group_id='DISPATCHER')

        subscriptions = []
        for source_id in self.consumer_topics:
            if self.consumer.partitions_for_topic(source_id) is not None:
                logger.debug("Subscribing to {} topic".format(source_id))
                subscriptions.append(source_id)
        if len(subscriptions) == 0:
            logger.error("There are no topics available. Exiting...")
            sys.exit(2)

        self.consumer.subscribe(subscriptions)
        # TODO: decide if we want it to restart from the beginning or not
        # self.consumer.seek_to_beginning(self.consumer.subscription())

        logger.debug("Subscribed to {} source topics".format(len(subscriptions)))

        self.producer = KafkaProducer(bootstrap_servers=broker_url,
                                      security_protocol='SSL',
                                      ssl_check_hostname=True,
                                      ssl_cafile=ca_cert,
                                      ssl_certfile=client_cert,
                                      ssl_keyfile=client_key)
        self._obtain_consent_oauth_token()
        self._obtain_hgw_frontend_oauth_token()

    @staticmethod
    def _get_sources(loop=True):
        try:
            res = requests.get('{}/v1/sources/'.format(HGW_BACKEND_URI))
            return [d['source_id'] for d in res.json()]
        except Exception as ex:
            if loop:
                logger.exception(ex)
                time.sleep(2)
                return Dispatcher._get_sources()
            raise ex

    @staticmethod
    def _obtain_oauth_token(url, client_id, client_secret):
        logger.debug('Getting OAuth token from {}'.format(url))
        client = BackendApplicationClient(client_id)
        oauth_session = OAuth2Session(client=client)
        token_url = '{}/oauth2/token/'.format(url)
        try:
            res = oauth_session.fetch_token(token_url=token_url, client_id=client_id,
                                            client_secret=client_secret)
        except InvalidClientError:
            return None
        except requests.exceptions.ConnectionError as e:
            return None

        if 'access_token' in res:
            logger.debug('Token obtained')
            return oauth_session
        else:
            logger.debug('Error obtaining token')
            return None

    def _obtain_hgw_frontend_oauth_token(self):
        self.hgw_frontend_oauth_session = self._obtain_oauth_token(HGW_FRONTEND_URI,
                                                                   HGW_FRONTEND_OAUTH_CLIENT_ID,
                                                                   HGW_FRONTEND_OAUTH_CLIENT_SECRET)
        if self.hgw_frontend_oauth_session is None:
            sys.exit(1)

    def _obtain_consent_oauth_token(self):
        self.consent_oauth_session = self._obtain_oauth_token(CONSENT_MANAGER_URI,
                                                              CONSENT_MANAGER_OAUTH_CLIENT_ID,
                                                              CONSENT_MANAGER_OAUTH_CLIENT_SECRET)
        if self.consent_oauth_session is None:
            sys.exit(1)

    def _get_process_id(self, channel_id):
        try:
            fr = self.hgw_frontend_oauth_session.get('{}/v1/flow_requests/search/?channel_id={}'.
                                                     format(HGW_FRONTEND_URI, channel_id))
        except TokenExpiredError:
            logger.debug('Frontend token expired: getting new one')
            # hgw frontend token expired. Getting a new one
            self._obtain_hgw_frontend_oauth_token()
            fr = self.hgw_frontend_oauth_session.get('{}/v1/flow_requests/search/?channel_id={}'.
                                                     format(HGW_FRONTEND_URI, channel_id))
        logger.debug(fr.json())

        if fr.status_code == 200:
            return fr.json()['process_id']
        else:
            return None

    def _process_message(self, channel_id, payload):
        try:
            logger.debug("Checking the consent manager to get the consent status")
            try:
                cm_res = self.consent_oauth_session.get('{}/v1/consents/{}/'.format(CONSENT_MANAGER_URI, channel_id))
            except TokenExpiredError:
                logger.debug('Consent token expired: getting new one')
                self._obtain_consent_oauth_token()
                cm_res = self.consent_oauth_session.get('{}/v1/consents/{}/'.format(CONSENT_MANAGER_URI, channel_id))
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to the Consent Manager to verify the channel status. Skipping")
        else:
            if cm_res.status_code == 200:
                consent = cm_res.json()
                if consent['status'] == 'AC':
                    dest_id = consent['destination']['id']
                    try:
                        process_id = self._get_process_id(channel_id)
                    except requests.exceptions.ConnectionError:
                        logger.error("Cannot connect to HGW Frontend to get the process id. Skipping")
                    else:
                        if process_id:
                            logger.debug('Sending to destination {} with process_id {}'.format(dest_id, process_id))
                            future = self.producer.send(dest_id, payload, key=process_id.encode('utf-8'))
                            try:
                                record_metadata = future.get(timeout=5)
                            except KafkaError as e:
                                logger.info("Error sending record")
                                logger.info(e)
                            else:
                                logger.info("Sent message to topic: {}".format(record_metadata.topic))
                        else:
                            logger.debug('Process id not found for the channel id')
                elif consent['status'] == 'RE':
                    logger.info('Sent message to a revoked channel')
                elif consent['status'] == 'PE':
                    logger.info('Tried to send a message to a revoked channel. Discarding')
                else:
                    logger.info('Sent message to an invalid channel')
            else:
                logger.error('Error retrieving consent status for the channel {}. Status: {}'.format(
                    channel_id, cm_res.status_code))

    def run(self):
        # partition = TopicPartition(self.consumer_topics[0], 0)
        for msg in self.consumer:
            # logger.debug("Reading offset {}. Last offset is {}".format(msg.offset, self.consumer.highwater(partition)))
            # logger.debug(self.consumer.assignment())
            if msg.key:
                channel_id = msg.key.decode('utf-8')
                logger.debug('Received message from {} for channel {}'.format(msg.topic, channel_id))
                payload = msg.value
                self._process_message(channel_id, payload)
            else:
                logger.debug('Rejecting message from {}. Channel id not specified'.format(msg.topic))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dispatch messages from a source to a destination')
    parser.add_argument('--kafka-server', dest='kafka_server', type=str, help='the kafka server to use')
    parser.add_argument('--kafka-ca-cert', dest='kafka_ca_cert', type=str, help='the kafka CA certificate')
    parser.add_argument('--kafka-client-cert', dest='kafka_client_cert', type=str, help='the kafka client certificate')
    parser.add_argument('--kafka-client-key', dest='kafka_client_key', type=str, help='the kafka client key')

    args = parser.parse_args()
    kafka_server = args.kafka_server or KAFKA_BROKER
    kafka_ca_cert = args.kafka_server or KAFKA_CA_CERT
    kafka_client_cert = args.kafka_server or KAFKA_CLIENT_CERT
    kafka_client_key = args.kafka_server or KAFKA_CLIENT_KEY

    disp = Dispatcher(kafka_server, kafka_ca_cert, kafka_client_cert, kafka_client_key)
    disp.run()
