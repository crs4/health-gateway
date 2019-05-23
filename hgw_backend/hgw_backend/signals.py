import json

from django.db.models.signals import post_save
from django.dispatch import Signal, receiver
from kafka.errors import KafkaError

from hgw_backend.settings import (KAFKA_CONNECTOR_NOTIFICATION_TOPIC,
                                  KAFKA_SOURCE_NOTIFICATION_TOPIC)
from hgw_backend.utils import get_kafka_producer
from hgw_common.utils import get_logger

logger = get_logger('hgw_backend')

connector_created = Signal(providing_args=['connector'])


def source_saved_handler(sender, instance, **kwargs):
    """
    Post save signal handler for Source model.
    It sends new Source data to kafka
    """
    message = {
        'source_id': instance.source_id,
        'name': instance.name,
        'profile': {
            'code': instance.profile.code,
            'version': instance.profile.version,
            'payload': instance.profile.payload
        }
    }
    kafka_producer = get_kafka_producer()
    if kafka_producer is not None:
        logger.info('Notifying source creation or update')
        future = kafka_producer.send(KAFKA_SOURCE_NOTIFICATION_TOPIC, value=json.dumps(message).encode('utf-8'))
        # Block for 'synchronous' sends
        try:
            record_metadata = future.get(timeout=10)
        except KafkaError:
            # Decide what to do if produce request failed...
            logger.error('Error notifying source creation or update')
    else:
        logger.info('Error notifying source creation or update: failed kafka connection')


def connector_created_handler(connector, **kwargs):
    message = {
        'channel_id': connector['channel_id']
    }
    kafka_producer = get_kafka_producer()
    if kafka_producer is not None:
        kafka_producer.send(KAFKA_CONNECTOR_NOTIFICATION_TOPIC, value=json.dumps(message).encode('utf-8'))
