from __future__ import annotations

import json
import os
import sys
import time

from option import Err, Ok, Option, Result, Some
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from helpers.norm import norm
from variables.Config import Config

if sys.version_info >= (3, 11):
    from typing import TYPE_CHECKING
else:
    from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.remote.webelement import WebElement


exist = EC.presence_of_element_located


class Browser:
    def __init__(self) -> None:
        self.__creating_folders()

        options = webdriver.EdgeOptions()
        options.add_argument("log-level=3")  # type: ignore
        options.add_argument("start-minimized")  # type: ignore
        options.add_argument(f"user-data-dir={os.path.abspath(Config.USER_DATA_DIR)}")  # type: ignore
        options.add_experimental_option("excludeSwitches", ["enable-logging"])  # type: ignore

        self.__loading_extension(options)

        driver_path = EdgeChromiumDriverManager().install()
        print(f"Edge driver path: {driver_path}")
        self.driver = webdriver.Edge(service=EdgeService(driver_path), options=options)

        self.__loading_cookies()

    # region: helper functions

    def __creating_folders(self) -> None:
        if not os.path.exists(Config.EXTENSIONS_DIR):
            os.makedirs(Config.EXTENSIONS_DIR)
        if not os.path.exists(Config.COOKIES_DIR):
            os.makedirs(Config.COOKIES_DIR)
        if not os.path.exists(Config.USER_DATA_DIR):
            os.makedirs(Config.USER_DATA_DIR)

    def __loading_extension(self, options: Options) -> None:
        extensions = [
            os.path.join(Config.EXTENSIONS_DIR, ext)
            for ext in os.listdir(Config.EXTENSIONS_DIR)
            if os.path.isfile(os.path.join(Config.EXTENSIONS_DIR, ext)) and ext.endswith(".crx")
        ]
        for ext in extensions:
            options.add_extension(os.path.abspath(ext))

    def __loading_cookies(self) -> None:
        cookies_files = [
            f
            for f in os.listdir(Config.COOKIES_DIR)
            if os.path.isfile(os.path.join(Config.COOKIES_DIR, f)) and f.endswith(".json")
        ]

        for cookie_file in cookies_files:
            with open(os.path.join(Config.COOKIES_DIR, cookie_file), "r") as f:
                # Source: https://stackoverflow.com/a/63220249
                self.driver.execute_cdp_cmd("Network.enable", {})  # type: ignore
                for cookie in json.load(f):
                    self.driver.execute_cdp_cmd("Network.setCookie", cookie)  # type: ignore
                self.driver.execute_cdp_cmd("Network.disable", {})  # type: ignore

    # endregion

    def cookies_create(self, website: str, filename: str, css_presence: str = "") -> Result[None, str]:
        """Popup a browser window to login to the website and save the cookies to a file
        - website: to login to
        - filename: where to save the cookies
        - css_presence: css selector to check if the user is logged in, leave it empty to skip this check
        """

        website = "https://" + website if not website.startswith("https://") else website
        filename = norm(filename) + ".json" if not filename.endswith(".json") else norm(filename)

        self.driver.get(website)
        self.driver.maximize_window()
        input(f"Press enter after you logged in to {website}...")
        cookies = self.driver.get_cookies()  # type: ignore
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
        self.driver.minimize_window()

        self.driver.get(website)
        if css_presence == "":
            return Ok(None)

        try:
            WebDriverWait(self.driver, Config.WAIT_ELEM_TIMEOUT).until(exist((By.CSS_SELECTOR, css_presence)))  # type: ignore
            return Ok(None)
        except:
            return Err("Cannot find the css selector provided. Ignore this if it's logged in.")

    def get_inner_html(self, parent: WebElement | WebDriver, css_selector: str, timeout: float = 1) -> str:
        """Scrape a css selector until it's not empty, then return it
        This function panics on purpose if the element is not found after the timeout
        """
        WebDriverWait(self.driver, Config.WAIT_ELEM_TIMEOUT).until(exist((By.CSS_SELECTOR, css_selector)))  # type: ignore
        element: WebElement = parent.find_element(By.CSS_SELECTOR, css_selector)  # type: ignore
        content: str = element.get_attribute("innerHTML") or ""  # type: ignore
        start_time = time.time()
        while content == "":
            content = element.get_attribute("innerHTML") or ""  # type: ignore
            if time.time() - start_time > timeout:
                break
        return content

    def get_elem(
        self, parent: WebElement | WebDriver, css_selector: str, timeout: float = Config.WAIT_ELEM_TIMEOUT
    ) -> Option[WebElement]:
        """Wait + find an element"""
        WebDriverWait(parent, timeout).until(exist((By.CSS_SELECTOR, css_selector)))
        if (res := parent.find_element(By.CSS_SELECTOR, css_selector)) is not None:
            return Some(res)
        return Option.NONE()

    def get_elems(
        self, parent: WebElement | WebDriver, css_selector: str, timeout: float = Config.WAIT_ELEM_TIMEOUT
    ) -> list[WebElement]:
        """Wait + find elements"""
        WebDriverWait(parent, timeout).until(exist((By.CSS_SELECTOR, css_selector)))
        return parent.find_elements(By.CSS_SELECTOR, css_selector)
