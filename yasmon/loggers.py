from loguru import logger
from abc import ABC, abstractmethod
import sys
import yaml
import systemd.journal


class LoggerSyntaxError(Exception):
    """
    Raised on logger syntax error
    """

    def __init__(self, message="logger syntax error"):
        self.message = message
        super().__init__(self.message)


class AbstractLogger(ABC):
    """
    Abstract class from which all logger classes are derived.

    The preferred way to instatiate a logger is from class
    method :func:`~from_yaml`.
    """

    @abstractmethod
    def __init__(self):
        self.check_imp_level()
        self.id = self.add_logger()
        logger.info(f'logger ({self.__class__}) initialized')

    @classmethod
    @abstractmethod
    def from_yaml(cls, data: str):
        """
        A class method for constructing a logger from a YAML document.

        :param data: yaml data

        :return: new instance
        """

        logger.debug(f'logger defined form yaml \n{data}')

    def add_logger(self):
        """
        Add logger with logging level.

        :param level: logging level (lower case)
        """

        return logger.add(self.handler,
                          format=self.format,
                          level=self.level.upper())

    def check_imp_level(self):
        imp_levels = [
            'trace',
            'debug',
            'info',
            'success',
            'warning',
            'error',
            'critical'
        ]

        if self.level not in imp_levels:
            raise LoggerSyntaxError(f"""\
            in {self.__class__} invalid logger level {self.level}
            """)


class StdErrLogger(AbstractLogger):
    """
    `stderr` logger.

    The preferred way to instatiate is from class
    method :func:`~from_yaml`.
    """

    def __init__(self, level: str = 'debug', format: str = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | " # noqa
        "<level>{message}</level>"
    )):
        self.handler = sys.stderr
        self.level = level
        self.format = format
        super().__init__()

    @classmethod
    def from_yaml(cls, data: str):
        """
        A class method for constructing a stderr logger from a YAML document.

        :param data: yaml data

        :return: new instance
        """

        try:
            parsed = yaml.safe_load(data)
            super().from_yaml(data)
        except yaml.YAMLError as err:
            raise LoggerSyntaxError(err)

        if parsed is not None and 'level' in parsed:
            if isinstance(parsed['level'], str):
                return cls(parsed['level'])
            else:
                raise LoggerSyntaxError('in log_stderr expected '
                                        'level to be of type str')
        else:
            return cls()


class FileLogger(AbstractLogger):
    """
    Logger logging into a file

    The preferred way to instatiate is from class
    method :func:`~from_yaml`.
    """

    def __init__(self, path: str, level: str = 'debug',
                 format: str = ("<level>{level: <8}</level> | "
                                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | " # noqa
                                "<level>{message}</level>")):
        self.handler = path
        self.path = path
        self.level = level

        self.format = format
        super().__init__()

    @classmethod
    def from_yaml(cls, data: str):
        """
        A class method for constructing a stderr logger from a YAML document.

        :param data: yaml data

        :return: new instance
        """

        try:
            parsed = yaml.safe_load(data)
            super().from_yaml(data)
        except yaml.YAMLError as err:
            raise LoggerSyntaxError(err)

        if parsed is not None and 'path' in parsed:
            path = parsed['path']
            if not isinstance(path, str):
                raise LoggerSyntaxError('in log_file expected '
                                        'path to be of type str')
        else:
            raise LoggerSyntaxError('in logger log_file path is missing')

        if parsed is not None and 'level' in parsed:
            level = parsed['level']
            if not isinstance(level, str):
                raise LoggerSyntaxError('in log_file expected '
                                        'level to be of type str')

            return cls(path, level)

        return cls(path)


class JournalLogger(AbstractLogger):
    """
    System journal logger.

    The preferred way to instatiate is from class
    method :func:`~from_yaml`.
    """

    def __init__(self, level: str = 'debug', format: str = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | " # noqa
        "<level>{message}</level>"
    )):
        self.handler = systemd.journal.JournalHandler()
        self.level = level
        self.format = format
        super().__init__()

    @classmethod
    def from_yaml(cls, data: str):
        """
        A class method for constructing a system journal
        logger from a YAML document.

        :param data: yaml data

        :return: new instance
        """

        try:
            parsed = yaml.safe_load(data)
            super().from_yaml(data)
        except yaml.YAMLError as err:
            raise LoggerSyntaxError(f'in log_journal {err}')

        if parsed is not None and 'level' in parsed:
            level = parsed['level']
            if not isinstance(level, str):
                raise LoggerSyntaxError('in log_journal expected '
                                        'level to be of type str')
            else:
                return cls(level)

        return cls()
