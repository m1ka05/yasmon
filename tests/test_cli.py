from yasmon import cli
from loguru import logger

import unittest
from unittest import mock


class CLITest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(CLITest, self).__init__(*args, **kwargs)

    def test_parse_args_value_assignment(self):
        """
        Test cli.parse_args() for assignment of options.
        """

        config_file = 'tests/assets/cli/config.yaml'
        args = cli.parse_args('--config', config_file)
        assert args.config == config_file

    def test_execute_ExitCode_Success(self):
        """
        Test if cli.execute() returns ExitCodes.Success

        This exit code is returned in the case that no errors occured
        during operation.
        """

        default_logger_id = cli.setup_default_logger()
        args = cli.parse_args('--config', 'tests/assets/config.yaml')
        code = cli.execute(args, default_logger_id)
        assert code == cli.ExitCodes.Success
        logger.remove()

    def test_execute_ExitCode_FileNotFoundError(self):
        """
        Test if cli.execute() returns ExitCodes.FileNotFoundError

        This exit code should be returned if the path to the config file
        does not exist.
        """

        default_logger_id = cli.setup_default_logger()
        args = cli.parse_args('--config', 'invalid/path/to/config')
        code = cli.execute(args, default_logger_id)
        assert code == cli.ExitCodes.FileNotFoundError
        logger.remove()

    def test_execute_ExitCode_YAMLSyntaxError(self):
        """
        Test if cli.execute() returns ExitCodes.YAMLSyntaxError

        This exit code should be returned if the config syntax
        is invalid. This includes typical YAML Syntax errors as well as
        Yasmon specific syntax errors like missing callbacks and tasks.
        """

        default_logger_id = cli.setup_default_logger()
        args = cli.parse_args('--config', 'tests/assets/invalid.yaml')
        code = cli.execute(args, default_logger_id)
        assert code == cli.ExitCodes.YAMLSyntaxError
        logger.remove()

    def test_execute_catches_exceptions(self):
        """
        Test if cli.execute() catches all necessary exceptions.

        This only tests if all appropriate ExitCodes are returned.
        Actual rasing of exceptions is tested elsewhere.
        """

        # cli.ExitCodes.CallbackSyntaxError
        default_logger_id = cli.setup_default_logger()
        args = cli.parse_args(
            '--config',
            'tests/assets/CallbackSyntaxError.yaml')
        code = cli.execute(args, default_logger_id)
        assert code == cli.ExitCodes.CallbackSyntaxError
        logger.remove()

        # cli.ExitCodes.TaskError
        default_logger_id = cli.setup_default_logger()
        args = cli.parse_args(
            '--config',
            'tests/assets/TaskError.yaml')
        code = cli.execute(args, default_logger_id)
        assert code == cli.ExitCodes.TaskError
        logger.remove()

        # cli.ExitCodes.LoggerSyntaxError
        default_logger_id = cli.setup_default_logger()
        args = cli.parse_args(
            '--config',
            'tests/assets/LoggerSyntaxError.yaml')
        code = cli.execute(args, default_logger_id)
        assert code == cli.ExitCodes.LoggerSyntaxError
        logger.remove()

        # cli.ExitCodes.UnexpectedException
        with mock.patch('yasmon.processor.YAMLProcessor.__init__') as mck:
            mck.side_effect = Exception
            default_logger_id = cli.setup_default_logger()
            args = cli.parse_args(
                '--config',
                'tests/assets/config.yaml')
            code = cli.execute(args, default_logger_id)
            assert code == cli.ExitCodes.UnexpectedException
            logger.remove()


if __name__ == '__main__':
    unittest.main(verbosity=2)
