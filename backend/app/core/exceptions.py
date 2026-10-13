class MonError(Exception):
    """Erro base da aplicação."""

    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(MonError):
    status_code = 404


class AuthenticationError(MonError):
    status_code = 401


class PermissionDeniedError(MonError):
    status_code = 403


class ConflictError(MonError):
    status_code = 409


class ValidationError(MonError):
    status_code = 422


class UnsupportedFileTypeError(ValidationError):
    pass


class ProviderNotConfiguredError(MonError):
    status_code = 503


class ExtractionError(MonError):
    status_code = 422
