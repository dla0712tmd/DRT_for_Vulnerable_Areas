# stcis_stop.py
import re, time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException

# ── 유틸
def _accept_alert_if_any(drv):
    try:
        a = drv.switch_to.alert
        t = a.text
        a.accept()
        return t
    except NoAlertPresentException:
        return None

def _set_input_framework_safe(drv, css_sel, value) -> bool:
    js = """
    const el = document.querySelector(arguments[0]); if(!el) return false;
    el.removeAttribute('readonly');
    const d = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value');
    if(d && d.set) d.set.call(el, arguments[1]); else el.value = arguments[1];
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
    return !!el.value;
    """
    return bool(drv.execute_script(js, css_sel, value))

# ── 모달 대기/행 수집
def wait_modal(drv, sec=6):
    try:
        W(drv, sec).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#popupSttn")))
        return True
    except TimeoutException:
        return False

def _data_rows_in_modal(modal):
    """실제 데이터 행만 반환(무자료 안내행 제외)"""
    rows = modal.find_elements(By.XPATH, ".//table//tbody/tr[td]")
    clean = []
    for r in rows:
        tds = r.find_elements(By.TAG_NAME, "td")
        if not tds:
            continue
        txt = " ".join(td.text.strip() for td in tds if td.text.strip())
        # 안내 문구 포함
        if "검색된 내용이 없습니다" in txt:
            continue
        # 단일 셀 + colspan → 무자료 행
        if len(tds) == 1 and (tds[0].get_attribute("colspan") or "없습니다" in txt):
            continue
        # nodata 클래스
        cls = (r.get_attribute("class") or "").lower()
        if "nodata" in cls:
            continue
        clean.append(r)
    return clean

def modal_rows(drv, sec=10):
    W(drv, sec).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#popupSttn")))
    modal = drv.find_element(By.CSS_SELECTOR, "#popupSttn")
    rows = _data_rows_in_modal(modal)
    return modal, rows

def modal_has_no_result(drv) -> bool:
    try:
        m = drv.find_element(By.CSS_SELECTOR, "#popupSttn")
    except:
        return True
    return len(_data_rows_in_modal(m)) == 0

def count_modal_rows(drv, sec=10) -> int:
    W(drv, sec).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#popupSttn")))
    return len(_data_rows_in_modal(drv.find_element(By.CSS_SELECTOR, "#popupSttn")))

def _find_col_index(modal, keywords):
    ths = modal.find_elements(By.XPATH, ".//table//thead//th")
    for i, th in enumerate(ths):
        t = th.text.strip()
        if any(k in t for k in keywords):
            return i
    return None

def _norm(s: str) -> str:
    if s is None:
        return ""
    return re.sub(r"[^가-힣A-Za-z0-9]", "", s)

def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def list_modal_rows(drv, sec=10):
    """
    모달에서 모든 행의 텍스트, ARS, 정류장명(name)을 수집
    """
    modal, rows = modal_rows(drv, sec)
    res = []
    ars_col  = _find_col_index(modal, ["ARS", "ARS번호"])
    name_col = _find_col_index(modal, ["정류장명", "정류장", "정류소명", "정류소"])

    for i, r in enumerate(rows):
        tds = r.find_elements(By.TAG_NAME, "td")
        if not tds:
            continue
        text = " | ".join(td.text.strip() for td in tds if td.text.strip())
        ars = None
        if ars_col is not None and ars_col < len(tds):
            val = tds[ars_col].text.strip()
            ars = None if val in ("", "-", "~") else val
        elif len(tds) >= 5:
            val = tds[4].text.strip()
            ars = None if val in ("", "-", "~") else val
        # 정류장명
        if name_col is not None and name_col < len(tds):
            name = tds[name_col].text.strip()
        else:
            name = tds[-1].text.strip()
        res.append({"idx": i, "text": text, "ars": ars, "name": name})
    return res

