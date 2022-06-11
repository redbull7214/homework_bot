class SendMessageError(Exception):
    """Исключения при отправки сообщений в телеграмм."""

    pass


class HTTPStatusError(Exception):
    """Исключение для статусов HTTP-ответа, отличных от 200."""

    pass


class TokensError(Exception):
    """Исключение, выбрасываемое при отсутсвии одного из токенов."""

    pass
