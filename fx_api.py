from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from config import FX_ID, FX_PW

URL = 'https://tradefx.gaitame.com/pcweb/gneo/login.html'


class FX:
    def __init__(self, headless=True, interval=10):
        options = Options()
        options.headless = headless
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(interval)
        self.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()
        del self.driver

    def start(self):
        # Open Gaitame URL
        self.driver.get(URL)
        # Login
        self.driver.find_element_by_id('id').send_keys(FX_ID)
        self.driver.find_element_by_id('pw').send_keys(FX_PW)
        self.driver.find_element_by_id('login_btn').click()
        # Delete alert
        try:
            alert = self.driver.find_element_by_id('login_complete_alert')
            alert.find_element_by_xpath('.//input[@value="0"]').click()
            alert.find_element_by_id('button-ok').click()
        except NoSuchElementException:
            pass

    def quit(self):
        self.driver.quit()

    def ask(self, country: int = 0, count: int = 0):
        self.driver.find_element_by_id('gm2').click()
        neworder = self.driver.find_element_by_id('content_neworder')
        neworder.find_element_by_xpath('.//input[@value="S"]').click()
        print('OK')


if __name__ == '__main__':
    main()
