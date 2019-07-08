import json
from json import JSONDecodeError

from yaml.serializer import Serializer

from hgw_common.messaging import SerializationError


class Serializer():
    """
    Generic serializer class. Just define the interface
    """

    def serialize(self, obj):
        """
        Method that performs the serialization. It must be implemented by subclasses
        """
        raise NotImplementedError

class JSONSerializer(Serializer):
    """
    Serialize the object in json format
    """

    def serialize(self, obj):
        """
        Returns a byte string representing the json serialized object
        """
        try:
            return json.dumps(obj).encode('utf-8')
        except TypeError:
            raise SerializationError


class RawSerializer(Serializer):
    """
    It is a Serializer that doesn't serialize at all
    """

    def serialize(self, obj):
        """
        Returns exactly the same object in input
        """
        return obj
