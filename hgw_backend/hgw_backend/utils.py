from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from _ssl import SSLError
from hgw_backend.settings import (KAFKA_BROKER, KAFKA_CA_CERT,
                                  KAFKA_CLIENT_CERT, KAFKA_CLIENT_KEY,
                                  KAFKA_SSL)
from hgw_common.utils import get_logger

logger = get_logger('hgw_backend')


def get_kafka_producer():
    """
    Returns a kafka producer with parameters read from settings. 
    If error happens during the connection to the broker, it returns None
    """
    if KAFKA_SSL:
        consumer_params = {
            'bootstrap_servers': KAFKA_BROKER,
            'security_protocol': 'SSL',
            'ssl_check_hostname': True,
            'ssl_cafile': KAFKA_CA_CERT,
            'ssl_certfile': KAFKA_CLIENT_CERT,
            'ssl_keyfile': KAFKA_CLIENT_KEY
        }
    else:
        consumer_params = {
            'bootstrap_servers': KAFKA_BROKER
        }
    try:
        return KafkaProducer(**consumer_params)
    except NoBrokersAvailable:
        logger.error('Cannot connect to kafka broker')
        return None
    except SSLError:
        logger.error('Failed authentication connection to kafka broker. Wrong certs')
        return None
