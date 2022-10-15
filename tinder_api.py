import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException

from config import FACEBOOK_ID, FACEBOOK_PW


URL = "https://tinder.com/en"


class TinderAPI:
    def __init__(self, headless=False, interval=10):
        options = Options()
        options.headless = headless
        self.headless = headless
        self.interval = interval
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(interval)
        self.driver.execute_cdp_cmd(
            "Browser.grantPermissions",
            {"origin": "https://tinder.com", "permissions": ["geolocation"]},
        )
        self.driver.execute_cdp_cmd(
            "Emulation.setGeolocationOverride",
            {
                "latitude": 35.7,
                "longitude": 139.7,
                "accuracy": 100,
            },
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.save_screenshot("end.png")
        self.driver.quit()
        del self.driver

    def like(self):
        element = self.driver.find_element("xpath", '//span[text()="Like"]')
        while element.tag_name != "button":
            element = element.find_element("xpath", "..")
        element.click()
        time.sleep(3)

    def nope(self):
        element = self.driver.find_element("xpath", '//span[text()="Nope"]')
        while element.tag_name != "button":
            element = element.find_element("xpath", "..")
        element.click()
        time.sleep(3)

    def random_swipe(self, p=0.8):
        if random.random() < p:
            self.like()
        else:
            self.nope()

    def login(self):
        self.driver.get(URL)
        self.driver.set_window_size(1200, 900)
        time.sleep(30)
        self.driver.find_element(
            "xpath", "/html/body/div[1]/div/div[2]/div/div/div[1]/button"
        ).click()
        time.sleep(2)
        self.driver.find_element(
            "xpath", '//a[@href="https://tinder.onelink.me/9K8a/3d4abb81"]'
        ).click()
        time.sleep(2)
        self.driver.find_element(
            "xpath", "/html/body/div[2]/div/div/div[1]/div/div[3]/span/div[2]/button"
        ).click()
        time.sleep(2)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.find_element("id", "email").send_keys(FACEBOOK_ID)
        self.driver.find_element("id", "pass").send_keys(FACEBOOK_PW)
        self.driver.find_element("name", "login").click()
        time.sleep(10)
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def swipe(self):
        self.login()
        print("login")
        reach = False
        for i in range(10):
            self.driver.save_screenshot(str(i) + ".png")
            try:
                self.random_swipe()
                reach = False
                print("swipe")
            except Exception as e:
                print(e)
                print("ad occur")
                if reach:
                    print("out")
                    break
                try:
                    element = self.driver.find_element(
                        "xpath",
                        '//span[contains(text(), "Later")'
                        + ' or text()="No Thanks"'
                        + ' or contains(text(), "Skip")]',
                    )
                    while element.tag_name != "button":
                        element = element.find_element("xpath", "..")
                    element.click()
                except:
                    print("error")
                    time.sleep(30)
                    raise
                time.sleep(3)
                self.random_swipe()
                print("swipe")
                reach = True


if __name__ == "__main__":
    with TinderAPI() as t:
        t.swipe()
