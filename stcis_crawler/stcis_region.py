import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException

def _select_by_text_with_js(drv, select_el, text):
    opt = select_el.find_element(By.XPATH, f".//option[contains(normalize-space(.), '{text}')]")
    drv.execute_script("""
        const sel = arguments[0], opt = arguments[1];
        opt.selected = true; sel.value = opt.value;
        sel.dispatchEvent(new Event('change', {bubbles:true}));
    """, select_el, opt)

def set_region_gyeongnam_changwon(drv, sec=10):
    try:
        btn = W(drv, sec).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(.,'공간선택')]/descendant::button[normalize-space(.)='시군구']")))
        drv.execute_script("arguments[0].click();", btn); time.sleep(0.2)
    except TimeoutException:
        pass

    sido = W(drv, sec).until(EC.element_to_be_clickable((By.ID, "searchPopSttnZoneSd")))
    try: Select(sido).select_by_visible_text("경상남도")
    except ElementNotInteractableException: _select_by_text_with_js(drv, sido, "경상남도")
    time.sleep(0.25)

    sgg = W(drv, sec).until(EC.element_to_be_clickable((By.ID, "searchPopSttnZoneSgg")))
    W(drv, sec).until(lambda d: any("창원" in o.text for o in sgg.find_elements(By.TAG_NAME, "option")))
    target = "창원시" if any("창원시" in o.text for o in sgg.find_elements(By.TAG_NAME,"option")) else "창원특례시"
    try: Select(sgg).select_by_visible_text(target)
    except ElementNotInteractableException: _select_by_text_with_js(drv, sgg, target)
    time.sleep(0.25)