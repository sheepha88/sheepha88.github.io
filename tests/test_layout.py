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
    page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
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


@pytest.mark.parametrize("name", ["mobile", "tablet"])
def test_collage_stacks_without_overlap_on_small_screens(browser, base_url, name):
    w, h = WIDTHS[name]
    ctx, page = _open(browser, base_url, w, h, "light")
    boxes = page.evaluate("""() => [...document.querySelectorAll('.collage-product figure')].map(f => {
        const r = f.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom];
    })""")
    assert len(boxes) == 4
    for b in boxes:
        assert b[3] - b[1] > 100 and b[2] - b[0] > 100, f"콜라주 이미지가 너무 작음: {b}"
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, c = boxes[i], boxes[j]
            overlap = min(a[2], c[2]) - max(a[0], c[0]) > 1 and min(a[3], c[3]) - max(a[1], c[1]) > 1
            assert not overlap, f"겹침: {i} / {j}"
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
    assert page.locator("#p4 details").count() == 0
    assert page.locator("#career tbody tr").count() == 4
    ctx.close()


def test_no_phone_number_or_education(browser, base_url):
    ctx, page = _open(browser, base_url, 1440, 900, "light")
    text = page.content()
    assert not re.search(r"01\d[-.\s]?\d{3,4}[-.\s]?\d{4}", text), "전화번호 형식 문자열 발견"
    assert "학력" not in text and "고려대학교" not in text
    ctx.close()


def test_lightbox_navigation(browser, base_url):
    ctx, page = _open(browser, base_url, 1440, 900, "light")
    page.evaluate("document.querySelector('#p1 details').open = true")
    page.locator("#p1 .slide a").first.click()
    assert page.locator(".lb-count").inner_text() == "1 / 9"
    page.keyboard.press("ArrowRight")
    assert page.locator(".lb-count").inner_text() == "2 / 9"
    page.locator(".lb-next").click()
    assert page.locator(".lb-count").inner_text() == "3 / 9"
    ctx.close()
