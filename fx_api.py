from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
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

    def get_rate(self, offer: str, country: str = 'usdjpy') -> float:
        self.driver.find_element_by_id('gm1').click()
        panel = self.driver.find_element_by_id(
            'uforex1_id_rate_panel_' + country.lower())
        rate = panel.find_element_by_xpath(f'.//*[text()="{offer}"]')
        value = rate.find_elements_by_xpath('..//span')
        return float(value[0].text + value[1].text + value[2].text)

    def get_ask_rate(self, country: str = 'usdjpy') -> float:
        return self.get_rate('ASK', country)

    def get_bid_rate(self, country: str = 'usdjpy') -> float:
        return self.get_rate('BID', country)

    def order(self, offer: str, country: str = 'USDJPY', lot: int = 1):
        # prepare
        self.driver.find_element_by_id('gm2').click()
        neworder = self.driver.find_element_by_id('content_neworder')
        neworder.find_element_by_id('order_tab2').click()
        # country
        Select(neworder.find_element_by_xpath(
            './/select[@name="com_list"]')).select_by_value(country.upper())
        # no straddling
        neworder.find_element_by_xpath('.//input[@value="0"]').click()
        # lot
        order_count = neworder.find_element_by_xpath(
            './/input[@name="orderCount"]')
        order_count.clear()
        order_count.send_keys(str(lot))
        # ask or bid
        neworder.find_element_by_xpath(f'.//input[@value="{offer}"]').click()
        # only market
        Select(neworder.find_element_by_xpath(
            './/select[@name="oexc_list"]')).select_by_value('00')
        # ignore attention
        confirm = neworder.find_element_by_xpath(
            './/input[@name="confirmChk"]')
        if confirm.is_selected():
            confirm.click()
        # order
        neworder.find_element_by_xpath('.//input[@name="confirmBtn"]').click()

    def order_ask(self, country: str = 'USDJPY', lot: int = 1):
        self.order('B', country, lot)

    def order_bid(self, country: str = 'USDJPY', lot: int = 1):
        self.order('S', country, lot)


if __name__ == '__main__':
    main()
