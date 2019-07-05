import json
from json import JSONDecodeError

from hgw_common.messaging import DeserializationError, SerializationError


class Deserializer():
    """
    Generic serializer class. Just define the interface
    """

    def deserialize(self, obj):
        """
        Method that performs the serialization. It must be implemented by subclasses
        """
        raise NotImplementedError

class JSONDeserializer(Deserializer):
    """
    Serialize the object in json format
    """

    def deserialize(self, obj):
        """
        Returns a byte string representing the json serialized object
        """
        try:
            return json.loads(obj)
        except (JSONDecodeError, TypeError):
            raise DeserializationError