"""API 키 없이 네이버 블로그를 검색하고 글별 본문을 UTF-8 txt로 저장합니다.

실행: .venv/bin/python Naver.py
설치: python -m pip install selenium beautifulsoup4
Chrome 브라우저가 필요합니다.
"""

import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


SEARCH_URL = "https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query=%EC%9B%85%ED%8C%8C%EC%9D%B4+%EC%88%99%EB%8C%80"
START_DATE = "2025-06-30"
END_DATE = "2026-09-15"
SCROLL_IDLE_ROUNDS = 5
REQUIRED_TEXT = "웅파이"

OUTPUT_DIR = Path(__file__).resolve().parent / "naver_texts"
REQUEST_DELAY = 2
BODY_SELECTOR = ".se-main-container, #postViewArea, .post-view"


def dated_search_url():
    start = datetime.strptime(START_DATE, "%Y-%m-%d").date()
    end = datetime.strptime(END_DATE, "%Y-%m-%d").date()
    if start > end:
        raise ValueError("시작일은 종료일보다 늦을 수 없습니다.")
    parsed = urlparse(SEARCH_URL)
    query = parse_qs(parsed.query)
    query["nso"] = [f"so:r,p:from{start:%Y%m%d}to{end:%Y%m%d}"]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def extract_post_date(source):
    soup = BeautifulSoup(source, "html.parser")
    nodes = soup.select(".se_publishDate")
    if not nodes:
        nodes = soup.select(".post-top .date, .post .date, .post_date, .blog_date")
    for node in nodes:
        match = re.search(r"(\d{4})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})", node.get_text(" ", strip=True))
        if match:
            try:
                return datetime(*map(int, match.groups())).date()
            except ValueError:
                continue
    return None


