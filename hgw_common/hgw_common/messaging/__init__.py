
class UnknownSender(Exception):
    """
    Exception to be raised when it was impossible to instantiate the correct sender
    """

class UnknownReceiver(Exception):
    """
    Exception to be raised when it was impossible to instantiate the correct receiver
    """

class SendingError(Exception):
    """
    Exception to be raised when a notification error happens
    """

class BrokerConnectionError(Exception):
    """
    Exception to be raised when the connection to a broker fails
    """

class SerializationError(Exception):
    """
    Exception to be raised when error happens during serialization
    """

class DeserializationError(Exception):
    """
    Exception to be raised when error happens during serialization
    """