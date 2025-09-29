from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def go_stop_usage_tab(drv, sec: int = 10):
    WebDriverWait(drv, sec).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "ul#ulListIndiSel li.title_tab"))
    )
    target = None
    for li in drv.find_elements(By.CSS_SELECTOR, "ul#ulListIndiSel li.title_tab"):
        if "정류장별 이용량" in li.text.strip():
            target = li; break
    if target is None: raise RuntimeError("탭 '정류장별 이용량' 미발견")
    drv.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
    drv.execute_script("arguments[0].click();", target)
    WebDriverWait(drv, sec).until(lambda d: "active" in target.get_attribute("class"))