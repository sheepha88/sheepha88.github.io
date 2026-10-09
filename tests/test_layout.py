"""dist/ 를 빌드해 임시 서버로 띄운 뒤 세 폭 x 라이트/다크 레이아웃을 검증한다."""
import functools
import http.server
import re
import sys
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = Path(__file__).parent / "screenshots"
sys.path.insert(0, str(ROOT))

import build  # noqa: E402

WIDTHS = {"mobile": (390, 844), "tablet": (768, 1024), "desktop": (1440, 900)}
SCHEMES = ["light", "dark"]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def base_url():
    build.main()
    handler = functools.partial(_Quiet, directory=str(ROOT / "dist"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/"
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _open(browser, base_url, width, height, scheme, js=True):
    ctx = browser.new_context(viewport={"width": width, "height": height},
                              color_scheme=scheme, java_script_enabled=js)
    page = ctx.new_page()
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    return ctx, page


def _expand_all(page):
    page.evaluate("document.querySelectorAll('img').forEach(i => i.loading = 'eager')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)


@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("name", WIDTHS)
def test_no_horizontal_scroll_and_screenshots(browser, base_url, name, scheme):
    w, h = WIDTHS[name]
    ctx, page = _open(browser, base_url, w, h, scheme)
    SHOTS.mkdir(exist_ok=True)
    page.screenshot(path=str(SHOTS / f"{name}-{scheme}-closed.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "접힌 상태 가로 스크롤"
    _expand_all(page)
    page.screenshot(path=str(SHOTS / f"{name}-{scheme}-expanded.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "펼친 상태 가로 스크롤"
    ctx.close()


@pytest.mark.parametrize("name", WIDTHS)
def test_all_images_load(browser, base_url, name):
    w, h = WIDTHS[name]
    ctx, page = _open(browser, base_url, w, h, "light")
    _expand_all(page)
    broken = page.evaluate("""() => [...document.images]
        .filter(i => !i.closest('dialog'))
        .filter(i => !i.complete || i.naturalWidth === 0)
        .map(i => i.getAttribute('src'))""")
    assert broken == []
    missing_attrs = page.evaluate("""() => [...document.images]
        .filter(i => !i.closest('dialog') && (!i.getAttribute('width') || !i.getAttribute('height') || !i.alt))
        .map(i => i.getAttribute('src'))""")
    assert missing_attrs == [], "width/height/alt 누락"
    ctx.close()


@pytest.mark.parametrize("name", WIDTHS)
def test_coverflow_shows_one_large_card_and_navigates(browser, base_url, name):
    w, h = WIDTHS[name]
    ctx, page = _open(browser, base_url, w, h, "light")
    assert page.locator(".cf-item").count() == 3
    assert page.locator('.cf-item[data-pos="0"]').count() == 1
    assert page.locator(".cf-dots button").count() == 3
    center = page.locator('.cf-item[data-pos="0"]')
    assert center.bounding_box()["width"] > 200
    first = center.locator("figcaption").inner_text()
    page.locator(".cf-next").click()
    page.wait_for_timeout(500)
    second = page.locator('.cf-item[data-pos="0"] figcaption').inner_text()
    assert second != first
    page.locator(".cf-prev").click()
    page.wait_for_timeout(500)
    assert page.locator('.cf-item[data-pos="0"] figcaption').inner_text() == first
    page.locator(".cf-dots button").nth(2).click()
    page.wait_for_timeout(500)
    assert page.locator('.cf-dots button[aria-current="true"]').count() == 1
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    ctx.close()


def test_coverflow_lightbox_has_three(browser, base_url):
    ctx, page = _open(browser, base_url, 1440, 900, "light")
    page.locator('.cf-item[data-pos="0"] .zoom').click()
    assert page.locator(".lb-count").inner_text() == "1 / 3"
    ctx.close()


def test_anchor_targets_exist(browser, base_url):
    ctx, page = _open(browser, base_url, 1440, 900, "light")
    missing = page.evaluate("""() => [...document.querySelectorAll('a[href^="#"]')]
        .map(a => a.getAttribute('href').slice(1))
        .filter(id => id && !document.getElementById(id))""")
    assert missing == []
    ctx.close()


def test_content_present_without_js(browser, base_url):
    ctx, page = _open(browser, base_url, 390, 844, "light", js=False)
    assert page.locator("#p1 .slide").count() == 9
    assert page.locator("#p2 .slide").count() == 9
    assert page.locator("#p3 .slide").count() == 8
    assert page.locator("#p4 .case").count() == 0
    assert page.locator(".case").count() == 3
    assert page.locator("#career tbody tr").count() == 4
    assert page.locator(".cf-item").count() == 3
    ctx.close()


def test_no_phone_number_or_education(browser, base_url):
    ctx, page = _open(browser, base_url, 1440, 900, "light")
    text = page.content()
    assert not re.search(r"01\d[-.\s]?\d{3,4}[-.\s]?\d{4}", text), "전화번호 형식 문자열 발견"
    assert "학력" not in text and "고려대학교" not in text
    ctx.close()


def test_lightbox_navigation(browser, base_url):
    ctx, page = _open(browser, base_url, 1440, 900, "light")
    page.locator("#p1 .slide a").first.click()
    assert page.locator(".lb-count").inner_text() == "1 / 9"
    page.keyboard.press("ArrowRight")
    assert page.locator(".lb-count").inner_text() == "2 / 9"
    page.locator(".lb-next").click()
    assert page.locator(".lb-count").inner_text() == "3 / 9"
    ctx.close()
