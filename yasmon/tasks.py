from yasmon.callbacks import AbstractCallback
from yasmon.callbacks import CallbackAttributeError
from yasmon.callbacks import CallbackCircularAttributeError

from loguru import logger
from abc import ABC, abstractmethod
from typing import Self, Optional
import watchfiles
import asyncio
import signal
import yaml
import pathlib


class TaskSyntaxError(Exception):
    """
    Raised on task syntax issue.
    """

    def __init__(self, message="task syntax error"):
        self.message = message
        super().__init__(self.message)


class TaskNotImplementedError(Exception):
    """
    Raised if a requested task type is not implemented.
    """

    def __init__(self, type, message="task {type} not implemented"):
        self.message = message.format(type=type)
        super().__init__(self.message)


class AbstractTask(ABC):
    """
    Abstract class from which all task classes are derived.

    Derived tasks are functors calling the assigned callback coroutine
    and can be used for :class:`yasmon.tasks.TaskRunner`.

    The preferred way to instatiate a task is from class
    method :func:`~from_yaml`.
    """
    @abstractmethod
    def __init__(self):
        if not self.name:
            self.name = "Generic Task"
        if not self.attrs:
            self.attrs = {}
        logger.info(f'{self.name} ({self.__class__}) initialized')

    @abstractmethod
    async def __call__(self, callback: AbstractCallback):
        """
        Coroutine called by :class:`TaskRunner`.
        """
        logger.info(f'{self.name} ({self.__class__}) scheduled with '
                    f'{callback.name} ({callback.__class__})')

    @classmethod
    @abstractmethod
    def from_yaml(cls, name: str, data: str,
                  callbacks: list[AbstractCallback]):
        """
        A class method for constructing a callback from a YAML document.

        :param name: unique identifier
        :param data: yaml data
        :param callbacks: collection of callbacks

        :return: new instance
        """
        logger.debug(f'{name} defined from yaml \n{data}')


class TaskList(list):
    """
    A dedicated `list` for tasks.
    """
    def __init__(self, iterable: Optional[list[AbstractTask]] = None):
        if iterable is not None:
            super().__init__(item for item in iterable)
        else:
            super().__init__()


class TaskError(Exception):
    """
    Raised when a path watched by task does not exist anymore.
    """

    def __init__(self, task, message="error in task {task}"):
        self.message = message.format(task=task)
        super().__init__(self.message)


