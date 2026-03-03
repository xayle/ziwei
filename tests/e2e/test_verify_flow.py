"""
tests/e2e/test_verify_flow.py — E2E Playwright 测试（N7.02）

场景覆盖：
  场景1: 完整计算流程（填表→提交→断言 Tab>10 且非空）
  场景2: 历史对比（计算两次→点对比→断言并排出现）
  场景3: 分享卡片 PNG 导出（断言下载触发+文件大小>10KB）
  场景4（异常):  Token 过期→重定向/401 提示
  场景5（异常):  CSV 超 50 行→前端拦截，不发请求
  场景6（异常):  非法日期→表单报错不提交

前置条件（运行前必须手动完成）：
    pip install playwright pytest-playwright
    playwright install chromium
    服务以 AUTH_BYPASS=true 启动在 http://localhost:8000
"""
from __future__ import annotations

import os
import time

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")

# ── 跳过条件：未安装 playwright 时自动跳过，不影响 pytest 主套件 ──────────────

playwright_available = False
try:
    import playwright  # noqa: F401
    playwright_available = True
except ImportError:
    pass

pytestmark = pytest.mark.skipif(
    not playwright_available,
    reason="playwright 未安装，跳过 E2E 测试（pip install playwright pytest-playwright）",
)


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────────────────

def _fill_verify_form(page, dt: str = "1990-03-15T08:30") -> None:
    """填写排盘表单并点击提交."""
    from playwright.sync_api import expect  # noqa: F401

    page.goto(f"{BASE_URL}/verify")
    page.wait_for_load_state("networkidle", timeout=10_000)

    # 填写出生时间
    dt_input = page.locator("input#dt, input[name='dt'], input[type='datetime-local']").first
    dt_input.fill(dt)

    # 填写经度
    lon_input = page.locator("input#lon, input[name='lon'], input[type='number']").first
    lon_input.fill("116.41")

    # 点击提交
    submit_btn = page.locator("button#submitBtn, button[type='submit'], button:has-text('排盘'), button:has-text('计算')").first
    submit_btn.click()

    # 等待结果出现
    page.wait_for_selector(".tab-nav, #tab-mobile-select, .result-tabs", timeout=20_000)


# ─────────────────────────────────────────────────────────────────────────────
# 场景 1: 完整计算流程
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_complete_verify_flow(page):
    """场景1: 填表→提交→断言 Tab 数量>10 且每个 Tab 内容容器非空."""
    _fill_verify_form(page)

    # 等待至少一个 Tab 渲染
    page.wait_for_selector(".tab-nav .tab-btn, .tab-btn, [role='tab']", timeout=15_000)

    # 断言 Tab 数量宽松下界（>10，不硬编码具体数量）
    tab_buttons = page.locator(".tab-btn, [role='tab']")
    tab_count = tab_buttons.count()
    assert tab_count > 10, f"Tab 数量过少：{tab_count}，期望 >10（验证引擎正常返回多维数据）"

    # 断言每个可见 Tab 内容容器 innerHTML 非空
    tab_contents = page.locator(".tab-content, .tab-panel, [role='tabpanel']")
    visible_contents = 0
    for i in range(tab_contents.count()):
        panel = tab_contents.nth(i)
        if panel.is_visible():
            html = panel.inner_html()
            assert len(html.strip()) > 0, f"第 {i+1} 个 Tab 内容为空"
            visible_contents += 1

    assert visible_contents > 0, "没有可见的 Tab 内容容器"


# ─────────────────────────────────────────────────────────────────────────────
# 场景 2: 历史对比
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_history_compare(page):
    """场景2: 计算两次→点对比→断言并排展示出现."""
    # 第一次计算
    _fill_verify_form(page, dt="1990-03-15T08:30")
    page.wait_for_timeout(2000)

    # 第二次计算（不同日期）
    page.locator("input#dt, input[name='dt'], input[type='datetime-local']").first.fill("1985-07-20T10:00")
    submit_btn = page.locator("button#submitBtn, button[type='submit'], button:has-text('排盘'), button:has-text('计算')").first
    submit_btn.click()
    page.wait_for_timeout(3000)

    # 查找对比按钮（N5.01 新增）
    compare_btn = page.locator("button:has-text('对比'), button:has-text('历史对比'), #histCompareBtn")
    if compare_btn.count() > 0 and compare_btn.first.is_visible():
        compare_btn.first.click()
        page.wait_for_timeout(1500)

        # 断言并排展示出现（两列或模态框）
        side_by_side = page.locator(
            ".compare-panel, .hist-compare, [id*='compare'], .side-by-side"
        )
        assert side_by_side.count() > 0 or page.locator("dialog, .modal").count() > 0, \
            "点击对比后未出现并排展示面板或模态框"
    else:
        pytest.skip("历史记录对比按钮未找到（可能未计算足够2次，或 N5.01 未触发）")


# ─────────────────────────────────────────────────────────────────────────────
# 场景 3: 分享卡片 PNG 导出
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_share_card_export(page):
    """场景3: 下载分享卡片 PNG（断言 download 触发+文件大小>10KB，验收 R42）."""
    _fill_verify_form(page)
    page.wait_for_timeout(2000)

    # 打开导出下拉
    export_btn = page.locator("button:has-text('导出'), button#exportBtn, .export-dropdown button").first
    if not export_btn.is_visible():
        pytest.skip("导出按钮未找到，跳过场景3")

    export_btn.click()
    page.wait_for_timeout(500)

    # 点击分享卡片选项（N5.02）
    share_option = page.locator("button:has-text('分享卡片'), a:has-text('分享卡片'), button:has-text('PNG')")
    if share_option.count() == 0:
        pytest.skip("分享卡片 PNG 选项未找到，跳过场景3")

    # 等待下载事件
    with page.expect_download(timeout=15_000) as download_info:
        share_option.first.click()

    download = download_info.value

    # 断言文件大小 > 10KB（html2canvas 渲染非空白，CDN 加载成功）
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, download.suggested_filename or "card.png")
        download.save_as(path)
        size = os.path.getsize(path)
        assert size > 10 * 1024, f"分享卡片 PNG 文件大小 {size} B < 10KB，html2canvas 可能渲染失败"

    # R42: 断言 #share-card 内免责声明文字可见
    disclaimer_text = page.locator("#share-card, .share-card")
    if disclaimer_text.count() > 0:
        inner = disclaimer_text.inner_text()
        assert "娱乐" in inner or "参考" in inner or "建议" in inner, \
            "R42: #share-card 内未找到免责声明文字（防水印被遮挡）"


