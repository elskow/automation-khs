import json
import os
from contextlib import contextmanager

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

# Load environment variables
load_dotenv()


class KHSScraper:
    def __init__(self, verbose=False):
        """Initializes the scraper."""
        self.__verbose = verbose
        self.__driver = None
        self.__email = os.getenv("EMAIL")
        self.__password = os.getenv("PASSWORD")
        if not self.__email or not self.__password:
            raise ValueError("EMAIL and PASSWORD must be set in the environment.")
        self.__sso_login_url = "https://sso.unesa.ac.id/login"
        self.__sso_dashboard_url = "https://sso.unesa.ac.id/dashboard"
        self.__dataKHS = {}

    def __load_config(self):
        """Loads configuration from a JSON file."""
        with open("config.json") as f:
            return json.load(f)

    @contextmanager
    def __init_driver(self):
        """Initializes the webdriver."""
        config = self.__load_config()
        options = webdriver.ChromeOptions()
        for option in config["options"]:
            options.add_argument(option)
        options.add_experimental_option("prefs", config["prefs"])
        driver = webdriver.Chrome(options=options)
        if self.__verbose:
            print("Driver initialized!")
        yield driver
        driver.quit()

    def __login(self):
        """Performs login and navigation operations."""
        self.__login_to_sso()
        self.__navigate_to_siakadu()
        self.__navigate_to_khs()

    def run(self):
        """Starts the scraper."""
        with self.__init_driver() as driver:
            self.__driver = driver
            self.__login()
            self.__get_khs()
            self.__quit()
            return self.__dataKHS

    def __login_to_sso(self):
        """Logs in to SSO."""
        self.__driver.get(self.__sso_login_url)
        WebDriverWait(self.__driver, 30).until(
            ec.presence_of_element_located((By.ID, "identifierId"))
        ).send_keys(self.__email)
        self.__driver.find_element(By.ID, "identifierNext").click()
        WebDriverWait(self.__driver, 30).until(
            ec.presence_of_element_located((By.NAME, "Passwd"))
        ).send_keys(self.__password)
        self.__driver.find_element(By.ID, "passwordNext").click()
        if self.__verbose:
            print("Login success!")
        WebDriverWait(self.__driver, 30).until(ec.url_to_be(self.__sso_dashboard_url))
        if self.__verbose:
            print("Redirected to dashboard!")

    def __navigate_to_siakadu(self):
        """Navigates to Siakadu."""
        siakadu_url = self.__driver.find_element(
            By.CSS_SELECTOR, "a[href^='https://siakadu.unesa.ac.id/sso']"
        ).get_attribute("href")
        self.__driver.get(siakadu_url)
        if self.__verbose:
            print("Redirected to siakadu!")
        WebDriverWait(self.__driver, 30).until(
            ec.url_to_be("https://sindig.unesa.ac.id/?home=1")
        )

    def __navigate_to_khs(self):
        """Navigates to KHS."""
        khs_url = self.__driver.find_element(
            By.XPATH, "//span[text()='KHS']/parent::a"
        ).get_attribute("href")
        self.__driver.get(khs_url)
        if self.__verbose:
            print("Redirected to khs!")

    def __get_khs(self):
        """Gets the KHS data."""
        for _ in range(5):
            try:
                WebDriverWait(self.__driver, 30).until(
                    ec.presence_of_element_located((By.CLASS_NAME, "table-responsive"))
                )
                break
            except:
                self.__driver.refresh()
                if self.__verbose:
                    print("Waiting for element to load...")
        else:
            raise Exception("Data not loaded after 5 retries!")
        self.__dataKHS = self.__driver.execute_script("return this.DTKHS")

    def __quit(self):
        """Quits the driver."""
        self.__driver.quit()


if __name__ == "__main__":
    scraper = KHSScraper()
    data = scraper.run()
    print(data)
