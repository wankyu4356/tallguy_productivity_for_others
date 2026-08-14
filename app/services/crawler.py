from __future__ import annotations

import asyncio
import hashlib
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
)

from app.config import settings
from app.models.schemas import ArticleInfo
from app.services.browser import SeleniumContext
from app.utils.logging import get_logger

logger = get_logger(__name__)

KST = ZoneInfo("Asia/Seoul")

DEALSITEPLUS_BASE = "https://dealsiteplus.co.kr"
DEALSITEPLUS_LOGIN_URL = f"{DEALSITEPLUS_BASE}/user/access/login"

# Target sections: (display_label, section_code)
# URL pattern: /categories/{section_code}
SECTION_CODES = [
    ("Deals - M&A",           "002062"),
    ("Deals - ECM",           "002063"),
    ("Deals - IPO",           "002064"),
    ("Deals - PF",            "002065"),
    ("Deals - Debt/Loan",     "002066"),
    ("Investors - IB",        "016068"),
    ("Investors - PEF/VC",    "016069"),
    ("Industry - 건설/부동산",  "025073"),
    ("Industry - 제약/바이오",  "025074"),
]


LOGIN_TIMEOUT = 300  # 5 minutes max wait for manual login


def _is_error_page(driver) -> bool:
    """Check whether the current page is a 404 or error page."""
    page_text = driver.page_source[:3000].lower()
    current_url = driver.current_url.lower()
    title = driver.title.lower() if driver.title else ""

    error_indicators = [
        "찾을 수 없습니다",
        "찾을 수가 없습니다",
        "페이지를 찾을 수",
        "존재하지 않는 페이지",
        "요청하신 페이지",
        "404",
        "not found",
        "page not found",
        "error page",
    ]

    for indicator in error_indicators:
        if indicator in page_text or indicator in title or indicator in current_url:
            logger.warning(f"에러 페이지 감지 | url={current_url} | title={driver.title} | match='{indicator}'")
            return True

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body_text = body.text.strip()
        if len(body_text) < 20:
            return True
    except Exception:
        pass

    return False


def _check_logged_in(driver) -> bool:
    """Check if the user is currently logged in to DealSitePlus.

    Strategy:
    1. Check for .ht-r-user-id element (logged-in indicator)
    2. Check for logout link
    3. Check for .ht-r-user-not-signedin (not logged in indicator)
    """
    current_url = driver.current_url
    title = driver.title or "(no title)"

    # 1) Check for logged-in user element
    try:
        user_els = driver.find_elements(By.CSS_SELECTOR, ".ht-r-user-id")
        if user_els:
            for el in user_els:
                text = el.text.strip()
                if text:
                    logger.info(f"로그인 확인됨 (ht-r-user-id) | user={text} | url={current_url}")
                    return True
    except Exception:
        pass

    # 2) Check for logout form/link
    try:
        logout_els = driver.find_elements(By.CSS_SELECTOR, "form[action*='logout'], a[href*='logout']")
        if logout_els:
            logger.info(f"로그인 확인됨 (logout 링크) | url={current_url}")
            return True
    except Exception:
        pass

    # 3) Check for mypage link (only visible when logged in)
    try:
        mypage_els = driver.find_elements(By.CSS_SELECTOR, "a[href*='/mypage']")
        if mypage_els:
            logger.info(f"로그인 확인됨 (mypage 링크) | url={current_url}")
            return True
    except Exception:
        pass

    # 4) Check body text for '로그아웃'
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        visible_text = body.text
        if "로그아웃" in visible_text:
            logger.info(f"로그인 확인됨 | url={current_url} | '로그아웃' 텍스트 표시")
            return True
    except Exception:
        pass

    # 5) Negative check: not-signed-in indicator
    try:
        not_signed_in = driver.find_elements(By.CSS_SELECTOR, ".ht-r-user-not-signedin")
        if not_signed_in:
            logger.info(f"로그인 안됨 (ht-r-user-not-signedin) | url={current_url}")
            return False
    except Exception:
        pass

    logger.info(f"로그인 안됨 | url={current_url} | title={title}")
    return False