# ── 검색 → 모달 오픈
def search_stop(drv, name: str, sec: int = 10):
    css_sel = "#popupSearchSttnNm"
    try:
        W(drv, sec).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_sel)))
        if not _set_input_framework_safe(drv, css_sel, name):
            raise RuntimeError("정류장명 입력 실패")
    except TimeoutException:
        inp = W(drv, sec).until(EC.presence_of_element_located((
            By.XPATH, "//input[contains(@placeholder,'정류장명') or contains(@aria-label,'정류장명')]"
        )))
        drv.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
        try: inp.clear()
        except: pass
        try: inp.send_keys(name)
        except:
            _set_input_framework_safe(drv, css_sel, name)

    btn = None
    for loc in [
        (By.XPATH, "//*[@id='sttn_space1']/li[2]/button"),
        (By.CSS_SELECTOR, "#sttn_space1 li:nth-child(2) button"),
        (By.XPATH, "//input[@id='popupSearchSttnNm']/following::button[1]"),
        (By.XPATH, "(//button[normalize-space(.)='검색'])[1]"),
        (By.XPATH, "(//button[contains(.,'검색')])[1]"),
    ]:
        try:
            btn = W(drv, sec).until(EC.element_to_be_clickable(loc))
            break
        except:
            pass
    if not btn:
        raise RuntimeError("정류장 검색 버튼 미발견")

    drv.execute_script("arguments[0].click();", btn)
    _accept_alert_if_any(drv)
    if not wait_modal(drv, sec):
        drv.execute_script("arguments[0].click();", btn)
        _accept_alert_if_any(drv)
        if not wait_modal(drv, sec):
            raise RuntimeError("검색 결과 모달을 열지 못했습니다.")

# ── 체크 & 확인
def _click_row_checkbox(drv, row, modal=None):
    drv.execute_script("arguments[0].scrollIntoView({block:'center'});", row)
    time.sleep(0.05)
    try:
        drv.execute_script("arguments[0].click();", row); time.sleep(0.05)
    except:
        pass
    try:
        overlay = row.find_element(By.CSS_SELECTOR, "div.check")
        ActionChains(drv).move_to_element_with_offset(overlay, 6, 6).click().perform()
    except:
        pass
    try:
        cb = row.find_element(By.XPATH, ".//input[@type='checkbox']")
        drv.execute_script("""
            const cb=arguments[0];
            cb.checked=true;
            cb.dispatchEvent(new Event('input',{bubbles:true}));
            cb.dispatchEvent(new Event('change',{bubbles:true}));
        """, cb)
    except:
        pass

def _click_modal_confirm(drv, modal):
    btn = modal.find_element(By.XPATH, ".//button[contains(.,'선택') or contains(.,'확인')]")
    drv.execute_script("arguments[0].click();", btn)
    W(drv, 10).until(EC.invisibility_of_element_located(
        (By.XPATH, "//div[@id='popupSttn' and contains(@style,'display: block')]")
    ))

# ── 스마트 선택
def pick_modal_smart(drv, ars_no: str | None, row_text_sub: str | None,
                     sec=10, name_hint: str | None=None):
    modal, rows = modal_rows(drv, sec)
    target = None
    want_digits = _digits(ars_no) if ars_no else ""
    needle_norm = _norm(name_hint) if name_hint else ""
    text_norm   = _norm(row_text_sub) if row_text_sub else ""

    if want_digits:
        for r in rows:
            tds = r.find_elements(By.TAG_NAME, "td")
            if any(_digits(td.text) == want_digits for td in tds):
                target = r; break

    if target is None and needle_norm:
        name_col = _find_col_index(modal, ["정류장명", "정류장", "정류소명", "정류소"])
        for r in rows:
            tds = r.find_elements(By.TAG_NAME, "td")
            if not tds: continue
            cand = tds[name_col].text if name_col is not None and name_col < len(tds) else tds[-1].text
            if _norm(cand) == needle_norm:
                target = r; break

    if target is None and text_norm:
        for r in rows:
            if _norm(r.text).find(text_norm) >= 0:
                target = r; break

    if target is None:
        raise RuntimeError(f"행을 찾지 못했습니다. ARS={ars_no!r}, name~={name_hint!r}")

    _click_row_checkbox(drv, target, modal)
    _click_modal_confirm(drv, modal)

def pick_modal_by_global_index(drv, idx: int, sec=10):
    modal, rows = modal_rows(drv, sec)
    if idx < 0 or idx >= len(rows):
        raise RuntimeError(f"행 index {idx} 범위 초과 (총 {len(rows)})")
    row = rows[idx]
    _click_row_checkbox(drv, row, modal)
    _click_modal_confirm(drv, modal)

def close_modal(drv, sec=5):
    try:
        modal = drv.find_element(By.CSS_SELECTOR, "#popupSttn")
        close_btn = modal.find_element(By.XPATH, ".//button[contains(@class,'btn') and contains(.,'닫기')]")
        drv.execute_script("arguments[0].click();", close_btn)
        W(drv, sec).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#popupSttn")))
    except Exception as e:
        print(f"[WARN] 모달 닫기 실패 또는 이미 닫힘: {e}")