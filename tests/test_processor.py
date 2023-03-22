from yasmon.processor import YAMLProcessor, YAMLSyntaxError
from yasmon.callbacks import CallbackDict, CallbackSyntaxError
from yasmon.callbacks import CallbackNotImplementedError
from yasmon.tasks import TaskNotImplementedError
from yasmon.loggers import LoggerSyntaxError

from loguru import logger
import unittest
from unittest import mock


class YAMLProcessorTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(YAMLProcessorTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor()

    def test_load_file_raise_exceptions(self):
        """
        Test if YAMLProcessor.load_file() raises appropriate exceptions.
        """

        fun = self.proc.load_file

        # FileNotFoundError
        self.assertRaises(FileNotFoundError, fun, "tests/assets/notafile")
        self.assertRaises(FileNotFoundError, fun, "tests/asset/config.yaml")

        # OSError
        with mock.patch('builtins.open') as mock_oserror:
            mock_oserror.side_effect = OSError
            self.assertRaises(OSError, fun, 'tests/assets/config.yaml')

        # Exception
        with mock.patch('builtins.open') as mock_oserror:
            mock_oserror.side_effect = Exception
            self.assertRaises(Exception, fun, 'tests/assets/config.yaml')

        # PermissionError
        with mock.patch('builtins.open') as mock_oserror:
            mock_oserror.side_effect = PermissionError
            self.assertRaises(PermissionError, fun, 'tests/assets/config.yaml')

        # YAMLSyntaxError
        self.assertRaises(YAMLSyntaxError, fun, 'tests/assets/invalid.yaml')

        # empty config file
        path = 'tests/assets/empty.yaml'
        self.assertRaises(YAMLSyntaxError, self.proc.load_file, path)

    def test_load_document_raise_exceptions(self):
        """
        Test if YAMLProcessor.load_document() raises appropriate exceptions.
        """

        # general syntax error
        test_yaml = """
        key: ][
        """
        self.assertRaises(YAMLSyntaxError, self.proc.load_document, test_yaml)

        # config is empty
        test_yaml = """
        """
        self.assertRaises(YAMLSyntaxError, self.proc.load_document, test_yaml)

    def test_add_logger_implemented_loggers(self):
        """
        Test if YAMLProcessor.add_loggers() can process implemented loggers.
        """

        # log_stderr
        test_yaml = """
        log_stderr:
        """
        self.proc.load_document(test_yaml)
        assert len(self.proc.add_loggers()) == 1
        logger.remove()

        # log_stderr with level info
        test_yaml = """
        log_stderr:
            level: info
        """
        self.proc.load_document(test_yaml)
        assert len(self.proc.add_loggers()) == 1
        assert self.proc.data['log_stderr']['level'] == 'info'
        logger.remove()

        # log_journal
        test_yaml = """
        log_journal:
        """
        self.proc.load_document(test_yaml)
        assert len(self.proc.add_loggers()) == 1
        logger.remove()

        # log_journal with level debug
        test_yaml = """
        log_journal:
            level: debug
        """
        self.proc.load_document(test_yaml)
        assert len(self.proc.add_loggers()) == 1
        assert self.proc.data['log_journal']['level'] == 'debug'
        logger.remove()

        # log_file
        test_yaml = """
        log_file:
            path: tests/assets/tmp/logfile
        """
        self.proc.load_document(test_yaml)
        assert self.proc.data['log_file']['path'] == 'tests/assets/tmp/logfile'
        assert len(self.proc.add_loggers()) == 1
        logger.remove()

        # log_file with level debug
        test_yaml = """
        log_file:
            path: tests/assets/tmp/logfile
            level: error
        """
        self.proc.load_document(test_yaml)
        assert len(self.proc.add_loggers()) == 1
        assert self.proc.data['log_file']['level'] == 'error'
        assert self.proc.data['log_file']['path'] == 'tests/assets/tmp/logfile'
        logger.remove()

    def test_add_logger_raise_exceptions(self):
        """
        Test if YAMLProcessor.add_loggers() raises appropriate exceptions.
        """

        # invalid level
        test_yaml = """
        log_stderr:
            level: []
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(LoggerSyntaxError, self.proc.add_loggers)
        logger.remove()

        # invalid level
        test_yaml = """
        log_journal:
            level: []
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(LoggerSyntaxError, self.proc.add_loggers)
        logger.remove()

        # invalid level
        test_yaml = """
        log_file:
            path: /tmp/log
            level: []
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(LoggerSyntaxError, self.proc.add_loggers)
        logger.remove()

        # invalid path
        test_yaml = """
        log_file:
            path: []
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(LoggerSyntaxError, self.proc.add_loggers)
        logger.remove()

        # invalid level (not implemented)
        test_yaml = """
        log_stderr:
            level: notalevel
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(LoggerSyntaxError, self.proc.add_loggers)

        # invalid level (not implemented)
        test_yaml = """
        log_journal:
            level: notalevel
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(LoggerSyntaxError, self.proc.add_loggers)

        # OSError
        test_yaml = """
        log_file:
            path: /tmp/log
        """
        self.proc.load_document(test_yaml)
        with mock.patch('builtins.open') as mock_oserror:
            mock_oserror.side_effect = OSError
            self.assertRaises(OSError, self.proc.add_loggers)

        # missing path for log_file
        test_yaml = """
        log_file:
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(LoggerSyntaxError, self.proc.add_loggers)

        # adds all defined loggers
        test_yaml = """
        log_stderr:
        log_journal:
        log_file:
            path: /tmp/test_add_logger_file.log
        """
        self.proc.load_document(test_yaml)
        assert len(self.proc.add_loggers()) == 3
        assert self.proc.data['log_file']['path'] == '/tmp/test_add_logger_file.log' # noqa
        logger.remove()

    def test_get_tasks_raise_exceptions(self):
        """
        Test if YAMLProcessor.get_tasks() raises appropriate exceptions.
        """

        fun = self.proc.get_tasks

        # tasks not defined
        test_yaml = """
        key:
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(YAMLSyntaxError, fun, CallbackDict())

        # tasks are not a dictionary
        test_yaml = """
        tasks:
            - sometask
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(YAMLSyntaxError, fun, CallbackDict())

        # task is missing callbacks
        test_yaml = """
        tasks:
            sometask:
                type: watchfiles
                paths:
                    - /tmp/
                changes:
                    - added
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(YAMLSyntaxError, fun, CallbackDict())

        # task data (sometask) is not a dictionary
        test_yaml = """
        tasks:
            sometask:
                - type: watchfiles
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(YAMLSyntaxError, fun, CallbackDict())

        # task is not implemented
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: exit 0
        tasks:
            sometask:
                type: notimplemented
                changes:
                    - added
                    - modified
                    - deleted
                paths:
                    - /tmp/
                callbacks:
                    - callback0
        """
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        self.assertRaises(TaskNotImplementedError, fun, callbacks)

    def test_get_callbacks_raise_exceptions(self):
        """
        Test if YAMLProcessor.get_callbacks() raises appropriate exceptions.
        """

        fun = self.proc.get_callbacks

        # callbacks not defined
        test_yaml = """
        tasks:
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(YAMLSyntaxError, fun)

        # callbacks not a dictionary
        test_yaml = """
        callbacks:
            - callback0
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(YAMLSyntaxError, fun)

        # callback data (callback0) is not a dictionary
        test_yaml = """
        callbacks:
            callback0:
                - type: watchfiles
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(YAMLSyntaxError, fun)

        # callback is not implemented
        test_yaml = """
        callbacks:
            callback0:
                type: notimplemented
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(CallbackNotImplementedError, fun)

        # invalid callback syntax
        test_yaml = """
        callbacks:
            callback0:
                type: logger
                level: notdefined
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(CallbackSyntaxError, fun)


if __name__ == '__main__':
    unittest.main(verbosity=2)
