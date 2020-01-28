import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import FX_ID, FX_PW

URL = 'https://tradefx.gaitame.com/pcweb/gneo/login.html'


def main():
    # Open Chrome Driver
    options = Options()
    options.headless = True
    with webdriver.Chrome(options=options) as driver:
        # Open Gaitame URL
        driver.get(URL)
        time.sleep(10)
        # Move to NextNeo
        driver.find_element_by_id('id').send_keys(FX_ID)
        driver.find_element_by_id('pw').send_keys(FX_PW)
        driver.find_element_by_id('login_btn').click()
        time.sleep(10)
        # Change to Order
        alert = driver.find_element_by_id('login_complete_alert')
        alert.find_element_by_xpath('.//input[@value="0"]').click()
        alert.find_element_by_id('button-ok').click()
        time.sleep(3)
        driver.find_element_by_id('gm2').click()
        time.sleep(3)
        neworder = driver.find_element_by_id('content_neworder')
        neworder.find_element_by_xpath('.//input[@value="S"]').click()
        time.sleep(3)
        print('OK')


if __name__ == '__main__':
    main()
