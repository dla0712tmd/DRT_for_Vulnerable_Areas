# stcis_driver.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

IC0307_URL = "https://stcis.go.kr/pivotIndi/wpsPivotIndicator.do?siteGb=P&indiClss=IC03&indiSel=IC0307"

def make_driver(headless: bool = True, download_dir: str | None = None) -> webdriver.Chrome:
    o = Options()
    if headless: o.add_argument("--headless=new")
    o.add_argument("--window-size=1600,1000")
    o.add_argument("--no-sandbox"); o.add_argument("--disable-dev-shm-usage")
    if download_dir:
        os.makedirs(download_dir, exist_ok=True)
        prefs = {
            "download.default_directory": os.path.abspath(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,
        }
        o.add_experimental_option("prefs", prefs)
    drv = webdriver.Chrome(options=o)
    # CDP로 headless에서도 다운로드 허용 보강
    try:
        drv.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": os.path.abspath(download_dir or os.getcwd())
        })
    except Exception:
        pass
    return drv

def wait_css(drv, css: str, sec: int = 15):
    return WebDriverWait(drv, sec).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))

def open_ic0307(drv):
    drv.get(IC0307_URL)
    wait_css(drv, "ul#ulListIndiSel li.title_tab")