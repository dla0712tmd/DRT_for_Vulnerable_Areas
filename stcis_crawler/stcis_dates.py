# stcis_dates.py
# 날짜 입력: readonly 필드 대응(JS로 값 주입 + input/change/blur 이벤트)
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC

def _set_value_with_events(drv, css_selector: str, value: str) -> bool:
    js = """
    const el = document.querySelector(arguments[0]);
    if (!el) return false;
    el.removeAttribute('readonly');
    el.value = arguments[1];
    el.dispatchEvent(new Event('input',  {bubbles:true}));
    el.dispatchEvent(new Event('change', {bubbles:true}));
    el.dispatchEvent(new Event('blur',   {bubbles:true}));
    return true;
    """
    return bool(drv.execute_script(js, css_selector, value))

def set_period_js(drv,
                  start_ymd: str,
                  end_ymd: str,
                  start_sel: str = "#searchFromDay",
                  end_sel: str   = "#searchToDay",
                  wait_sec: int = 10,
                  settle_sleep: float = 0.2) -> None:
    """
    시작일 → 내부 검증 대기 → 종료일 순서로 주입.
    사이트의 14일 제한을 넘기면 종료일이 리셋될 수 있음.
    """
    # 시작일
    W(drv, wait_sec).until(EC.presence_of_element_located((By.CSS_SELECTOR, start_sel)))
    if not _set_value_with_events(drv, start_sel, start_ymd):
        raise RuntimeError(f"시작일 요소를 찾지 못함: {start_sel}")
    time.sleep(settle_sleep)

    # 종료일
    W(drv, wait_sec).until(EC.presence_of_element_located((By.CSS_SELECTOR, end_sel)))
    if not _set_value_with_events(drv, end_sel, end_ymd):
        raise RuntimeError(f"종료일 요소를 찾지 못함: {end_sel}")
    time.sleep(settle_sleep)

# (옵션) 직접 타이핑이 가능한 페이지용 백업 경로
def set_period_direct(drv,
                      start_ymd: str,
                      end_ymd: str,
                      start_sel: str = "#searchFromDay",
                      end_sel: str   = "#searchToDay",
                      wait_sec: int = 10) -> None:
    s = W(drv, wait_sec).until(EC.presence_of_element_located((By.CSS_SELECTOR, start_sel)))
    e = W(drv, wait_sec).until(EC.presence_of_element_located((By.CSS_SELECTOR, end_sel)))
    try:
        s.clear(); s.send_keys(start_ymd)
        e.clear(); e.send_keys(end_ymd)
    except Exception as ex:
        raise RuntimeError("direct 입력 실패: readonly 필드일 가능성") from ex