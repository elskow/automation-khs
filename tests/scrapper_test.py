import unittest
from unittest.mock import MagicMock, patch

from scrapper import KHSScraper


class TestKHSScraper(unittest.TestCase):
    @patch("os.getenv")
    @patch("selenium.webdriver.Chrome")
    def setUp(self, mock_chrome, mock_getenv):
        mock_getenv.return_value = "test"
        self.scraper = KHSScraper()

    @patch.object(KHSScraper, "_KHSScraper__login")
    @patch.object(KHSScraper, "_KHSScraper__get_khs")
    @patch.object(KHSScraper, "_KHSScraper__quit")
    @patch("selenium.webdriver.Chrome")
    def test_run(self, mock_chrome, mock_quit, mock_get_khs, mock_login):
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        self.scraper.run()
        mock_login.assert_called_once()
        mock_get_khs.assert_called_once()
        mock_quit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