class WatchfilesTask(AbstractTask):
    def __init__(self, name: str, changes: list[watchfiles.Change],
                 callbacks: list[AbstractCallback], paths: list[str],
                 timeout: int, max_retry: int,
                 attrs: Optional[dict[str, str]] = None) -> None:
        """
        :param name: unique identifier
        :param changes: list of watchfiles events
        :param callbacks: assigned callbacks
        :param paths: paths to watch (files/directories)
        :param attrs: (static) attributes
        """
        self.name = name
        self.changes = changes
        self.callbacks = callbacks
        self.paths = paths
        self.abs_paths = []  # resolved upon self.__call__()
        self.attrs = {} if attrs is None else attrs
        self.max_retry = max_retry
        self.timeout = timeout
        super().__init__()

    async def __call__(self, callback):
        await super().__call__(callback)
        retry = 0
        max_retry = 'inf' if self.max_retry == -1 else self.max_retry

        while True:
            try:
                for path in self.paths:
                    if not pathlib.Path.exists(pathlib.Path(path)):
                        raise FileNotFoundError(path)
                    else:
                        abs_path = pathlib.Path(path).resolve()
                        self.abs_paths.append(str(abs_path))
            except FileNotFoundError as path:
                if retry == self.max_retry and self.max_retry > -1:
                    logger.error(f'in task {self.name}'
                                 f' path {path} does not exist '
                                 f'and max_retry {self.max_retry} '
                                 'was reached')
                    raise TaskError(self.name)
                else:
                    retry += 1
                    logger.warning(f'in task {self.name}'
                                   f' path {path} does not exist (anymore)'
                                   f'... retrying callback {callback.name}'
                                   f' after {self.timeout} sec timeout '
                                   f' ({retry}/{max_retry} retries)')
                    await asyncio.sleep(self.timeout)
                    continue

            # run awatch loop if all paths exist
            try:
                await self.awatch_loop(callback)
            except FileNotFoundError:
                continue
            finally:
                retry = 0

    async def awatch_loop(self, callback):
        async for changes in watchfiles.awatch(*self.paths):
            for (change, path) in changes:
                if change in self.changes:
                    match change:
                        case watchfiles.Change.added:
                            chng = 'added'
                        case watchfiles.Change.modified:
                            chng = 'modified'
                        case watchfiles.Change.deleted:
                            chng = 'deleted'
                    try:
                        call_attrs = {'change': chng, 'path': path}
                        await callback(self, self.attrs | call_attrs)
                    except CallbackAttributeError as err:
                        logger.error(f'in task {self.name} callback {callback.name} raised {err}') # noqa
                        raise err
                    except CallbackCircularAttributeError as err:
                        logger.error(f'in task {self.name} callback {callback.name} raised {err}') # noqa
                        raise err

                if (change == watchfiles.Change.deleted and
                        path in self.abs_paths):
                    raise FileNotFoundError

    @classmethod
    def from_yaml(cls, name: str, data: str,
                  callbacks: list[AbstractCallback]) -> Self:
        """
        :class:`WatchfilesTask` can be also constructed from a YAML snippet.

        .. code:: yaml

            changes:
                - added
            callbacks:
                - callback0
            paths:
                - /some/path/to/file1
                - /some/path/to/file2
            attrs:
                myattr: value
            timeout: 10
            max_retry: 3

        Possible changes are ``added``, ``modified`` and ``deleted``.

        :param name: unique identifier
        :param data: YAML snippet
        :param callbacks: list of associated callbacks

        :return: new instance
        :rtype: WatchfilesTask
        """
        super().from_yaml(name, data, callbacks)
        try:
            yamldata = yaml.safe_load(data)
        except yaml.YAMLError as err:
            raise TaskSyntaxError(err)

        if 'timeout' in yamldata:
            try:
                timeout = int(yamldata['timeout'])
                if not timeout > 0:
                    raise ValueError
            except ValueError:
                raise TaskSyntaxError(f"in task {name}: invalid timeout")
            except TypeError:
                raise TaskSyntaxError(f"in task {name}: timeout not integer")
        else:
            timeout = 30

        if 'max_retry' in yamldata:
            try:
                max_retry = int(yamldata['max_retry'])
            except ValueError:
                raise TaskSyntaxError(f"in task {name}: invalid max_retry")
            except TypeError:
                raise TaskSyntaxError(f"in task {name}: max_retry not integer")
        else:
            max_retry = 5

        if 'changes' not in yamldata:
            raise TaskSyntaxError(f"in task {name}: "
                                  "missing changes list")

        if 'paths' not in yamldata:
            raise TaskSyntaxError(f"in task {name}: "
                                  "missing paths list")

        if not isinstance(yamldata['paths'], list):
            raise TaskSyntaxError(f"in task {name}: "
                                  "paths must be a list")

        for path in yamldata['paths']:
            if not isinstance(path, str):
                raise TaskSyntaxError(f"in task {name}: "
                                      "paths must be strings")

        if len(yamldata['paths']) < 1:
            raise TaskSyntaxError(f"in task {name}: "
                                  "at least one path required")

        if 'attrs' in yamldata:
            if not isinstance(yamldata['attrs'], dict):
                raise TaskSyntaxError(f"in task {name}: "
                                      "attrs must be a dictionary")

        imp_changes = ['added', 'modified', 'deleted']
        for change in yamldata['changes']:
            if change not in imp_changes:
                raise TaskSyntaxError(f"in task {name}: "
                                      f"invalid change {change}")

        if not isinstance(yamldata['changes'], list):
            raise TaskSyntaxError(f"in task {name}: "
                                  "changes must be a list")

        changes = [getattr(watchfiles.Change, change)
                   for change in yamldata['changes']]

        paths = yamldata["paths"]
        attrs = yamldata['attrs'] if 'attrs' in yamldata else None
        return cls(name, changes, callbacks, paths, timeout, max_retry, attrs)


class TaskRunner:
    """
    `Asyncio` loop handler. Acts as a functor.
    """
    def __init__(self, tasks: TaskList, testenv: bool = False):
        logger.debug('task runner started...')
        self.loop = asyncio.get_event_loop()
        self.tasks = []

        if testenv:
            self.loop = asyncio.new_event_loop()
            self.tasks.append(
                self.loop.create_task(self.cancle_tasks()))

        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            self.loop.add_signal_handler(s, lambda s=s: asyncio.create_task(
                self.signal_handler(s)))

        for task in tasks:
            for callback in task.callbacks:
                self.tasks.append(
                    self.loop.create_task(task(callback)))

    async def __call__(self):
        for task in asyncio.as_completed(self.tasks):
            try:
                await task
            except RuntimeError as err:
                if str(err) == "Already borrowed":
                    # Suppress RuntimeError("Already borrowed"), to
                    # work around this issue:
                    # https://github.com/samuelcolvin/watchfiles/issues/200
                    pass
                else:
                    raise
            except asyncio.CancelledError:
                raise
            except Exception:
                raise

    async def signal_handler(self, sig: signal.Signals):
        """
        Signal handler.
        """
        logger.debug(f'received {sig.name}')
        for task in self.tasks:
            task.cancel()

    async def cancle_tasks(self, delay=2):
        """
        Cancle tasks (for testing purposes)
        """
        await asyncio.sleep(delay)
        for task in self.tasks:
            if task is not asyncio.current_task():
                task.cancel()