def _find_login_form_and_fill(driver, user_id: str, password: str) -> bool:
    """Find DealSitePlus login form fields, fill them, and submit.

    DealSitePlus login form structure:
    - form#loginForm
    - input#login (username)
    - input#password (password)
    - button#submitBtn (submit)
    - CSRF token in meta[name="_csrf"] and input#token
    """
    id_selectors = [
        "form#loginForm input#login",
        "input#login",
        "input[name='login']",
    ]

    pw_selectors = [
        "form#loginForm input#password",
        "input#password",
        "input[name='password']",
    ]

    submit_selectors = [
        "button#submitBtn",
        "form#loginForm button[type='submit']",
        "button.btn-big-confirm",
    ]

    id_field = None
    pw_field = None

    for sel in id_selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            if el.is_displayed():
                id_field = el
                logger.debug(f"ID 필드 발견: {sel}")
                break
        except (NoSuchElementException, ElementNotInteractableException):
            continue

    for sel in pw_selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            if el.is_displayed():
                pw_field = el
                logger.debug(f"PW 필드 발견: {sel}")
                break
        except (NoSuchElementException, ElementNotInteractableException):
            continue

    if not id_field or not pw_field:
        logger.warning("로그인 폼 필드를 찾을 수 없습니다.")
        return False

    try:
        id_field.clear()
        id_field.send_keys(user_id)
        time.sleep(0.3)

        pw_field.clear()
        pw_field.send_keys(password)
        time.sleep(0.3)

        for sel in submit_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed():
                    btn.click()
                    logger.info(f"로그인 버튼 클릭: {sel}")
                    return True
            except (NoSuchElementException, ElementNotInteractableException):
                continue

        # Fallback: trigger via JS
        logger.info("로그인 버튼을 못 찾아 JS로 제출 시도")
        try:
            driver.execute_script(
                "document.getElementById('submitBtn').click();"
            )
            return True
        except Exception:
            pass

        from selenium.webdriver.common.keys import Keys
        pw_field.send_keys(Keys.RETURN)
        logger.info("PW 필드에서 Enter 키로 로그인 시도")
        return True

    except Exception as e:
        logger.warning(f"로그인 폼 입력 중 오류: {e}")
        return False


def _load_login_page(driver) -> bool:
    """Load DealSitePlus login page."""
    logger.debug(f"로그인 URL 로드: {DEALSITEPLUS_LOGIN_URL}")
    try:
        driver.get(DEALSITEPLUS_LOGIN_URL)
    except TimeoutException:
        logger.debug(f"로그인 URL 타임아웃: {DEALSITEPLUS_LOGIN_URL}")
        return False

    time.sleep(3)

    if _is_error_page(driver):
        logger.debug(f"로그인 URL 에러: {DEALSITEPLUS_LOGIN_URL}")
        return False

    logger.info(f"로그인 페이지 로드 성공: {DEALSITEPLUS_LOGIN_URL}")
    return True


def _auto_login_sync(driver) -> bool:
    """Attempt automatic login using configured credentials."""
    user_id = settings.DEALSITEPLUS_ID
    password = settings.DEALSITEPLUS_PW

    if not user_id or not password:
        logger.info("자동 로그인 자격증명 미설정 — 수동 로그인으로 전환")
        return False

    _load_login_page(driver)
    time.sleep(2)

    form_submitted = _find_login_form_and_fill(driver, user_id, password)
    if not form_submitted:
        logger.warning("자동 로그인 폼 제출 실패 — 수동 로그인으로 전환")
        return False

    # Wait for AJAX login to process
    time.sleep(3)

    # Check for login error messages
    try:
        page_source = driver.page_source
        error_indicators = ["아이디 또는 비밀번호", "로그인 실패", "입력해 주세요", "확인해 주세요"]
        if any(ind in page_source for ind in error_indicators):
            logger.warning("로그인 실패 메시지 감지 — 자격증명을 확인하세요")
            return False
    except Exception:
        pass

    # Navigate to main page to verify login
    driver.get(DEALSITEPLUS_BASE)
    time.sleep(2)

    if _check_logged_in(driver):
        logger.info("자동 로그인 성공!")
        return True

    logger.warning("자동 로그인 결과 불확실 — 수동 로그인으로 전환")
    return False


