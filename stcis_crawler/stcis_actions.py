# stcis_actions.py
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC

def click_query_results(drv, sec=12):
    """
    '검색결과조회' 버튼 클릭. 
    화면 크기와 관계없이 안정적으로 동작하도록 JS 함수 직접 호출 fallback 포함.
    """
    try:
        # 버튼 존재 확인
        btn = W(drv, sec).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(.,'검색결과조회')]"))
        )
        drv.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        # 클릭 시도
        try:
            drv.execute_script("arguments[0].click();", btn)
        except:
            btn.click()
    except Exception:
        # 버튼이 안 잡히면 JS 함수 직접 호출
        drv.execute_script("if (typeof fnSearch === 'function') fnSearch();")

    # 결과 로딩 대기
    try:
        W(drv, sec).until(EC.presence_of_element_located((
            By.XPATH, "//div[@id='rgrstyReportResult' or @id='rgstryReportResult']//table"
        )))
    except:
        pass
    time.sleep(0.5)