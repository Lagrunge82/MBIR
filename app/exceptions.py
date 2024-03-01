class BaseAppException(Exception):
    pass


class AppInitException(BaseAppException):
    pass


class ConfigError(AppInitException):
    pass

