class NagiosResponse:
    def __init__(self, message, code):
        self.message = message
        self.code = code

    def is_ok(self):
        return self.code == 0


def ok(message):
    """
    Constructs an OK(code=0) nagios response with the given message.

    :param message:
    :return: NagiosResponse
    """
    return NagiosResponse(message=f"OK - {message}", code=0)


def warning(message):
    """
    Constructs a WARNING(code=1) nagios response with the given message.

    :param message:
    :return: NagiosResponse
    """
    return NagiosResponse(message=f"WARNING - {message}", code=1)


def critical(message):
    """
    Constructs a CRITICAL(code=2) nagios response with the given message.

    :param message: Description
    :return: NagiosResponse
    """
    return NagiosResponse(message=f"CRITICAL - {message}", code=2)


def unknown(message):
    """
    Constructs an UNKNOWN(code=3) nagios response with the given message.

    :param message:
    :return: NagiosResponse
    """
    return NagiosResponse(message=f"UNKNOWN - {message}", code=3)
