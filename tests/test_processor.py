from yasmon import YAMLProcessor, CallbackDict, CallbackSyntaxError
from loguru import logger
import unittest
import yaml
from textwrap import dedent
import io

logger.remove(0)

class YAMLProcessorTest(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super(YAMLProcessorTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor(yaml.SafeLoader)

    def test_loading_files(self):
        self.assertRaises(FileNotFoundError, self.proc.load_file, "tests/assets/notafile")
        self.assertRaises(FileNotFoundError, self.proc.load_file, "tests/asset/config.yaml")
        self.assertRaises(yaml.YAMLError, self.proc.load_file, "tests/assets/invalid.yaml")
    
    def test_load_document(self):
        test_yaml = """
        key: ][
        """
        self.assertRaises(yaml.YAMLError, self.proc.load_document, test_yaml)

    
    def test_add_logger_stderr(self):
        test_yaml = """
        log_stderr:
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 1
        logger.remove()


    def test_add_logger_stderr_level_assign(self):
        test_yaml = """
        log_stderr:
            level: info
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 1
        assert self.proc.data['log_stderr']['level'] == 'info'
        logger.remove()

    def test_add_logger_stderr_invalid_level(self):
        test_yaml = """
        log_stderr:
            level: notalevel
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(AssertionError, self.proc.add_loggers)

    def test_add_logger_journal(self):
        test_yaml = """
        log_journal:
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 1
        logger.remove()


    def test_add_logger_journal_level_assign(self):
        test_yaml = """
        log_journal:
            level: info
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 1
        assert self.proc.data['log_journal']['level'] == 'info'
        logger.remove()

    def test_add_logger_journal_invalid_level(self):
        test_yaml = """
        log_journal:
            level: notalevel
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(AssertionError, self.proc.add_loggers)

    def test_add_logger_file(self):
        test_yaml = """
        log_file:
            path: /tmp/test_add_logger_file.log
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 1
        assert self.proc.data['log_file']['path'] == '/tmp/test_add_logger_file.log'
        logger.remove()

    def test_add_logger_file_level_assign(self):
        test_yaml = """
        log_file:
            path: /tmp/test_add_logger_file.log
            level: info
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 1
        assert self.proc.data['log_file']['level'] == 'info'
        assert self.proc.data['log_file']['path'] == '/tmp/test_add_logger_file.log'
        logger.remove()

    def test_add_logger_file_path_missing(self):
        test_yaml = """
        log_file:
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(AssertionError, self.proc.add_loggers)

    def test_add_logger_all(self):
        test_yaml = """
        log_stderr:
        log_journal:
        log_file:
            path: /tmp/test_add_logger_file.log
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 3
        assert self.proc.data['log_file']['path'] == '/tmp/test_add_logger_file.log'
        logger.remove()

    def test_get_tasks_not_defined(self):
        test_yaml = """
        key:
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(AssertionError, self.proc.get_tasks, CallbackDict())

    def test_get_tasks_not_dictionary(self):
        test_yaml = """
        tasks:
            - sometask
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(AssertionError, self.proc.get_tasks, CallbackDict())

    def test_get_tasks_missing_callbacks(self):
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
        self.assertRaises(AssertionError, self.proc.get_tasks, CallbackDict())

    def test_get_tasks_task_data_not_dictionary(self):
        test_yaml = """
        tasks:
            sometask:
                - type: watchfiles
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(AssertionError, self.proc.get_tasks, CallbackDict())

    def test_get_tasks_task_not_implemented(self):
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
        self.assertRaises(NotImplementedError, self.proc.get_tasks, callbacks)

    def test_get_tasks_task_syntax_error(self):
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: exit 0
        tasks:
            sometask:
                type: watchfiles
                changes:
                    - added
                    - modified
                    - deleted
                paths:
                    - /tmp/
                callbacks:
                    - callback0
        """
        try:
            self.proc.load_document(test_yaml)
            callbacks = self.proc.get_callbacks()
            self.proc.get_tasks(callbacks)
        except:
            pass # tbd

    def test_get_callbacks_not_defined(self):
        test_yaml = """
        key:
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(AssertionError, self.proc.get_callbacks)

    def test_get_callbacks_not_dictionary(self):
        test_yaml = """
        callbacks:
            - callback0
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(AssertionError, self.proc.get_callbacks)

    def test_get_callbacks_callback_data_not_dictionary(self):
        test_yaml = """
        callbacks:
            callback0:
                - type: watchfiles
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(AssertionError, self.proc.get_callbacks)

    def test_get_callbacks_callback_not_implemented(self):
        test_yaml = """
        callbacks:
            callback0:
                type: notimplemented
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(NotImplementedError, self.proc.get_callbacks)

    def test_get_callbacks_callback_syntax_error(self):
        test_yaml = """
        callbacks:
            callback0:
                type: logger
                level: notdefined
        """
        self.proc.load_document(test_yaml)
        self.assertRaises(CallbackSyntaxError, self.proc.get_callbacks)


if __name__ == '__main__':
    unittest.main(verbosity=2)