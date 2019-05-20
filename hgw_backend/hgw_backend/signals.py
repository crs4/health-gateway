import json

from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

from hgw_backend.settings import (KAFKA_CONNECTOR_NOTIFICATION_TOPIC,
                                  KAFKA_SOURCE_NOTIFICATION_TOPIC)
from hgw_backend.utils import get_kafka_producer

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
        kafka_producer.send(KAFKA_SOURCE_NOTIFICATION_TOPIC, value=json.dumps(message).encode('utf-8'))


def connector_created_handler(connector, **kwargs):
    message = {
        'consent_id': connector['channel_id']
    }
    kafka_producer = get_kafka_producer()
    if kafka_producer is not None:
        kafka_producer.send(KAFKA_CONNECTOR_NOTIFICATION_TOPIC, value=json.dumps(message).encode('utf-8'))