def normalize_post_url(url):
    """블로그 홈/외부 사이트를 제외하고 같은 글의 URL을 통일합니다."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "blog.naver.com", "m.blog.naver.com"
    }:
        return None
    match = re.fullmatch(r"/([A-Za-z0-9_-]+)/(\d+)/?", parsed.path)
    if match:
        blog_id, post_id = match.groups()
    elif parsed.path.lower() == "/postview.naver":
        query = parse_qs(parsed.query)
        blog_id = query.get("blogId", [""])[0]
        post_id = query.get("logNo", [""])[0]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", blog_id) or not post_id.isdigit():
            return None
    else:
        return None
    return f"https://blog.naver.com/{blog_id}/{post_id}"


def collect_post_urls(driver, search_url):
    driver.get(search_url)
    WebDriverWait(driver, 15).until(
        lambda browser: browser.find_elements(By.CSS_SELECTOR, "a[href*='blog.naver.com']")
    )
    urls = []
    seen = set()
    unchanged = 0
    # 검색 결과가 더 이상 늘지 않으면 종료합니다.
    previous_height = 0
    while True:
        previous_count = len(urls)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for anchor in soup.select("a[href]"):
            url = normalize_post_url(anchor["href"])
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
        height = driver.execute_script("return document.body.scrollHeight")
        unchanged = unchanged + 1 if len(urls) == previous_count and height == previous_height else 0
        previous_height = height
        if len(urls) > previous_count:
            print(f"검색 결과에서 블로그 글 {len(urls)}건 발견", flush=True)
        if unchanged >= SCROLL_IDLE_ROUNDS:
            break
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(REQUEST_DELAY)
    return urls


def extract_body_text(source):
    """본문 영역만 추출해 메뉴, 댓글, HTML 태그를 제외합니다."""
    soup = BeautifulSoup(source, "html.parser")
    body = soup.select_one(".se-main-container")
    if body is None:
        body = soup.select_one("#postViewArea")
    if body is None:
        body = soup.select_one(".post-view")
    if body is None:
        return ""
    for element in body.select("script, style, noscript, iframe, .se-module-map, .se-module-oglink"):
        element.decompose()
    # 문단 내 강조 태그로 인해 단어가 줄바꿈되지 않도록 처리합니다.
    for br in body.find_all("br"):
        br.replace_with("\n")
    for element in body.select("span, b, strong, em, i, u, a"):
        element.unwrap()
    body.smooth()
    lines = [line.replace("\u200b", "").replace("\xa0", " ").strip()
             for line in body.get_text(separator="\n").splitlines()]
    return "\n".join(line for line in lines if line)


def fetch_post_text(driver, url):
    driver.switch_to.default_content()
    driver.get(url)

    def body_ready(browser):
        browser.switch_to.default_content()
        frames = browser.find_elements(By.ID, "mainFrame")
        if frames:
            browser.switch_to.frame(frames[0])
        return browser.find_elements(By.CSS_SELECTOR, BODY_SELECTOR)

    try:
        WebDriverWait(driver, 15).until(body_ready)
        source = driver.page_source
        return extract_body_text(source), extract_post_date(source)
    finally:
        driver.switch_to.default_content()


def main():
    keyword = parse_qs(urlparse(SEARCH_URL).query).get("query", ["search"])[0]
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        print("네이버 블로그 검색 결과를 확인하고 있습니다.")
        print(f"작성일 조건: {START_DATE} ~ {END_DATE} (양 끝 날짜 포함)")
        urls = collect_post_urls(driver, dated_search_url())
        if not urls:
            print("블로그 글을 찾지 못했습니다. 검색 결과나 페이지 구조를 확인해주세요.")
            return 1
        folder_name = re.sub(r"[^\w가-힣-]+", "_", keyword)[:50] or "search"
        output = OUTPUT_DIR / f"{folder_name}_{START_DATE}_{END_DATE}_{datetime.now():%Y%m%d_%H%M%S_%f}"
        output.mkdir(parents=True, exist_ok=True)
        (output / "urls.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")
        failures = []
        excluded = []
        excluded_keywords = []
        saved_urls = []
        saved = 0
        start_date = datetime.strptime(START_DATE, "%Y-%m-%d").date()
        end_date = datetime.strptime(END_DATE, "%Y-%m-%d").date()
        for index, url in enumerate(urls, 1):
            time.sleep(REQUEST_DELAY)
            try:
                text, post_date = fetch_post_text(driver, url)
                if post_date is None:
                    failures.append(url)
                    print(f"[{index}/{len(urls)}] 작성일 확인 불가: {url}")
                    continue
                if not start_date <= post_date <= end_date:
                    excluded.append(f"{post_date}\t{url}")
                    print(f"[{index}/{len(urls)}] 기간 밖 제외: {post_date} {url}")
                    continue
                if not text:
                    failures.append(url)
                    print(f"[{index}/{len(urls)}] 본문 텍스트 없음: {url}")
                    continue
                if REQUIRED_TEXT not in text:
                    excluded_keywords.append(url)
                    print(f"[{index}/{len(urls)}] '{REQUIRED_TEXT}' 미포함 제외: {url}")
                    continue
                blog_id, post_id = urlparse(url).path.strip("/").split("/")
                filename = output / f"{index:03d}_{blog_id}_{post_id}.txt"
                filename.write_text(text + "\n", encoding="utf-8")
                saved += 1
                saved_urls.append(f"{post_date}\t{url}\t{filename.name}")
                print(f"[{index}/{len(urls)}] 저장: {filename.name}")
            except TimeoutException:
                failures.append(url)
                print(f"[{index}/{len(urls)}] 본문 로딩 실패(비공개·삭제·접근 제한 또는 구조 변경): {url}")
            except WebDriverException as error:
                failures.append(url)
                print(f"[{index}/{len(urls)}] 브라우저 오류: {url} ({error.msg.splitlines()[0]})")
        (output / "saved_posts.tsv").write_text("date\turl\tfile\n" + "\n".join(saved_urls) + "\n", encoding="utf-8")
        if excluded:
            (output / "excluded_dates.txt").write_text("\n".join(excluded) + "\n", encoding="utf-8")
        if excluded_keywords:
            (output / "excluded_keywords.txt").write_text("\n".join(excluded_keywords) + "\n", encoding="utf-8")
        if failures:
            (output / "failed_urls.txt").write_text("\n".join(failures) + "\n", encoding="utf-8")
        print(f"\n발견 {len(urls)}건 / 텍스트 저장 {saved}건 / 기간 밖 {len(excluded)}건 / 키워드 미포함 {len(excluded_keywords)}건 / 실패 {len(failures)}건")
        print("검색 결과가 5회 연속 늘지 않아 탐색을 종료했습니다. 네이버가 노출하지 않은 결과는 포함되지 않습니다.")
        print(f"저장 폴더: {output}")
        return 0 if saved else 1
    except TimeoutException:
        print("검색 페이지를 불러오지 못했습니다. 검색 결과·네트워크·접근 제한을 확인해주세요.", file=sys.stderr)
        return 1
    except WebDriverException as error:
        print(f"Chrome 실행 또는 페이지 접근 오류: {error.msg}\nChrome 설치 및 네트워크 연결을 확인해주세요.", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"파일 저장 또는 실행 환경 오류: {error}", file=sys.stderr)
        return 1
    finally:
        if driver is not None:
            try:
                driver.quit()
            except WebDriverException:
                pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\n작업이 취소되었습니다. 이미 저장된 텍스트 파일은 유지됩니다.", file=sys.stderr)
        sys.exit(1)