def _manual_login_sync(driver, timeout: int = LOGIN_TIMEOUT) -> bool:
    """Open DealSitePlus and wait for user to log in manually."""
    _load_login_page(driver)

    logger.info("브라우저에서 딜사이트플러스 로그인을 완료하세요 (최대 5분 대기)...")

    last_url = driver.current_url
    start = time.time()
    while time.time() - start < timeout:
        try:
            current_url = driver.current_url

            if current_url != last_url:
                logger.info(f"페이지 이동 감지 | {last_url} → {current_url}")
                last_url = current_url
                time.sleep(2)

            if _check_logged_in(driver):
                logger.info("수동 로그인 성공!")
                return True

        except Exception:
            pass
        time.sleep(3)

    logger.error("로그인 타임아웃 (5분)")
    return False


def _login_sync(driver) -> bool:
    """Combined login: try auto-login first, then fall back to manual."""
    try:
        if _auto_login_sync(driver):
            return True
    except Exception as e:
        logger.warning(f"자동 로그인 중 예외 발생: {e}")

    logger.info("수동 로그인 모드로 전환합니다.")
    return _manual_login_sync(driver)


async def login(context: SeleniumContext) -> bool:
    """Login to DealSitePlus. Tries auto-login first, then manual."""
    try:
        return await asyncio.to_thread(_login_sync, context.driver)
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return False


