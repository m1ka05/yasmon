from loguru import logger
from abc import ABC, abstractmethod
from typing import Self, Type, TYPE_CHECKING
import asyncio
import yaml

if TYPE_CHECKING:
    from .tasks import AbstractTask

class CallbackAttributeError(Exception):
    "Raised when an undefined attribute is used"
    pass

    def __init__(self, attr, message="undefined attribute {attr}"):
        self.message = message.format(attr=attr)
        super().__init__(self.message)

class AbstractCallback(ABC):
    """
    Abstract class from which all callback classes are derived.

    Derived callbacks are functors and can be used as coroutines for any
    of :class:`yasmon.tasks.AbstractTasks`.
    
    The preferred way to instatiate a callback is from class method :func:`~from_yaml`.
    """

    @abstractmethod
    def __init__(self):
        if not self.name:
            self.name = "Generic Callback"
        logger.info(f'{self.name} ({self.__class__}) initialized')

    @abstractmethod
    async def __call__(self, task: 'AbstractTask', attrs: dict[str,str]):
        """
        Coroutine called by :class:`TaskRunner`.

        :param task: task calling the callback
        """
        logger.info(f'{self.name} ({self.__class__}) called by {task.name} ({task.__class__})')

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


class CallbackDict(dict):
    """
    A dedicated `dictionary` for callbacks.
    """
    def __init__(self, mapping=(), **kwargs):
        super().__init__(mapping, **kwargs)


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

    async def __call__(self, task: 'AbstractTask', attrs: dict[str,str]):
        await super().__call__(task, attrs)

        try:
            cmd = self.cmd.format(**attrs)
        except KeyError as e:
            raise CallbackAttributeError(e)

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
        parsed = yaml.load(data, Loader=yaml.SafeLoader)
        cmd = parsed["command"]
        return cls(name, cmd)

