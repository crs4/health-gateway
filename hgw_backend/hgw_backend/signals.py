from django.dispatch import Signal

from hgw_backend.settings import (KAFKA_CONNECTOR_NOTIFICATION_TOPIC,
                                  KAFKA_SOURCE_NOTIFICATION_TOPIC)
from hgw_common.messaging.sender import create_sender
from hgw_common.utils import create_broker_parameters_from_settings, get_logger

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

    sender = create_sender(create_broker_parameters_from_settings())
    if sender.send(KAFKA_SOURCE_NOTIFICATION_TOPIC, message):
        logger.info("Souce notified correctly")


def connector_created_handler(connector, **kwargs):
    """
    Handler for signal create_connector. It notifies the correct operation
    """
    message = {
        'channel_id': connector['channel_id']
    }
    sender = create_sender(create_broker_parameters_from_settings())
    if sender.send(KAFKA_CONNECTOR_NOTIFICATION_TOPIC, message):
        logger.info("Connector notified correctly")
