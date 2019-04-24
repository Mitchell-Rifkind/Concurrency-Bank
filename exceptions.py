class Error(Exception):
    pass


class DatabaseConnectionError(Error):
    pass


class NoDatabaseConnectionError(Error):
    pass
