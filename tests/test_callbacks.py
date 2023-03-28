from yasmon.processor import YAMLProcessor
from yasmon.tasks import TaskRunner
from yasmon.callbacks import ShellCallback
from yasmon.callbacks import LoggerCallback
from yasmon.callbacks import MailCallback
from yasmon.callbacks import CallbackError
from yasmon.callbacks import CallbackSyntaxError
from yasmon.callbacks import CallbackCircularAttributeError
from yasmon.callbacks import CallbackAttributeError

import unittest
from unittest import mock
import subprocess
import asyncio
import time
import os
import random
import string
import poplib
import email
from email.message import EmailMessage
import filecmp
import mimetypes


class ShellCallbackTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ShellCallbackTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor()
        self.input_producer_script = 'tests/assets/watchfiles_test.sh'
        self.input_producer = None

    def start_input_producer(self):
        self.input_producer = subprocess.Popen(self.input_producer_script,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)

        # wait a moment for input producer (just to be safe)
        time.sleep(1)

    def stop_input_producer(self):
        if self.input_producer:
            self.input_producer.kill()
            self.input_producer.wait()
            self.input_producer.communicate()
            self.input_producer = None

    def test_from_yaml_assignment(self):
        """
        Test ShellCallback.from_yaml() for value assignment.
        """

        test_yaml = """
            type: shell
            command: somecommand
        """
        callback = ShellCallback.from_yaml('name', test_yaml)
        assert callback.name == 'name'
        assert callback.cmd == 'somecommand'

    def test_ShellCallback_raise_exceptions(self):
        """
        Test ShellCallback.from_yaml() for proper exceptions.
        """

        # general yaml error
        test_yaml = """
            type: shell
            command: ]]
        """
        fun = ShellCallback.from_yaml
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # command not defined
        test_yaml = """
            type: shell
        """
        fun = ShellCallback.from_yaml
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # command not a string
        test_yaml = """
            type: shell
            command: []
        """
        fun = ShellCallback.from_yaml
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

    def test_call_success(self):
        """
        Test ShellCallback.__call__() with stdout for success.
        """

        # stdout (command success)
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: echo {myattr}; return 0
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - modified
                paths:
                    - tests/assets/tmp/watchfiles_call_test
                callbacks:
                    - callback0
                attrs:
                    myattr: somevalue
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        try:
            runner.loop.run_until_complete(runner())
        except Exception:
            self.fail()
        self.stop_input_producer()

        # stderr (command failure)
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: ">&2 echo {myattr}; return 1"
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - modified
                paths:
                    - tests/assets/tmp/watchfiles_call_test
                callbacks:
                    - callback0
                attrs:
                    myattr: somevalue
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        try:
            runner.loop.run_until_complete(runner())
        except Exception:
            self.fail()
        self.stop_input_producer()


class LoggerCallbackTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(LoggerCallbackTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor()
        self.input_producer_script = 'tests/assets/watchfiles_test.sh'
        self.input_producer = None

    def start_input_producer(self):
        self.input_producer = subprocess.Popen(self.input_producer_script,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)

        # wait a moment for input producer (just to be safe)
        time.sleep(1)

    def stop_input_producer(self):
        if self.input_producer:
            self.input_producer.kill()
            self.input_producer.wait()
            self.input_producer.communicate()
            self.input_producer = None

    def test_from_yaml_assignment(self):
        """
        Test LoggerCallback.from_yaml() for value assignment.
        """

        test_yaml = """
            level: trace
            message: some message
        """
        callback = LoggerCallback.from_yaml('name', test_yaml)
        assert callback.name == 'name'
        assert callback.level == 'trace'
        assert callback.message == 'some message'

    def test_from_yaml_raise_exceptions(self):
        """
        Test LoggerCallback.from_yaml() for proper exceptions.
        """

        fun = LoggerCallback.from_yaml

        # general yaml error
        test_yaml = """
            level: trace
            message: ]]
        """
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # missing level
        test_yaml = """
            message: some message
        """
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # invalid level type
        test_yaml = """
            level: []
            message: some message
        """
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # invalid level
        test_yaml = """
            level: INVALID
            message: some message
        """
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # missing message
        test_yaml = """
            level: info
        """
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # invalid message type
        test_yaml = """
            level: info
            message: []
        """
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

    def test_call_success(self):
        """
        Test LoggerCallback.__call__() for success.
        """

        test_yaml = """
        callbacks:
            logger0:
                type: logger
                level: info
                message: "{myattr}"
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - modified
                paths:
                    - tests/assets/tmp/watchfiles_call_test
                callbacks:
                    - logger0
                attrs:
                    myattr: somevalue
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        try:
            runner.loop.run_until_complete(runner())
        except Exception:
            self.fail()
        self.stop_input_producer()

    def test_call_raise_exceptions(self):
        """
        Test LoggerCallback.__call__() for proper exceptions
        """

        # CallbackCircularAttributeError
        test_yaml = """
        callbacks:
            logger0:
                type: logger
                level: info
                message: "{myattr}"
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - modified
                paths:
                    - tests/assets/tmp/watchfiles_call_test
                callbacks:
                    - logger0
                attrs:
                    myattr: this {INVALID} attribute
                    INVALID: is {myattr} circular
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        fun = runner.loop.run_until_complete
        self.assertRaises(CallbackCircularAttributeError, fun, runner())
        self.stop_input_producer()

        # CallbackAttributeError
        test_yaml = """
        callbacks:
            logger0:
                type: logger
                level: info
                message: "{myattr}"
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - modified
                paths:
                    - tests/assets/tmp/watchfiles_call_test
                callbacks:
                    - logger0
                attrs:
                    INVALID: myattr is not defined
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        fun = runner.loop.run_until_complete
        self.assertRaises(CallbackAttributeError, fun, runner())
        self.stop_input_producer()


class MailCallbackTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(MailCallbackTest, self).__init__(*args, **kwargs)
        self.SMTP_HOST = os.environ.get('YASMON_SMTP_HOST')
        self.POP3_HOST = os.environ.get('YASMON_POP3_HOST')
        self.SMTP_LOGIN = os.environ.get('YASMON_SMTP_LOGIN')
        self.SMTP_PASSWORD = os.environ.get('YASMON_SMTP_SECRET')

    def test_from_yaml_assignment(self):
        """
        Test MailCallback.from_yaml() for value assignment.
        """

        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            subject: Notification {{subject}}
            message: "{{message}}"
            attach:
                - path/to/file1
                - path/to/file2
            delay: 10
        """
        mail = MailCallback.from_yaml('name', test_yaml)
        assert mail.host == self.SMTP_HOST
        assert mail.port == 587
        assert mail.login == self.SMTP_LOGIN
        assert mail.password == self.SMTP_PASSWORD
        assert mail.security == 'starttls'
        assert mail.fromaddr == '{from}'
        assert mail.toaddr == '{to}'
        assert mail.subject == 'Notification {subject}'
        assert mail.message == '{message}'
        assert mail.attach == ['path/to/file1', 'path/to/file2']
        assert mail.delay == 10

    def test_from_yaml_raise_exceptions(self):
        """
        Test MailCallback.from_yaml() for proper exceptions.
        """

        fun = MailCallback.from_yaml

        # general yaml error
        test_yaml = """
            message: ][
        """
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # missing host
        test_yaml = f"""
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' missing 'host'"

        # missing port
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' missing 'port'"

        # missing login
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' missing 'login'"

        # missing password
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' missing 'password'"

        # missing security
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' missing 'security'"

        # missing subject
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' missing 'subject'"

        # missing to address
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            subject: "Notification: {{subject}}"
            from: {{from}}
            security: starttls
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' missing 'to'"

        # missing from
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' missing 'from'"

        # missing message
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            subject: "Notification: {{subject}}"
            from: {{from}}
            to: "{{to}}"
            security: starttls
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' missing 'message'"

        # port is not and int
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: INVALID
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            security: starttls
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'port' not an int"

        # delay is not and int
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            delay: INVALID
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            security: starttls
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'delay' not an int"

        # host not a string
        test_yaml = f"""
            host: []
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'host' not a str"

        # login not a string
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: []
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: {{to}}
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'login' not a str"

        # password not a string
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: []
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'password' not a str"

        # security not a string
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: []
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'security' not a str"

        # subject not a string
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            subject: []
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'subject' not a str"

        # from not a string
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: []
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'from' not a str"

        # to not a string
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: []
            subject: "Notification: {{subject}}"
            message: "{{message}}"
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'to' not a str"

        # message not a string
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: starttls
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: []
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'message' not a str"

        # invalid security
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: WRONG
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: some message
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' invalid security 'WRONG' value"

        # invalid attach
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: WRONG
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: some message
            attach:
                file0:
                file1:
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' 'attach' not a list"

        # attach list entry not a string
        test_yaml = f"""
            host: "{self.SMTP_HOST}"
            port: 587
            login: "{self.SMTP_LOGIN}"
            password: "{self.SMTP_PASSWORD}"
            security: WRONG
            from: "{{from}}"
            to: "{{to}}"
            subject: "Notification: {{subject}}"
            message: some message
            attach:
                - []
                - /path/to/file
        """
        with self.assertRaises(CallbackSyntaxError) as context:
            fun('name', test_yaml)
        err = context.exception
        assert str(err) == "in callback 'name' invalid attachment"

    def test_call(self):
        """
        Test MailCallback.__call__() to run through.
        """

        # starttls security
        subject_ = ''.join(random.choices(string.ascii_lowercase, k=42))
        message_ = ''.join(random.choices(string.ascii_lowercase, k=42))
        test_yaml = f"""
        callbacks:
            mail0:
                type: mail
                host: "{self.SMTP_HOST}"
                port: 587
                login: "{self.SMTP_LOGIN}"
                password: "{self.SMTP_PASSWORD}"
                security: starttls
                from: "{self.SMTP_LOGIN}"
                to: "{self.SMTP_LOGIN}"
                subject: "{subject_}"
                message: "{message_}{{myattr}}"
                attach:
                    - tests/assets/mailcallback_test_file.png
                delay: 1
        tasks:
            watchfiles:
                type: watchfiles
                changes:
                    - deleted
                paths:
                    - tests/assets/
                callbacks: []
                attrs:
                    myattr: somevalue
        """
        proc = YAMLProcessor()
        proc.load_document(test_yaml)
        callbacks = proc.get_callbacks()
        tasks = proc.get_tasks(callbacks)

        mail = callbacks['mail0']
        task = tasks[0]

        # send out random message
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(mail(task, task.attrs))
            loop.close()
        except Exception:
            self.fail()

        time.sleep(30)  # just to be safe

        # retrive all messages from server and look for our random message
        server = poplib.POP3_SSL(self.POP3_HOST)
        server.user(self.SMTP_LOGIN)
        server.pass_(self.SMTP_PASSWORD)
        content_ = message_ + 'somevalue\n'
        message_correct = False
        content_correct = False
        try:
            num_messages = len(server.list()[1])
            for k in range(1, num_messages + 1):
                envelope = b'\n'.join(server.retr(k)[1])
                message = email.message_from_bytes(
                        envelope, _class=EmailMessage)

                subject = message['Subject']
                subject_correct = (subject == subject_)

                if message.is_multipart():
                    for part in message.walk():
                        ctype = part.get_content_type()
                        if ctype == 'image/png':
                            attachment_content = part.get_payload(decode=True)
                            with open('tests/assets/tmp/ysm_mail_attach',
                                      'wb') as fh:
                                fh.write(attachment_content)

                            attachment_correct = filecmp.cmp(
                                'tests/assets/mailcallback_test_file.png',
                                'tests/assets/tmp/ysm_mail_attach')

                        if ctype == 'text/plain':
                            content = bytes.decode(
                                part.get_payload(decode=True))
                            content_correct = (content == content_)

                if content_correct and subject_correct and attachment_correct:
                    message_correct = True
                server.dele(k)
        except Exception:
            raise
        finally:
            server.quit()

        assert message_correct is True

        # ssl security
        subject_ = ''.join(random.choices(string.ascii_lowercase, k=42))
        message_ = ''.join(random.choices(string.ascii_lowercase, k=42))
        test_yaml = f"""
        callbacks:
            mail0:
                type: mail
                host: "{self.SMTP_HOST}"
                port: 465
                login: "{self.SMTP_LOGIN}"
                password: "{self.SMTP_PASSWORD}"
                security: ssl
                from: "{self.SMTP_LOGIN}"
                to: "{self.SMTP_LOGIN}"
                subject: "{subject_}"
                message: "{message_}{{myattr}}"
                attach:
                    - tests/assets/mailcallback_test_file
                delay: 1
        tasks:
            watchfiles:
                type: watchfiles
                changes:
                    - deleted
                paths:
                    - tests/assets/
                callbacks: []
                attrs:
                    myattr: somevalue
        """
        proc = YAMLProcessor()
        proc.load_document(test_yaml)
        callbacks = proc.get_callbacks()
        tasks = proc.get_tasks(callbacks)

        mail = callbacks['mail0']
        task = tasks[0]

        # send out random message
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(mail(task, task.attrs))
            loop.close()
        except Exception:
            self.fail()

        time.sleep(30)  # just to be safe

        # retrive all messages from server and look for our random message
        server = poplib.POP3_SSL(self.POP3_HOST)
        server.user(self.SMTP_LOGIN)
        server.pass_(self.SMTP_PASSWORD)
        content_ = message_ + 'somevalue\n'
        message_correct = False
        try:
            num_messages = len(server.list()[1])
            for k in range(1, num_messages + 1):
                envelope = b'\n'.join(server.retr(k)[1])
                message = email.message_from_bytes(
                        envelope, _class=EmailMessage)

                subject = message['Subject']
                subject_correct = (subject == subject_)

                content_correct = False
                attachment_correct = False
                if message.is_multipart():
                    for part in message.walk():
                        ctype = part.get_content_type()
                        if ctype == 'text/plain':
                            content = part.get_payload(decode=True)
                            if bytes.decode(content) == content_:
                                content_correct = True

                            if attachment_correct is False:
                                with open('tests/assets/tmp/ysm_mail_attach',
                                          'wb') as fh:
                                    fh.write(content)

                                attachment_correct = filecmp.cmp(
                                    'tests/assets/mailcallback_test_file',
                                    'tests/assets/tmp/ysm_mail_attach')
                if content_correct and subject_correct and attachment_correct:
                    message_correct = True
                server.dele(k)
        except Exception:
            raise
        finally:
            server.quit()

        assert message_correct is True

    def test_call_raises_exceptions(self):
        """
        Test that __call__() raises CallbackError on unexpected exceptions.
        """

        test_yaml = f"""
        callbacks:
            mail_stls:
                type: mail
                host: "{self.SMTP_HOST}"
                port: 587
                login: "{self.SMTP_LOGIN}"
                password: "{self.SMTP_PASSWORD}"
                security: starttls
                from: "{self.SMTP_LOGIN}"
                to: "{self.SMTP_LOGIN}"
                subject: "some subject"
                message: "some message"
                attach:
                    - tests/assets/watchfiles_test.sh
            mail_ssl:
                type: mail
                host: "{self.SMTP_HOST}"
                port: 465
                login: "{self.SMTP_LOGIN}"
                password: "{self.SMTP_PASSWORD}"
                security: ssl
                from: "{self.SMTP_LOGIN}"
                to: "{self.SMTP_LOGIN}"
                subject: "some subject"
                message: "some message"
                attach:
                    - tests/assets/watchfiles_test.sh
        tasks:
            watchfiles:
                type: watchfiles
                changes:
                    - deleted
                paths:
                    - tests/assets/
                callbacks: []
                attrs:
                    myattr: somevalue
        """
        proc = YAMLProcessor()
        proc.load_document(test_yaml)
        callbacks = proc.get_callbacks()
        tasks = proc.get_tasks(callbacks)
        task = tasks[0]

        # starttls CallbackError
        mail = callbacks['mail_ssl']
        with mock.patch('smtplib.SMTP_SSL.login') as mck:
            mck.side_effect = Exception
            loop = asyncio.new_event_loop()
            fun = loop.run_until_complete
            with self.assertRaises(CallbackError) as context:
                fun(mail(task, task.attrs))
            err = context.exception
            err_ = "in callback 'mail_ssl' exception 'Exception' was raised, "
            assert str(err) == err_
            loop.close()

        # starttls CallbackError
        mail = callbacks['mail_stls']
        with mock.patch('smtplib.SMTP.starttls') as mck:
            mck.side_effect = Exception
            loop = asyncio.new_event_loop()
            fun = loop.run_until_complete
            with self.assertRaises(CallbackError) as context:
                fun(mail(task, task.attrs))
            err = context.exception
            err_ = "in callback 'mail_stls' exception 'Exception' was raised, "
            assert str(err) == err_
            loop.close()

        # CallbackError
        mail = callbacks['mail_ssl']
        with mock.patch('yasmon.callbacks.process_attributes') as mck:
            mck.side_effect = CallbackError
            loop = asyncio.new_event_loop()
            fun = loop.run_until_complete
            with self.assertRaises(CallbackError) as context:
                fun(mail(task, task.attrs))
            err = context.exception
            err_ = "callback error"
            assert str(err) == err_
            loop.close()

        # CallbackAttributeError
        mail = callbacks['mail_ssl']
        with mock.patch('yasmon.callbacks.process_attributes') as mck:
            mck.side_effect = CallbackAttributeError('attr')
            loop = asyncio.new_event_loop()
            fun = loop.run_until_complete
            with self.assertRaises(CallbackAttributeError) as context:
                fun(mail(task, task.attrs))
            err = context.exception
            err_ = "undefined attribute attr"
            assert str(err) == err_
            loop.close()

        # CallbackCircularAttributeError
        mail = callbacks['mail_ssl']
        with mock.patch('yasmon.callbacks.process_attributes') as mck:
            mck.side_effect = CallbackCircularAttributeError('expr')
            loop = asyncio.new_event_loop()
            fun = loop.run_until_complete
            with self.assertRaises(CallbackCircularAttributeError) as context:
                fun(mail(task, task.attrs))
            err = context.exception
            err_ = "expr\ndetected circular attributes"
            assert str(err) == err_
            loop.close()

        # CallbackError on process_attributes
        mail = callbacks['mail_ssl']
        with mock.patch('builtins.open') as mock_oserror:
            mock_oserror.side_effect = OSError
            loop = asyncio.new_event_loop()
            fun = loop.run_until_complete
            self.assertRaises(CallbackError, fun, mail(task, task.attrs))


if __name__ == '__main__':
    unittest.main(verbosity=2)
