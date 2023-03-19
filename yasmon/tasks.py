from loguru import logger
from abc import ABC, abstractmethod
from typing import Self, Optional
from textwrap import dedent
import watchfiles
import asyncio
import signal
import yaml
from .callbacks import AbstractCallback
from .callbacks import CallbackAttributeError, CallbackCircularAttributeError


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


class WatchfilesTask(AbstractTask):
    def __init__(self, name: str, changes: list[watchfiles.Change],
                 callbacks: list[AbstractCallback], paths: list[str],
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
        self.attrs = {} if attrs is None else attrs
        super().__init__()

    async def __call__(self, callback):
        await super().__call__(callback)
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
                    except CallbackCircularAttributeError as err:
                        logger.error(f'in task {self.name} callback {callback.name} raised {err}') # noqa

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

        Possible changes are ``added``, ``modified`` and ``deleted``.

        :param name: unique identifier
        :param data: YAML snippet
        :param callbacks: list of associated callbacks

        :return: new instance
        :rtype: WatchfilesTask
        """
        super().from_yaml(name, data, callbacks)
        try:
            yamldata = yaml.load(data, Loader=yaml.SafeLoader)
        except yaml.YAMLError as err:
            if hasattr(err, 'problem_mark'):
                mark = getattr(err, 'problem_mark')
                problem = getattr(err, 'problem')
                message = (f'YAML problem in line {mark.line} column'
                           f'{mark.column}:\n {problem})')
            elif hasattr(err, 'problem'):
                problem = getattr(err, 'problem')
                message = f'YAML problem:\n {problem}'
            logger.error(message)
            raise err

        changes = [getattr(watchfiles.Change, change)
                   for change in yamldata['changes']]
        paths = yamldata["paths"]
        attrs = yamldata['attrs'] if 'attrs' in yamldata else None
        return cls(name, changes, callbacks, paths, attrs)


class TaskRunner:
    """
    `Asyncio` loop handler. Acts as a functor.
    """
    def __init__(self, tasks: TaskList):
        logger.debug('task runner started...')
        self.tasks = tasks
        self.loop = asyncio.get_event_loop()
        self.loop.set_exception_handler(self.exception_handler)
        for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            self.loop.add_signal_handler(s, lambda s=s: asyncio.create_task(
                self.signal_handler(self.loop, s)))

    def __call__(self):
        try:
            for task in self.tasks:
                for callback in task.callbacks:
                    self.loop.create_task(task(callback))
            self.loop.run_forever()
        finally:
            self.loop.close()
            logger.debug('task runner stopped...')

    @staticmethod
    async def signal_handler(loop, sig: signal.Signals):
        """
        Signal handler.
        """
        logger.debug(f'received {sig.name}')
        tasks = [task for task in asyncio.all_tasks()
                 if task is not asyncio.current_task()]
        for task in tasks:
            task.cancel()

        # Suppress RuntimeError("Already borrowed"), to work around this
        # issue: https://github.com/samuelcolvin/watchfiles/issues/200
        exceptions_buggy = await asyncio.gather(*tasks, return_exceptions=True)
        exceptions = []
        for e in exceptions_buggy:
            if not (isinstance(e, RuntimeError)
                    and str(e) == "Already borrowed"):
                exceptions.append(e)

        # Since there is no cleanup to perform, ignore all CancelledError
        exceptions = list(filter(lambda exception:
                          not isinstance(exception, asyncio.CancelledError),
                          exceptions))

        loop.stop()
        for exception in exceptions:
            logger.error(f'unexpected {exception.__class__.__name__}'
                         f'while cancelling tasks: {exception}')

    @staticmethod
    def exception_handler(*args, **kwargs):
        """
        Exception handler.
        """
        loop, context = args
        message = context.get('exception', context['message'])
        logger.error(dedent(f"""\
        unexpected exception on future {context["future"]}
        message: {message}
        """))

        # this throws exceptions btw (ignored)
        asyncio.create_task(TaskRunner.signal_handler(loop, signal.SIGTERM))
