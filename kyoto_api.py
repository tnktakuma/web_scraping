import datetime
from typing import List, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert

from config import KYOTO_ID, KYOTO_PW


URL = 'https://g-kyoto.pref.kyoto.lg.jp/reserve_j/core_i/init.asp?SBT=1'


class KyotoTennis:
    def __init__(self, headless=True, interval=10):
        options = Options()
        options.headless = headless
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(interval)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()
        del self.driver

    def start(self, place: int, date: datetime.datetime):
        # Open Kyoto Yoyaku URL
        self.driver.get(URL)
        # Switch Frame
        self.driver.switch_to.frame('MainFrame')
        self.driver.find_element_by_xpath(
            '//input[@src="../image/shisetu_kensaku.gif"]').click()
        # Search place
        if place == 0:
            place_name = '西院'
        elif place == 1:
            place_name = '岡崎'
        elif place == 2:
            place_name = '宝が池'
        else:
            raise ValueError('place is 0 or 1 or 2')
        self.driver.find_element_by_name('txt_keyword').send_keys(place_name)
        self.driver.find_element_by_name('btn_shortcut').click()
        self.driver.find_element_by_xpath(
            '//input[@src="../image/yoyaku_s.jpg"]').click()
        # Change Date
        ymd = date.strftime('%Y%m%d')
        this_month = datetime.date.today().month
        if (datetime.date.today().month + 1) % 12 == date.month % 12:
            self.driver.find_element_by_xpath('//img[@alt="翌月表示"]').click()
        self.driver.find_element_by_xpath(
            f'//a[@href="javascript:set_data({ymd})"]').click()

    def quit(self):
        self.driver.quit()

    def login(self):
        self.driver.find_element_by_name('txt_usr_cd').send_keys(KYOTO_ID)
        self.driver.find_element_by_name('txt_pass').send_keys(KYOTO_PW)
        self.driver.find_element_by_name('btn_ok').click()

    def get_avail(self, place: int, date: datetime.datetime) -> List[Tuple[Tuple[int, int], bool]]:
        """Get whether the place is vacancy on the date.

        Args:
            place (int): 0: saiin, 1: okazaki, 2: takaragaike
            date (datetime.datetime): the required date

        Retruns:
            List[Tuple[Tuple[int, int], bool]]: availability list.
                the first element of Tuple in the List is Tuple,
                whose first is start time and second is stop time.
                the second one is bool which shows availability.
        """
        self.start(place, date)
        rows = self.driver.find_elements_by_class_name('clsShisetuTitleOneDay')
        for row in rows:
            if row.text == 'テニスコート':
                tennis = row.find_element_by_xpath('..')
                break
        komas = tennis.find_elements_by_class_name('clsKoma')
        t = 8
        avail_list = []
        for koma in komas:
            dt = int(koma.get_attribute('colspan')) // 4
            avail = koma.find_element_by_tag_name('img').get_attribute('alt')
            if '予約可能' in avail:
                avail_list.append(((t, t + dt), True))
            elif '予約不可' in avail:
                avail_list.append(((t, t + dt), False))
            else:
                raise RuntimeError('error')
            t += dt
        return avail_list

    def reserve(self, place: int, date: datetime.datetime):
        """Get whether the place is vacancy on the date.

        Args:
            place (int): 0: saiin, 1: okazaki, 2: takaragaike
            date (datetime.datetime): the required date
        """
        self.start(place, date)
        rows = self.driver.find_elements_by_class_name('clsShisetuTitleOneDay')
        for row in rows:
            if row.text == 'テニスコート':
                tennis = row.find_element_by_xpath('..')
                break
        t = 8
        for koma in tennis.find_elements_by_class_name('clsKoma'):
            t += int(koma.get_attribute('colspan')) // 4
            if date.hour < t:
                avail = koma.find_element_by_tag_name('img')
                break
        if avail.get_attribute('alt') != '予約可能':
            raise ValueError('Not Available at this time')
        avail.click()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        for c in self.driver.find_elements_by_class_name('clsKomaLarge'):
            if '予約可能' in c.get_attribute('alt'):
                c.click()
                break
        self.driver.find_element_by_name('btn_close').click()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.switch_to.frame('MainFrame')
        self.driver.find_element_by_name('btn_ok').click()
        self.login()
        self.driver.find_element_by_name('btn_next').click()
        self.driver.find_element_by_name('btn_toroku').click()
        self.driver.find_element_by_name('btn_cmd').click()
        Alert(self.driver).accept()
        self.quit()
