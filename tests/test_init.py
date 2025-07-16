import unittest
from unittest.mock import MagicMock, patch


class TestInit(unittest.TestCase):
    @patch("subprocess.run")
    @patch("sys.exit")
    def test_main_success(self, mock_sys_exit, mock_subprocess_run):
        """Test the main function in __init__.py - success case."""
        from httpcheck import main

        # Mock the subprocess call
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        # Call the main function
        main()

        # Assert that subprocess.run was called with the correct arguments
        mock_subprocess_run.assert_called_once()
        self.assertIn("httpcheck.py", mock_subprocess_run.call_args[0][0][1])

        # Assert that sys.exit was called with the correct return code
        mock_sys_exit.assert_called_once_with(0)

    @patch("subprocess.run")
    @patch("sys.exit")
    @patch("os.path.exists", return_value=False)
    def test_main_script_not_found(
        self, mock_os_path_exists, mock_sys_exit, mock_subprocess_run
    ):
        """Test the main function in __init__.py - script not found case."""
        from httpcheck import main

        # Call the main function
        main()

        # Assert that subprocess.run was not called
        mock_subprocess_run.assert_not_called()

        # Assert that sys.exit was called with the correct return code
        mock_sys_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
