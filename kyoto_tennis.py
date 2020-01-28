import time
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from twitter_api import Twitter

URL = 'https://g-kyoto.pref.kyoto.lg.jp/reserve_j/core_i/init.asp?SBT=1'


def get_text():
    # Date
    today = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    tomorrow = today + datetime.timedelta(days=1)
    tmr = tomorrow.strftime('%Y%m%d')
    text = tomorrow.strftime('%Y年%m月%d日(%a)の空き情報') + '\n'
    # Term
    term = [8, 10, 12, 14, 16, 18, 21]
    # Special for saiin
    is_saiin = '0'
    # Open Chrome Driver
    for place in ['西院公園', '岡崎公園', '宝が池公園']:
        text += '\n' + place + '\n'
        options = Options()
        options.headless = True
        with webdriver.Chrome(options=options) as driver:
            # Open Kyoto Yoyaku URL
            driver.get(URL)
            time.sleep(1)
            # Switch Frame
            driver.switch_to.frame('MainFrame')
            time.sleep(1)
            # Move to Shisetu_Kensaku
            driver.find_element_by_xpath('//input[@src="../image/shisetu_kensaku.gif"]').click()
            time.sleep(3)
            # Search Saiin
            driver.find_element_by_name('txt_keyword').send_keys(place)
            time.sleep(3)
            driver.find_element_by_name('btn_shortcut').click()
            time.sleep(3)
            driver.find_element_by_xpath('//input[@src="../image/yoyaku_s.jpg"]').click()
            time.sleep(10)
            # Change Date
            driver.find_element_by_xpath(f'//a[@href="javascript:set_data({tmr})"]').click()
            time.sleep(10)
            # Print Yes or No
            for i in range(len(term)-1):
                img = f'image00000{i}00' + is_saiin
                avail = driver.find_element_by_name(img).get_attribute('alt')
                if avail == '予約可能':
                    text += f'{term[i]}-{term[i+1]} '
                elif avail == '予約不可':
                    text += 'X '
                else:
                    text += avail + ' Error '
            text += '\n'
        is_saiin = '1'
    return text


def main():
    Twitter().post_tweet(get_text())
    print('Tweeted')


if __name__ == '__main__':
    main()
