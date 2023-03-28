from loguru import logger
from abc import ABC, abstractmethod
from typing import Self, TYPE_CHECKING
import asyncio
import yaml
import re
import smtplib
import email
import ssl
import mimetypes
import pathlib

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

    def __init__(self, expr: str,
                 message="{expr}\ndetected circular attributes"):
        self.message = message.format(expr=expr)
        super().__init__(self.message)


class CallbackSyntaxError(Exception):
    """
    Raised on callback syntax error.
    """

    def __init__(self, message="callback syntax error"):
        self.message = message
        super().__init__(self.message)


class CallbackError(Exception):
    """
    Raised on callback execution error.
    """

    def __init__(self, message="callback error"):
        self.message = message
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
        :raises CallbackError: see documentation
        :raises CallbackAttributeError: see documentation
        :raises CallbackCircularAttributeError: see documentation
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


class MailCallback(AbstractCallback):
    """
    Callback implementing sending simple notification mails with
    attachments.
    """

    def __init__(self, name: str, host: str, port: int, login: str,
                 password: str, security: str, toaddr: str, subject: str,
                 fromaddr: str, message: str, attach: list[str],
                 delay: int) -> None:
        """
        :param name: unique callback identifier
        :param host: smtp host
        :param port: smtp port
        :param login: login name
        :param password: password
        :param security: ``starttls`` or ``ssl``
        :param toaddr: to address
        :param subject: mail subject
        :param fromaddr: from address
        :param message: message
        """
        self.name = name
        self.host = host
        self.port = port
        self.login = login
        self.password = password
        self.security = security
        self.toaddr = toaddr
        self.subject = subject
        self.fromaddr = fromaddr
        self.message = message
        self.attach = attach
        self.delay = delay
        super().__init__()

    def send_message_starttls(self, message: email.message.EmailMessage):
        """
        Send message using STARTTLS.
        """

        context = ssl.create_default_context()
        server = smtplib.SMTP(self.host, self.port)
        try:
            server.starttls(context=context)
            server.login(self.login, self.password)
            server.send_message(message)
        except Exception:
            raise
        finally:
            server.quit()

    def send_message_ssl(self, message: email.message.EmailMessage):
        """
        Send message using SSL.
        """

        try:
            server = smtplib.SMTP_SSL(self.host, self.port)
            server.login(self.login, self.password)
            server.send_message(message)
        except Exception:
            raise
        finally:
            server.quit()

    def process_attachments(self, message: email.message.EmailMessage,
                            attrs: dict[str, str]) -> None:
        """
        Process list of attachments from ``attach`` and attach these to
        ``message``.

        :raises CallbackError: if path to file does not exist
        """

        try:
            for attachment in self.attach:
                processed_path = process_attributes(attachment, attrs)
                filepath = pathlib.Path(processed_path)
                filename = filepath.name
                mimetype = mimetypes.guess_type(filename)
                if mimetype[0]:
                    data = mimetype[0].split('/')
                    attachment_mimetype = {
                        'maintype': data[0],
                        'subtype': data[1]
                    }
                else:
                    attachment_mimetype = {
                        'maintype': 'text',
                        'subtype': 'plain'
                    }
                with open(filepath, 'rb') as fh:
                    attachment_content = fh.read()
                    message.add_attachment(
                        attachment_content,
                        maintype=attachment_mimetype.get('maintype'),
                        subtype=attachment_mimetype.get('subtype'),
                        filename=filename)
        except Exception as err:
            raise CallbackError(
                f"in callback '{self.name}' exception "
                f"'{err.__class__.__name__}' was raised, {err}")

    async def __call__(self, task: 'AbstractTask',
                       attrs: dict[str, str]) -> None:
        await super().__call__(task, attrs)

        if self.delay > 0:
            logger.debug(f'{self.name} ({self.__class__}) '
                         f'delayed for {self.delay}')
            await asyncio.sleep(self.delay)

        try:
            message = email.message.EmailMessage()
            message['Subject'] = process_attributes(self.subject, attrs)
            message['From'] = process_attributes(self.fromaddr, attrs)
            message['To'] = process_attributes(self.toaddr, attrs)
            content = process_attributes(self.message, attrs)
            message.set_content(content)
            self.process_attachments(message, attrs)
        except CallbackError:
            raise
        except CallbackAttributeError:
            raise
        except CallbackCircularAttributeError:
            raise

        try:
            loop = asyncio.get_event_loop()
            match self.security:
                case 'starttls':
                    await loop.run_in_executor(
                        None, self.send_message_starttls, message)
                case 'ssl':
                    await loop.run_in_executor(
                        None, self.send_message_ssl, message)
            logger.debug(f'{self.name} ({self.__class__}) '
                         f'sent a mail')
        except Exception as err:
            raise CallbackError(
                f"in callback '{self.name}' exception "
                f"'{err.__class__.__name__}' was raised, {err}")

    @classmethod
    def from_yaml(cls, name: str, data: str) -> Self:
        """
        :class:`MailCallback` can be also constructed from a YAML snippet.

        .. code:: yaml

            host: [SMTP_HOST]
            port: [SMTP_PORT]
            login: [SMTP_LOGIN]
            password: [SMTP_PASSWORD]
            security: [starttls | ssl]
            from: account@host.com
            to: account@anotherhost.com
            subject: Some subject with an attribute {subject}
            message: Some message with attributes {message} {date}
            attach:
                - patch/to/file1
                - patch/to/file2
            delay: 42

        :param name: unique identifier
        :param data: YAML snippet

        :return: new instance
        :rtype: MailCallback
        """
        super().from_yaml(name, data)

        try:
            parsed = yaml.safe_load(data)
        except yaml.YAMLError as err:
            raise CallbackSyntaxError(err)

        required_keys = [
            'host',
            'port',
            'login',
            'password',
            'security',
            'to',
            'subject',
            'from',
            'message'
        ]

        for required_key in required_keys:
            if required_key not in parsed:
                raise CallbackSyntaxError(
                    f"in callback '{name}' missing '{required_key}'")

        host = parsed['host']
        port = parsed['port']
        login = parsed['login']
        password = parsed['password']
        security = parsed['security']
        toaddr = parsed['to']
        subject = parsed['subject']
        fromaddr = parsed['from']
        message = parsed['message']

        attach: list[str] = []
        if 'attach' in parsed:
            if not isinstance(parsed['attach'], list):
                raise CallbackSyntaxError(
                    f"in callback '{name}' 'attach' not a list")

            for attachment in parsed['attach']:
                if not isinstance(attachment, str):
                    raise CallbackSyntaxError(
                        f"in callback '{name}' invalid attachment")

                attach.append(attachment)

        if not isinstance(host, str):
            raise CallbackSyntaxError(
                f"in callback '{name}' 'host' not a str")

        if not isinstance(login, str):
            raise CallbackSyntaxError(
                f"in callback '{name}' 'login' not a str")

        if not isinstance(password, str):
            raise CallbackSyntaxError(
                f"in callback '{name}' 'password' not a str")

        if not isinstance(security, str):
            raise CallbackSyntaxError(
                f"in callback '{name}' 'security' not a str")

        if not isinstance(toaddr, str):
            raise CallbackSyntaxError(
                f"in callback '{name}' 'to' not a str")

        if not isinstance(subject, str):
            raise CallbackSyntaxError(
                f"in callback '{name}' 'subject' not a str")

        if not isinstance(fromaddr, str):
            raise CallbackSyntaxError(
                f"in callback '{name}' 'from' not a str")

        if not isinstance(message, str):
            raise CallbackSyntaxError(
                f"in callback '{name}' 'message' not a str")

        if not isinstance(port, int):
            raise CallbackSyntaxError(
                f"in callback '{name}' 'port' not an int")

        if 'delay' in parsed:
            delay = parsed['delay']
            if not isinstance(delay, int):
                raise CallbackSyntaxError(
                    f"in callback '{name}' 'delay' not an int")
        else:
            delay = 0

        if security not in ['starttls', 'ssl']:
            raise CallbackSyntaxError(
                f"in callback '{name}' invalid "
                f"security '{security}' value")

        return cls(name, host, port, login, password, security,
                   toaddr, subject, fromaddr, message, attach, delay)
