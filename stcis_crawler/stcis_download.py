# stcis_download.py
import os, time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC

def _latest_noncr_file(path_list):
    files = [p for p in path_list if os.path.isfile(p) and not p.endswith(".crdownload")]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def _wait_download_complete(download_dir, since_ts, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        paths = [os.path.join(download_dir, n) for n in os.listdir(download_dir)]
        cand = _latest_noncr_file(paths)
        if cand and os.path.getmtime(cand) >= since_ts:
            return cand
        time.sleep(0.5)
    return None

def click_download(drv, sec=12, download_dir=None, desired_basename=None, wait_timeout=30):
    # 1) 버튼 탐색
    locs = [
        (By.ID, "btnExport"),
        (By.CSS_SELECTOR, "a#btnExport, button#btnExport"),
        (By.XPATH, "//a[normalize-space(.)='다운로드']"),
        (By.XPATH, "//button[normalize-space(.)='다운로드']"),
        (By.XPATH, "//a[contains(.,'엑셀')]"),
        (By.XPATH, "//button[contains(.,'엑셀')]"),
        (By.XPATH, "//a[contains(@onclick,'excel') or contains(@onclick,'Export')]"),
        (By.XPATH, "//button[contains(@onclick,'excel') or contains(@onclick,'Export')]"),
    ]
    btn = None
    for by, sel in locs:
        try:
            btn = W(drv, 4).until(EC.presence_of_element_located((by, sel)))
            drv.execute_script("""
              const e=arguments[0];
              e.style.display=''; e.style.visibility='visible';
              e.removeAttribute('disabled'); e.classList.remove('disabled');
            """, btn)
            drv.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            W(drv, 3).until(EC.element_to_be_clickable((by, sel)))
            break
        except:
            btn = None

    clicked_at = time.time()
    # 2) 클릭 or JS 콜백
    if btn:
        try:
            drv.execute_script("arguments[0].click();", btn)
        except:
            btn.click()
    else:
        drv.execute_script("""
          if (window.rgrstyExcelExport) { rgrstyExcelExport('0'); }
          else if (window.excelExport) { excelExport('0'); }
        """)
    time.sleep(0.8)  # 트리거 간격

    # 3) 다운로드 감시 및 리네임
    if not download_dir:
        return None
    os.makedirs(download_dir, exist_ok=True)
    saved = _wait_download_complete(download_dir, since_ts=clicked_at, timeout=wait_timeout)
    if not saved:
        print("[WARN] 다운로드 완료 파일을 찾지 못했습니다. → 브라우저 종료 후 스킵")
        drv.quit()
        return None

    if desired_basename:
        root, ext = os.path.splitext(saved)
        new_path = os.path.join(download_dir, desired_basename + ext)
        try:
            os.replace(saved, new_path)
            return new_path
        except:
            return saved
    return saved