from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from dotenv import load_dotenv
import os
from pprint import pprint
import time
import json

load_dotenv()


class KHSScraper:
    def __init__(self, verbose=False):
        """Initializes the scraper."""
        self.verbose = verbose
        self._driver = self._init_driver()
        self._email = os.getenv("EMAIL")
        self._password = os.getenv("PASSWORD")
        self._sso_login_url = "https://sso.unesa.ac.id/login"
        self._sso_dashboard_url = "https://sso.unesa.ac.id/dashboard"
        self._dataKHS = {}

    def _init_driver(self):
        """
        Initializes the webdriver.
        """
        with open("config.json") as f:
            config = json.load(f)

        options = webdriver.ChromeOptions()
        for option in config["options"]:
            options.add_argument(option)

        options.add_experimental_option("prefs", config["prefs"])

        driver = webdriver.Chrome(options=options)
        if self.verbose:
            print("Driver initialized!")
        return driver

    def _login_to_sso(self):
        """Logs in to SSO."""
        self._driver.get(self._sso_login_url)

        WebDriverWait(self._driver, 30).until(
            ec.presence_of_element_located((By.ID, "identifierId"))
        ).send_keys(self._email)
        self._driver.find_element(By.ID, "identifierNext").click()
        WebDriverWait(self._driver, 30).until(
            ec.presence_of_element_located((By.NAME, "Passwd"))
        ).send_keys(self._password)
        self._driver.find_element(By.ID, "passwordNext").click()
        if self.verbose:
            print("Login success!")

        WebDriverWait(self._driver, 30).until(ec.url_to_be(self._sso_dashboard_url))
        if self.verbose:
            print("Redirected to dashboard!")

    def _navigate_to_siakadu(self):
        """Navigates to Siakadu."""
        siakadu_url = self._driver.find_element(
            By.CSS_SELECTOR, "a[href^='https://siakadu.unesa.ac.id/sso']"
        ).get_attribute("href")
        self._driver.get(siakadu_url)
        if self.verbose:
            print("Redirected to siakadu!")
        WebDriverWait(self._driver, 30).until(
            ec.url_to_be("https://sindig.unesa.ac.id/?home=1")
        )

    def _navigate_to_khs(self):
        """Navigates to KHS."""
        khs_url = self._driver.find_element(
            By.XPATH, "//span[text()='KHS']/parent::a"
        ).get_attribute("href")
        self._driver.get(khs_url)
        if self.verbose:
            print("Redirected to khs!")

    def _get_khs(self):
        """Gets the KHS data."""
        for _ in range(5):
            try:
                WebDriverWait(self._driver, 30).until(
                    ec.presence_of_element_located((By.CLASS_NAME, "table-responsive"))
                )
                break
            except:
                self._driver.refresh()
                if self.verbose:
                    print("Waiting for element to load...")
        else:
            raise Exception("Data not loaded after 5 retries!")

        data_khs = self._driver.execute_script("return this.DTKHS")
        self._dataKHS = data_khs

    def get_khs_semester(self, semester):
        """Gets the KHS data for a specific semester."""
        semester = str(semester)
        if self._dataKHS == {}:
            raise Exception("You haven't scraped this semester yet!")
        return self._dataKHS[semester]["data"]

    def quit(self):
        """Quits the driver."""
        self._driver.quit()

    def start(self):
        """Starts the scraper."""
        self._login_to_sso()
        self._navigate_to_siakadu()
        self._navigate_to_khs()
        self._get_khs()


if __name__ == "__main__":
    start = time.time()
    scraper = KHSScraper()
    scraper.start()
    pprint(scraper.get_khs_semester(3))
    scraper.quit()
    print(f"Finished in {time.time() - start} seconds")
