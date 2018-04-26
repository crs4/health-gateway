import argparse
import json
import logging
import os
import sys
import time
import docker
from Cryptodome.PublicKey import RSA
from hgw_common.cipher import Cipher
from kafka import KafkaConsumer

logger = logging.getLogger('mock_consumer')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PRI_RSA_KEY_PATH = os.path.join(BASE_DIR, 'certs/kafka/payload_encryption/rsa_privatekey_2048')
KAFKA = 'K'
REST = 'R'


def _get_destination_info(container_number):
    info = None
    while info is None:
        try:
            with open('/data/dests_id.json', 'r') as f:
                info = json.load(f)[container_number - 1]
        except FileNotFoundError:
            time.sleep(10)
    return info


def run(consumer):
    with open(PRI_RSA_KEY_PATH, 'rb') as f:
        rsa_pri_key = RSA.importKey(f.read())
        cipher = Cipher(private_key=rsa_pri_key)

    for msg in consumer:
        logger.info("Received message from consumer {} with key: {}".format(consumer.__class__, msg.key))
        message = msg.value
        if cipher.is_encrypted(message):
            message = cipher.decrypt(message)
            logger.info("Message is encrypted")
        logger.info('Message size is {}'.format(sys.getsizeof(message)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run mock consumer')
    parser.add_argument('-c', '--client', dest='client', type=str, choices=(KAFKA, REST), default=KAFKA)
    args = parser.parse_args()

    client = docker.from_env()
    container_number = int(client.containers.get(os.environ['HOSTNAME']).name.split('_')[-1])
    dest_info = _get_destination_info(container_number)

    if args.client == REST:
        import rest_consumer

        consumer = rest_consumer.Consumer(dest_info['client_id'], dest_info['client_secret'],
                                          'https://hgwfrontend:8000')

    else:
        consumer = KafkaConsumer(bootstrap_servers='kafka:9093',
                                 security_protocol='SSL',
                                 ssl_check_hostname=True,
                                 ssl_cafile='/container/certs/ca/kafka/certs/ca/kafka.chain.cert.pem',
                                 ssl_certfile='/container/certs/ca/kafka/certs/destinationmockup/cert.pem',
                                 ssl_keyfile='/container/certs/ca/kafka/certs/destinationmockup/key.pem')

        consumer.subscribe([dest_info['id']])
        logger.info('Topic for the source is: {}'.format(dest_info['id']))

    run(consumer)