def _parse_datetime(date_str: str) -> datetime | None:
    """Parse DealSitePlus date string into datetime.

    DealSitePlus format: "2026.03.10 17:00:28" or "2026.03.09 17:49"
    """
    date_str = date_str.strip()
    now = datetime.now(KST)

    patterns = [
        # Full with seconds: 2026.03.10 17:00:28
        (r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})", "full_datetime_sec"),
        # Full: 2026.03.09 17:49
        (r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s+(\d{1,2}):(\d{2})", "full_datetime"),
        # Date only: 2026.03.09
        (r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", "date_only"),
        # Short: 03-09 09:27 (no year)
        (r"(\d{1,2})[.\-/](\d{1,2})\s+(\d{1,2}):(\d{2})", "short_datetime"),
        # Short date only: 03-09
        (r"(\d{1,2})[.\-/](\d{1,2})$", "short_date"),
    ]
    for pat, kind in patterns:
        m = re.match(pat, date_str)
        if m:
            groups = m.groups()
            try:
                if kind == "full_datetime_sec":
                    return datetime(int(groups[0]), int(groups[1]), int(groups[2]),
                                    int(groups[3]), int(groups[4]), int(groups[5]), tzinfo=KST)
                elif kind == "full_datetime":
                    return datetime(int(groups[0]), int(groups[1]), int(groups[2]),
                                    int(groups[3]), int(groups[4]), tzinfo=KST)
                elif kind == "date_only":
                    return datetime(int(groups[0]), int(groups[1]), int(groups[2]),
                                    tzinfo=KST)
                elif kind == "short_datetime":
                    return datetime(now.year, int(groups[0]), int(groups[1]),
                                    int(groups[2]), int(groups[3]), tzinfo=KST)
                elif kind == "short_date":
                    return datetime(now.year, int(groups[0]), int(groups[1]),
                                    tzinfo=KST)
            except (ValueError, OverflowError):
                continue
    return None


def _make_article_id(url: str, title: str) -> str:
    """Generate a stable ID for an article based on its URL.

    DealSitePlus URL pattern: /articles/{articleId}/{categoryCode}
    """
    m = re.search(r'/articles/(\d+)', url)
    if m:
        return m.group(1)
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    raw = f"{parsed.path}:{title}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _diagnose_page(driver) -> str:
    """Diagnose current page state for troubleshooting."""
    current_url = driver.current_url
    title = driver.title or "(no title)"
    body_text = ""
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text[:300]
    except Exception:
        pass

    if any(kw in current_url.lower() for kw in ["login", "access/login"]):
        return f"세션 만료 (로그인 리다이렉트) | url={current_url}"

    bot_indicators = ["접근이 차단", "차단", "비정상", "자동화", "bot", "blocked", "denied", "captcha"]
    for ind in bot_indicators:
        if ind in body_text.lower() or ind in title.lower():
            return f"봇 감지/접근 차단 | match='{ind}' | url={current_url}"

    if _is_error_page(driver):
        return f"에러 페이지 | url={current_url} | title={title}"

    if len(body_text.strip()) < 50:
        return f"빈 페이지 | url={current_url} | body_len={len(body_text.strip())}"

    return f"셀렉터 매칭 실패 | url={current_url} | title={title} | body={body_text[:150]}"


def _navigate_to_section(driver, section_code: str, page: int = 1) -> bool:
    """Navigate directly to a category page.

    URL pattern: /categories/{section_code}?page={page}
    """
    url = f"{DEALSITEPLUS_BASE}/categories/{section_code}"
    if page > 1:
        url += f"?page={page}"
    logger.info(f"섹션 이동: Code={section_code} page={page} | url={url}")
    driver.get(url)
    time.sleep(2)

    if _is_error_page(driver):
        logger.warning(f"섹션 페이지 에러 | Code={section_code} | url={driver.current_url}")
        return False

    current_url = driver.current_url.lower()
    if "access/login" in current_url:
        logger.error(f"세션 만료: 로그인 리다이렉트 | url={driver.current_url}")
        return False

    return True


def _has_next_page(driver) -> bool:
    """Check if there is a next page in pagination.

    DealSitePlus pagination: a.next.active means next page exists.
    """
    try:
        next_els = driver.find_elements(By.CSS_SELECTOR, "a.next.active")
        return len(next_els) > 0
    except Exception:
        return False


def _crawl_current_page(driver, category_label: str) -> list[ArticleInfo]:
    """Extract articles from the currently loaded DealSitePlus category page.

    HTML structure per article:
    <div class="mnm-news">
        <div class="mnm-news-right">
            <span class="mnm-news-title-wrap">
                <a class="ss-news-top-title" href="/articles/{id}/{catCode}">
                    <span class="multi-line1">Article Title</span>
                </a>
            </span>
            <a class="mnm-news-txt" href="...">Summary...</a>
            <div class="mnm-news-info">
                <span>딜사이트 기자명</span>
                <span>2026.03.10 17:00:28</span>
            </div>
        </div>
    </div>
    """
    articles = []
    time.sleep(1)

    current_url = driver.current_url.lower()
    if "access/login" in current_url:
        logger.error(f"세션 만료: 로그인 리다이렉트 | url={driver.current_url}")
        return []

    if _is_error_page(driver):
        logger.warning(f"에러 페이지 | url={driver.current_url} | title={driver.title}")
        return []

    try:
        news_items = driver.find_elements(By.CSS_SELECTOR, "div.mnm-news")
    except Exception:
        news_items = []

    if not news_items:
        logger.warning(f"기사 컨테이너(div.mnm-news) 없음 | url={driver.current_url}")
        return []

    seen_urls = set()
    for item in news_items:
        try:
            title = ""
            href = ""

            try:
                title_link = item.find_element(By.CSS_SELECTOR, "a.ss-news-top-title")
                href = title_link.get_attribute("href") or ""
                try:
                    span = title_link.find_element(By.CSS_SELECTOR, "span.multi-line1")
                    title = span.text.strip()
                except Exception:
                    title = title_link.text.strip()
            except NoSuchElementException:
                continue

            if not title or len(title) < 3:
                continue
            if not href:
                continue
            if href in seen_urls:
                continue
            seen_urls.add(href)

            if not href.startswith("http"):
                href = DEALSITEPLUS_BASE + href

            # Extract summary
            summary = ""
            try:
                summary_el = item.find_element(By.CSS_SELECTOR, "a.mnm-news-txt")
                summary = summary_el.text.strip()
            except NoSuchElementException:
                pass

            # Extract date from mnm-news-info
            published_at = None
            try:
                info_spans = item.find_elements(By.CSS_SELECTOR, "div.mnm-news-info > span")
                if len(info_spans) >= 2:
                    date_text = info_spans[-1].text.strip()
                    published_at = _parse_datetime(date_text)
                elif len(info_spans) == 1:
                    date_text = info_spans[0].text.strip()
                    published_at = _parse_datetime(date_text)
            except Exception:
                pass

            article = ArticleInfo(
                id=_make_article_id(href, title),
                title=title,
                url=href,
                category=category_label.split(" - ")[0] if " - " in category_label else category_label,
                subcategory=category_label,
                published_at=published_at,
                summary=summary[:200] if summary else "",
            )
            articles.append(article)
        except Exception:
            continue

    logger.info(f"페이지 기사 수집: {len(articles)}개 | url={driver.current_url}")
    return articles


def _fetch_article_details(driver, articles: list[ArticleInfo], on_progress=None) -> None:
    """Fetch publish dates and summaries for articles missing them by visiting detail pages.

    DealSitePlus detail page selectors:
    - Date: div.nis-time
    - Summary: div.news-info-top-3news
    """
    needs_detail = [
        a for a in articles
        if (not a.published_at or not a.summary)
        and a.url
        and "dealsiteplus.co.kr" in a.url
    ]
    if not needs_detail:
        return

    logger.info(f"상세정보 보완 필요 기사 {len(needs_detail)}개 — 상세 페이지에서 날짜/요약 추출 시도")
    if on_progress:
        on_progress(f"기사 상세정보 보완 중... ({len(needs_detail)}개)")

    original_url = driver.current_url

    date_fetched = 0
    summary_fetched = 0
    consecutive_errors = 0
    for a in needs_detail:
        try:
            need_date = not a.published_at
            need_summary = not a.summary

            logger.debug(f"상세정보 방문: {a.title[:40]} | url={a.url}")
            driver.get(a.url)
            time.sleep(0.5)
            consecutive_errors = 0

            if need_date:
                try:
                    date_el = driver.find_element(By.CSS_SELECTOR, "div.nis-time")
                    date_text = date_el.text.strip()
                    parsed = _parse_datetime(date_text)
                    if parsed:
                        a.published_at = parsed
                        date_fetched += 1
                except NoSuchElementException:
                    pass

            if need_summary:
                try:
                    summary_el = driver.find_element(By.CSS_SELECTOR, "div.news-info-top-3news")
                    text = summary_el.text.strip()
                    if text and len(text) >= 10:
                        a.summary = text[:200]
                        summary_fetched += 1
                except NoSuchElementException:
                    pass

        except Exception as e:
            consecutive_errors += 1
            err_msg = str(e).lower()
            is_session_dead = (
                "invalid session" in err_msg
                or "disconnected" in err_msg
                or "session deleted" in err_msg
                or "unable to receive message from renderer" in err_msg
            )
            if is_session_dead or consecutive_errors >= 3:
                idx = needs_detail.index(a) if a in needs_detail else -1
                logger.warning(
                    f"상세정보 수집 중단 | reason={'session_dead' if is_session_dead else f'consecutive_errors={consecutive_errors}'} | "
                    f"진행={idx + 1}/{len(needs_detail)} | "
                    f"날짜추출={date_fetched}개 | article={a.title[:40]} | "
                    f"url={a.url} | error={type(e).__name__}: {str(e)[:200]}"
                )
                break
            logger.debug(f"상세정보 추출 실패: {a.title[:30]} | url={a.url} | {type(e).__name__}: {e}")
            continue

    logger.info(
        f"상세정보 보완 완료 | 대상={len(needs_detail)}개 | "
        f"날짜추출={date_fetched}개 | 요약추출={summary_fetched}개 | "
        f"연속에러={consecutive_errors}"
    )
    if on_progress:
        on_progress(f"상세정보 보완: 날짜 {date_fetched}개, 요약 {summary_fetched}개 추출")

    try:
        driver.get(original_url)
        time.sleep(1)
    except Exception:
        pass


def _crawl_section_sync(
    driver,
    category_label: str,
    section_code: str,
    date_from: datetime,
    date_to: datetime,
    on_progress: callable | None = None,
) -> list[ArticleInfo]:
    """Crawl articles from a DealSitePlus category with URL-based pagination."""
    all_articles = []
    seen_ids = set()
    page_num = 1
    max_pages = 20
    consecutive_undated_pages = 0

    while page_num <= max_pages:
        if page_num > 1:
            if not _navigate_to_section(driver, section_code, page_num):
                break

        articles = _crawl_current_page(driver, category_label)

        if not articles:
            if page_num == 1:
                diag = _diagnose_page(driver)
                logger.warning(f"기사 0개 | {category_label} | {diag}")
                if on_progress:
                    on_progress(f"⚠ {category_label}: {diag}")
            break

        new_ids = {a.id for a in articles}
        if new_ids.issubset(seen_ids):
            logger.info(f"중복 페이지 감지 — 페이지네이션 중단 | {category_label} 페이지 {page_num}")
            break
        seen_ids.update(new_ids)

        found_old = False
        dated_count = 0
        for a in articles:
            if a.published_at:
                dated_count += 1
                if date_from <= a.published_at <= date_to:
                    all_articles.append(a)
                elif a.published_at < date_from:
                    found_old = True
                else:
                    all_articles.append(a)
            else:
                all_articles.append(a)

        if dated_count == 0:
            consecutive_undated_pages += 1
        else:
            consecutive_undated_pages = 0

        if on_progress:
            on_progress(f"{category_label}: {len(all_articles)}개 수집 중... (페이지 {page_num})")

        if found_old:
            break

        if consecutive_undated_pages >= 3:
            logger.warning(
                f"연속 {consecutive_undated_pages}페이지 날짜 파싱 불가 — "
                f"페이지네이션 중단 | {category_label} 페이지 {page_num} | "
                f"수집된 기사 {len(all_articles)}개"
            )
            break

        if not _has_next_page(driver):
            break

        page_num += 1

    if on_progress:
        on_progress(f"{category_label}: {len(all_articles)}개 수집 완료")

    return all_articles


async def crawl_all_categories(
    context: SeleniumContext,
    date_from: datetime,
    date_to: datetime,
    on_progress: callable | None = None,
) -> list[ArticleInfo]:
    """Crawl all target categories by navigating to category URLs."""

    def _crawl_sync():
        driver = context.driver
        all_articles: list[ArticleInfo] = []
        seen_ids = set()
        seen_titles = set()

        for label, code in SECTION_CODES:
            if on_progress:
                on_progress(f"카테고리 수집 시작: {label}")

            if not _navigate_to_section(driver, code):
                if on_progress:
                    on_progress(f"⚠ '{label}' 섹션 이동 실패 (Code={code})")
                continue

            articles = _crawl_section_sync(driver, label, code, date_from, date_to, on_progress)
            for a in articles:
                title_key = a.title.strip()
                if a.id not in seen_ids and title_key not in seen_titles:
                    seen_ids.add(a.id)
                    seen_titles.add(title_key)
                    all_articles.append(a)

        if len(all_articles) == 0:
            msg = "전체 크롤링 결과 0개 — 로그인 만료, 봇 차단, 또는 사이트 구조 변경 가능성"
            logger.error(msg)
            if on_progress:
                on_progress(f"⚠ {msg}")
        else:
            try:
                _fetch_article_details(driver, all_articles, on_progress)
            except Exception as e:
                logger.warning(f"상세정보 보완 중 오류 (수집된 기사는 유지): {e}")
                if on_progress:
                    on_progress(f"⚠ 상세정보 보완 중 오류 — 수집된 기사는 유지됩니다")

            before_count = len(all_articles)
            all_articles = [
                a for a in all_articles
                if not a.published_at or (date_from <= a.published_at <= date_to)
            ]
            filtered_count = before_count - len(all_articles)
            if filtered_count > 0:
                logger.info(f"날짜 확인 후 범위 외 기사 {filtered_count}개 제거")
                if on_progress:
                    on_progress(f"날짜 확인 후 범위 외 기사 {filtered_count}개 제거")

            if on_progress:
                on_progress(f"전체 크롤링 완료: 총 {len(all_articles)}개 기사 수집")

        return all_articles

    try:
        return await asyncio.to_thread(_crawl_sync)
    except Exception as e:
        logger.error(
            f"크롤링 치명적 오류 | type={type(e).__name__} | "
            f"date_range={date_from.strftime('%Y-%m-%d')}~{date_to.strftime('%Y-%m-%d')} | "
            f"categories={len(SECTION_CODES)}개",
            exc_info=True,
        )
        return []
