from django.dispatch import Signal

from hgw_backend.settings import (KAFKA_CONNECTOR_NOTIFICATION_TOPIC,
                                  KAFKA_SOURCE_NOTIFICATION_TOPIC)
from hgw_common.notifier import get_notifier
from hgw_common.serializers import ProfileSerializer
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
        'profile': ProfileSerializer(instance=instance.profile).data
    }


    notifier = get_notifier(KAFKA_SOURCE_NOTIFICATION_TOPIC)
    if notifier.notify(message):
        logger.info("Souce notified correctly")


def connector_created_handler(connector, **kwargs):
    """
    Handler for signal create_connector. It notifies the correct operation
    """
    message = {
        'channel_id': connector['channel_id']
    }
    notifier = get_notifier(KAFKA_CONNECTOR_NOTIFICATION_TOPIC)
    if notifier.notify(message):
        logger.info("Connector notified correctly")