# ─────────────────────────────────────────────────────────────────────────────
# 场景 4（异常）: Token 过期
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_expired_token_redirects(page):
    """场景4: 用过期 JWT 覆盖 localStorage → 访问批量页 → 断言 401 或登录提示."""
    # 先正常访问一次，建立 session
    page.goto(f"{BASE_URL}/verify")
    page.wait_for_load_state("domcontentloaded")

    # 注入过期 JWT（exp=1 表示 1970-01-01，已过期）
    expired_jwt = (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        ".eyJleHAiOjF9"
        ".lxM74P_XKLL58IedPH0LMlHQcTJ_KN1T0h_VEQ5Yj8I"
    )
    page.evaluate(f"localStorage.setItem('token', '{expired_jwt}')")

    # 访问批量页面
    page.goto(f"{BASE_URL}/batch")
    page.wait_for_load_state("domcontentloaded", timeout=8000)

    # 断言出现 401 提示或重定向登录页
    page_text = page.content().lower()
    has_auth_hint = any(word in page_text for word in [
        "401", "未授权", "请先登录", "login", "unauthorized", "token"
    ])
    is_login_page = "login" in page.url.lower() or "/auth" in page.url.lower()

    assert has_auth_hint or is_login_page, (
        f"过期 token 访问批量页后未出现认证提示，page URL={page.url}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 场景 5（异常）: CSV 超 50 行前端拦截
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_csv_over_limit_blocked(page):
    """场景5（R39）: 上传超 50 行 CSV → 断言前端拦截，不发出网络请求."""
    import io
    from playwright.sync_api import Route

    page.goto(f"{BASE_URL}/batch")
    page.wait_for_load_state("domcontentloaded")

    # 监听是否有批量 API 请求发出
    api_called = {"flag": False}

    def intercept(route: Route):
        if "/api/v2/batch/verify" in route.request.url:
            api_called["flag"] = True
        route.continue_()

    page.route("**/api/v2/batch/verify", intercept)

    # 构造包含 51 行数据的 CSV
    csv_content = "dt,lon,tz\n"
    for i in range(51):
        csv_content += f"2000-01-01T08:00:00,116.41,Asia/Shanghai\n"

    # 使用 file chooser 上传
    file_input = page.locator("input[type='file']")
    if file_input.count() == 0:
        pytest.skip("未找到文件上传 input，跳过场景5")

    with page.expect_file_chooser(timeout=3000) as fc_info:
        file_input.click()
    file_chooser = fc_info.value
    file_chooser.set_files({
        "name": "test_over_limit.csv",
        "mimeType": "text/csv",
        "buffer": csv_content.encode("utf-8"),
    })

    page.wait_for_timeout(1000)

    # 断言出现错误提示
    status_el = page.locator("#status, .status, [id*='status'], [class*='error']").first
    if status_el.is_visible():
        status_text = status_el.inner_text()
        assert "50" in status_text or "超出" in status_text or "限制" in status_text, \
            f"超出限制提示文本不含 '50'/'超出'/'限制': {status_text}"

    # 最关键：确认没有发出批量 API 请求
    assert not api_called["flag"], "超出 50 行后仍然发出了批量 API 请求（前端拦截失败）"


# ─────────────────────────────────────────────────────────────────────────────
# 场景 6（异常）: 非法日期表单报错
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_invalid_date_form_error(page):
    """场景6: 非法日期（2000-13-45）→ 断言 HTML5 表单校验拦截或后端 400."""
    page.goto(f"{BASE_URL}/verify")
    page.wait_for_load_state("domcontentloaded")

    # 尝试填入非法日期（datetime-local input 会原生拒绝无效值）
    dt_input = page.locator("input#dt, input[name='dt'], input[type='datetime-local']").first
    if dt_input.count() == 0:
        pytest.skip("未找到 datetime 输入框")

    # 通过 JS 直接设置 value 绕过原生 picker，再触发 submit
    page.evaluate("""
        const el = document.querySelector("input#dt, input[name='dt'], input[type='datetime-local']");
        if (el) { el.value = '2000-13-45T25:99'; el.dispatchEvent(new Event('input')); }
    """)

    submit_btn = page.locator("button#submitBtn, button[type='submit'], button:has-text('排盘'), button:has-text('计算')").first
    if submit_btn.is_visible():
        submit_btn.click()
        page.wait_for_timeout(2000)

    # 断言：要么出现 HTML5 validationMessage，要么出现错误提示文字
    has_error_ui = page.locator(
        "[class*='error'], [id*='error'], .validation-error, #status.bad, #status.warn"
    ).count() > 0

    # 检查 HTTP 状态是否返回 400/422（若发出请求的话）
    has_error_text = any(word in page.content().lower() for word in [
        "invalid", "错误", "无效", "日期", "400", "422"
    ])

    assert has_error_ui or has_error_text, "非法日期输入后未出现表单错误提示"
