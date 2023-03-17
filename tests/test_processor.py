from yasmon import YAMLProcessor
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
    
    def test_add_logger_stderr(self):
        test_yaml = """
        log_stderr:
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 1
        logger.remove()


        test_yaml = """
        log_stderr:
            level: info
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 1
        assert self.proc.data['log_stderr']['level'] == 'info'
        logger.remove()

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


        test_yaml = """
        log_journal:
            level: info
        """
        self.proc.load_document(test_yaml)
        assert self.proc.add_loggers() == 1
        assert self.proc.data['log_journal']['level'] == 'info'
        logger.remove()

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

if __name__ == '__main__':
    unittest.main(verbosity=2)