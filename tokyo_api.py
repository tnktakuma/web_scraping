import datetime
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://kouen.sports.metro.tokyo.lg.jp/web/index.jsp"

# 種目: テニス（人工芝）の value
PURPOSE_TENNIS_ARTIFICIAL = "1000_1030"


# 何週先まで確認するか（今週 + 3 = 計4週）
WEEKS_AHEAD = 4


class TokyoTennisArtificial:
    """東京都立公園スポーツ予約システムでテニス（人工芝）の空き状況を確認するクラス。

    利用日を今日、種目をテニス（人工芝）に固定し、
    各公園について最大4並列で検索して今から4週間分（土日祝のみ）の空き時間帯を取得する。
    """

    def __init__(
        self,
        headless: bool = True,
        interval: int = 10,
        chromedriver_port: Optional[int] = None,
    ):
        self.headless = headless
        self.interval = interval
        self.chromedriver_port = (
            chromedriver_port
            if chromedriver_port is not None
            else int(os.getenv("CHROMEDRIVER_PORT", "9515"))
        )
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        chrome_binary = os.getenv("CHROME_BINARY_PATH")
        if chrome_binary:
            options.binary_location = chrome_binary
        for arg in [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-dev-tools",
            "--no-zygote",
            "--remote-debugging-pipe",
            "--window-size=1280,1696",
            "--lang=ja",
        ]:
            options.add_argument(arg)
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
        service = Service(
            executable_path=chromedriver_path,
            port=self.chromedriver_port,
        )
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(interval)
        self._first_search = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()

    def quit(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    def _js_click(self, element):
        """JavaScriptを使ってクリック（要素が隠れている場合に対応）"""
        self.driver.execute_script("arguments[0].click();", element)

    def _wait_for_id(self, element_id: str):
        return WebDriverWait(self.driver, self.interval).until(
            EC.presence_of_element_located((By.ID, element_id))
        )

    def _setup_common_conditions(self):
        """共通検索条件を設定する。

        - いつ: 今日（daystart に今日の日付を設定）
        - 種目: テニス（人工芝）を purpose-home / purpose に設定
        - bname-home の選択肢が更新されるまで待機

        この処理はトップページで一度だけ実行する。
        """
        self.driver.get(URL)
        self._wait_for_id("purpose-home")
        self._wait_for_id("bname-home")
        self._wait_for_id("purpose")
        self._wait_for_id("daystart-home")
        self._wait_for_id("daystart")

        # 種目: テニス（人工芝）を purpose-home にセットして change イベント発火
        # （purpose-home のイベントが bname-home の選択肢更新をトリガーする）
        self.driver.execute_script(
            """
            document.getElementById('purpose-home').value = arguments[0];
            $('#purpose-home').trigger('change');
            """,
            PURPOSE_TENNIS_ARTIFICIAL,
        )
        # bname-home の選択肢が Ajax で更新されるまで待機
        WebDriverWait(self.driver, self.interval).until(
            lambda driver: driver.execute_script(
                "return document.getElementById('bname-home').options.length"
            )
            > 1
        )

        # 種目: purpose（検索フォーム側）も設定
        self.driver.execute_script(
            "document.getElementById('purpose').value = arguments[0];",
            PURPOSE_TENNIS_ARTIFICIAL,
        )

        # 利用日: 今日
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.driver.execute_script(
            """
            document.getElementById('daystart-home').value = arguments[0];
            document.getElementById('daystart').value = arguments[0];
            """,
            today,
        )

    def _get_bname_options(self) -> List[Dict[str, str]]:
        """bname-home の選択肢（公園一覧）を返す。「選択してください」は除く。

        Returns:
            List[Dict[str, str]]: {"value": bcd, "text": 公園名} のリスト
        """
        opts = self.driver.execute_script(
            """
            var sel = document.getElementById('bname-home');
            return Array.from(sel.options)
                .filter(o => o.value !== '0')
                .map(o => ({value: o.value, text: o.textContent.trim()}));
            """
        )
        return opts

    def _search_by_park(self, bcd: str):
        """指定した公園（bcd）で検索を実行する（今週の先頭週を表示）。

        初回はトップページから btn-go で検索し、
        2回目以降は結果ページの bname セレクトを変更して btn-search1 で再検索する。

        Args:
            bcd (str): bname select の value（公園コード）
        """
        if self._first_search:
            # トップページ: bname-home と bname の両方をセット
            self.driver.execute_script(
                """
                document.getElementById('bname-home').value = arguments[0];
                document.getElementById('bname').value = arguments[0];
                document.getElementById('purpose-home').value = arguments[1];
                document.getElementById('purpose').value = arguments[1];
                """,
                bcd,
                PURPOSE_TENNIS_ARTIFICIAL,
            )
            time.sleep(0.5)
            self.driver.execute_script("document.getElementById('btn-go').click();")
            self._first_search = False
        else:
            # 結果ページ: bname と purpose をセットして再検索
            self.driver.execute_script(
                """
                document.getElementById('bname').value = arguments[0];
                document.getElementById('purpose').value = arguments[1];
                """,
                bcd,
                PURPOSE_TENNIS_ARTIFICIAL,
            )
            time.sleep(0.5)
            self.driver.execute_script(
                "document.getElementById('btn-search1').click();"
            )
        time.sleep(5)

    def _advance_week(self):
        """結果ページで翌週ボタンをクリックして次の週へ進む。"""
        self.driver.execute_script("document.getElementById('next-week').click();")
        time.sleep(4)

    def _parse_result_page(self) -> List[str]:
        """検索結果ページから土日祝の空き情報テキストを取得する。

        空きセルは td.available として描画される。
        ヘッダーの th.class に 'saturday' または 'holiday' が含まれる列のみを対象とする。

        Returns:
            List[str]: 空き情報の文字列リスト（例: "21土 ９時"）
        """
        avail_list = []
        try:
            table = self.driver.find_element(By.ID, "week-info")

            # ヘッダー行から日付テキストと土日祝フラグを取得（0番目は「時間帯」なのでスキップ）
            header_cells = table.find_elements(By.XPATH, ".//thead/tr/th")
            date_info = []
            for th in header_cells[1:]:
                cls = th.get_attribute("class") or ""
                is_holiday = "saturday" in cls or "holiday" in cls
                date_info.append((th.text.replace("\n", "").strip(), is_holiday))

            # tbody の各行を処理（土日祝列のみ）
            rows = table.find_elements(By.XPATH, ".//tbody/tr")
            for row in rows:
                time_label = row.find_element(By.TAG_NAME, "th").text.strip()
                cells = row.find_elements(By.TAG_NAME, "td")
                for i, cell in enumerate(cells):
                    if i >= len(date_info):
                        break
                    date_text, is_holiday = date_info[i]
                    if not is_holiday:
                        continue
                    cell_class = cell.get_attribute("class") or ""
                    if "available" in cell_class:
                        avail_list.append(f"{date_text} {time_label}".strip())
        except Exception:
            pass
        return avail_list

    def _get_avail_for_parks(
        self,
        parks: List[Dict[str, str]],
        setup_conditions: bool = True,
    ) -> Dict[str, List[str]]:
        """指定された公園リストについて空き情報を取得する。"""
        if setup_conditions:
            self._setup_common_conditions()
        results: Dict[str, List[str]] = {}

        for park in parks:
            bcd = park["value"]
            park_name = park["text"]

            # 先頭週を検索
            self._search_by_park(bcd)

            avail: List[str] = []
            for week in range(WEEKS_AHEAD):
                avail.extend(self._parse_result_page())
                if week < WEEKS_AHEAD - 1:
                    self._advance_week()

            results[park_name] = avail

        return results

    def _chunk_parks(
        self, parks: List[Dict[str, str]], workers: int
    ) -> List[List[Dict[str, str]]]:
        chunks: List[List[Dict[str, str]]] = [[] for _ in range(workers)]
        for i, park in enumerate(parks):
            chunks[i % workers].append(park)
        return [chunk for chunk in chunks if chunk]

    def get_avail_all_parks(self, parallel_workers: int = 4) -> Dict[str, List[str]]:
        """全公園についてテニス（人工芝）の空き情報を取得する。

        利用日=今日、種目=テニス（人工芝）で共通条件を設定し、
        各公園を最大 parallel_workers 並列で検索する。
        各公園について今週から WEEKS_AHEAD 週分（土日祝のみ）の空き時間帯を収集する。

        Returns:
            Dict[str, List[str]]: 公園名 -> 空き情報テキストのリスト
        """
        self._setup_common_conditions()
        parks = self._get_bname_options()

        if parallel_workers <= 1 or len(parks) <= 1:
            all_results = self._get_avail_for_parks(parks, setup_conditions=False)
        else:
            self.quit()
            workers = min(parallel_workers, len(parks))
            chunks = self._chunk_parks(parks, workers)
            chunk_results: Dict[str, List[str]] = {}

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {}
                for i, chunk in enumerate(chunks):
                    port = self.chromedriver_port + i
                    future = executor.submit(
                        self._fetch_park_chunk,
                        chunk,
                        self.headless,
                        self.interval,
                        port,
                    )
                    futures[future] = chunk

                for future in as_completed(futures):
                    chunk_results.update(future.result())

            all_results = {
                park["text"]: chunk_results.get(park["text"], []) for park in parks
            }

        for park in parks:
            park_name = park["text"]
            avail = all_results.get(park_name, [])

            if avail:
                print(f"[{park_name}] {len(avail)}件の空き")
                for a in avail:
                    print(f"  {a}")
            else:
                print(f"[{park_name}] 空きなし")

        return {park: avail for park, avail in all_results.items() if avail}

    @staticmethod
    def _fetch_park_chunk(
        parks: List[Dict[str, str]],
        headless: bool,
        interval: int,
        chromedriver_port: int,
    ) -> Dict[str, List[str]]:
        with TokyoTennisArtificial(
            headless=headless,
            interval=interval,
            chromedriver_port=chromedriver_port,
        ) as api:
            return api._get_avail_for_parks(parks)


def main():
    today_str = datetime.date.today().strftime("%Y年%m月%d日")
    print(f"=== {today_str} 今後4週間（土日祝）のテニス（人工芝）空き状況 ===\n")

    with TokyoTennisArtificial(headless=True) as api:
        results = api.get_avail_all_parks()

    print("\n=== 検索完了 ===")
    print(f"空きあり公園数: {len(results)}")
    print(results)
    return results


if __name__ == "__main__":
    main()
