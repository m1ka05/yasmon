from loguru import logger
from abc import ABC, abstractmethod
from typing import Self, TYPE_CHECKING
from textwrap import dedent
import asyncio
import yaml
import re

if TYPE_CHECKING:
    from .tasks import AbstractTask


def process_attributes(expr: str, attrs: dict[str, str]) -> str:
    """
    Performs attribute substitutions in `expr`.

    This is also checking for circular dependencies (`max_depth = 42`).

    :param expr: expression to process
    :param attrs: attributes to substitute

    :raises CallbackCircularAttributeError: see documentation
    :raises CallbackAttributeError: see documentation

    :return: processed expression
    :rtype: str
    """
    max_depth = 42
    regex = re.compile(r"\{[^{}]*\}")  # match attributes
    search = regex.search(expr)

    depth = 0
    while search:
        try:
            expr = expr.format(**attrs)
        except KeyError as e:
            raise CallbackAttributeError(e)

        if depth < max_depth:
            depth += 1
        else:
            raise CallbackCircularAttributeError(expr)

        search = regex.search(expr)

    return expr


class CallbackNotImplementedError(Exception):
    """
    Raised if a requested callback type is not implemented.
    """

    def __init__(self, type: str, message="callback {type} not implemented"):
        self.message = message.format(type=type)
        super().__init__(self.message)


class CallbackAttributeError(Exception):
    """
    Raised when an undefined task attribute is used by a callback.
    """

    def __init__(self, attr: str, message="undefined attribute {attr}"):
        self.message = message.format(attr=attr)
        super().__init__(self.message)


class CallbackCircularAttributeError(Exception):
    """
    Raised when task attributes have circular dependencies.
    """

    def __init__(self, expr: str, message=dedent("""\
    {expr}\ndetected circular attributes""")):
        self.message = message.format(expr=expr)
        super().__init__(self.message)


class CallbackSyntaxError(Exception):
    """
    Raised on callback syntax error.
    """

    def __init__(self, hint: str, message="callback syntax error"):
        self.message = message.format(hint=hint)
        super().__init__(self.message)


class CallbackDict(dict):
    """
    A dedicated `dictionary` for callbacks.
    """

    def __init__(self, mapping=(), **kwargs):
        super().__init__(mapping, **kwargs)


class AbstractCallback(ABC):
    """
    Abstract class from which all callback classes are derived.

    Derived callbacks are functors and can be used as coroutines for any
    of :class:`yasmon.tasks.AbstractTasks`.

    The preferred way to instatiate a callback is from class
    method :func:`~from_yaml`.
    """

    @abstractmethod
    def __init__(self):
        if not self.name:
            self.name = "Generic Callback"
        logger.info(f'{self.name} ({self.__class__}) initialized')

    @abstractmethod
    async def __call__(self, task: 'AbstractTask', attrs: dict[str, str]):
        """
        Coroutine called by :class:`TaskRunner`.

        :param task: task calling the callback
        """
        logger.info(f'{self.name} ({self.__class__}) called by '
                    f'{task.name} ({task.__class__})')

    @classmethod
    @abstractmethod
    def from_yaml(cls, name: str, data: str):
        """
        A class method for constructing a callback from a YAML document.

        :param name: unique identifier
        :param data: yaml data

        :return: new instance
        """
        logger.debug(f'{name} defined form yaml \n{data}')


class ShellCallback(AbstractCallback):
    """
    Callback implementing shell command execution.
    """

    def __init__(self, name: str, cmd: str) -> None:
        """
        :param name: unique identifier
        :param cmd: command to be executed
        """
        self.name = name
        self.cmd = cmd
        super().__init__()

    async def __call__(self, task: 'AbstractTask', attrs: dict[str, str]):
        await super().__call__(task, attrs)

        try:
            cmd = process_attributes(self.cmd, attrs)
        except CallbackAttributeError:
            raise
        except CallbackCircularAttributeError:
            raise

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await proc.communicate()
        out = stdout.decode()
        err = stderr.decode()

        if out:
            logger.info(f'callback {self.name} stdout:\n {out}')

        if err:
            logger.error(f'callback {self.name} stderr:\n {err}')

        return stdout, stderr

    @classmethod
    def from_yaml(cls, name: str, data: str) -> Self:
        """
        :class:`ShellCallback` can be also constructed from a YAML snippet.

        .. code:: yaml

            command: ls -lah /path/to/some/dir/

        :param name: unique identifier
        :param data: YAML snippet

        :return: new instance
        :rtype: ShellCallback
        """
        super().from_yaml(name, data)
        try:
            parsed = yaml.safe_load(data)
        except yaml.YAMLError as err:
            raise CallbackSyntaxError(err)

        if 'command' not in parsed:
            raise CallbackSyntaxError(f"""\
            in callback {name} missig command
            """)

        if not isinstance(parsed['command'], str):
            raise CallbackSyntaxError(f"""\
            in callback {name} not a string
            """)

        cmd = parsed["command"]
        return cls(name, cmd)


class LoggerCallback(AbstractCallback):
    """
    Callback implementing logger calls
    """

    def __init__(self, name: str, level: str, message: str) -> None:
        """
        :param name: unique identifier
        :param level: logging level
        :param message: message to pass to logger
        """
        self.name = name
        self.level = level
        self.message = message
        super().__init__()

    async def __call__(self, task: 'AbstractTask',
                       attrs: dict[str, str]) -> None:
        await super().__call__(task, attrs)

        try:
            message = process_attributes(self.message, attrs)
        except CallbackAttributeError:
            raise
        except CallbackCircularAttributeError:
            raise

        method = getattr(logger, self.level)
        method(message)

    @classmethod
    def from_yaml(cls, name: str, data: str) -> Self:
        """
        :class:`LoggerCallback` can be also constructed from a YAML snippet.

        .. code:: yaml

            level: [error | info | debug | ... (see Loguru docs)]
            message: message

        :param name: unique identifier
        :param data: YAML snippet

        :return: new instance
        :rtype: LoggerCallback
        """
        super().from_yaml(name, data)
        try:
            parsed = yaml.safe_load(data)
        except yaml.YAMLError as err:
            raise CallbackSyntaxError(err)

        imp_levels = [
            'trace',
            'debug',
            'info',
            'success',
            'warning',
            'error',
            'critical'
        ]

        if 'level' not in parsed:
            raise CallbackSyntaxError(f"""\
            in callback {name} missig logger level
            """)

        level = parsed["level"]
        if level not in imp_levels:
            raise CallbackSyntaxError(f"""\
            in callback {name} invalid logger level {level}
            """)

        if 'message' not in parsed:
            raise CallbackSyntaxError(f"""\
            in callback {name} missig message
            """)

        if not isinstance(parsed['message'], str):
            raise CallbackSyntaxError(f"""\
            in callback {name} message not a string
            """)

        message = parsed["message"]
        return cls(name, level, message)
