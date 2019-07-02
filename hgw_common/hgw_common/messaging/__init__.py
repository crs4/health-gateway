
class UnknownSender(Exception):
    """
    Exception to be raised when it was impossible to get the instantiate the correct sender
    """


class SendingError(Exception):
    """
    Exception to be raised when a notification error happens
    """

class SerializationError(Exception):
    """
    Exception to be raised when error happens during serialization
    """