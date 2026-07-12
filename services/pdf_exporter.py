import logging
from typing import TYPE_CHECKING
import urllib.parse

from markupsafe import escape as _html_escape
from playwright.async_api import async_playwright

if TYPE_CHECKING:
    from app.schemas.fusheng_report import FushengReportPdfRequest

logger = logging.getLogger(__name__)


def _sanitize_params(params: dict) -> dict:
    """B5: 对 params 中所有字符串值做 HTML 转义，防止 XSS 注入到渲染页面。"""
    return {k: str(_html_escape(v)) if isinstance(v, str) else v for k, v in params.items()}


async def generate_pdf(base_url: str, params: dict, output_path: str | None = None) -> bytes:
    """
    使用 Playwright 后端渲染网页，并导出为 A4 尺寸的多页 PDF。
    params 包含: year, month, day, hour, minute, gender 等用于排盘参数
    """
    params = _sanitize_params(params)  # B5: XSS 净化
    query_str = urllib.parse.urlencode(params)
    target_url = f"{base_url}/?{query_str}"

    logger.info(f"PDF 渲染目标: {target_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 用高分屏配置启动上下文，保证打印字体清晰
        context = await browser.new_context(device_scale_factor=2)
        page = await context.new_page()

        # 页面加载与等待：我们要依靠页面执行排盘计算渲染 DOM，因此等 networkidle
        try:
            await page.goto(target_url, wait_until="networkidle", timeout=15000)
            # 等待命盘被渲染（以 #cr 为标志）
            await page.wait_for_selector("#cr", state="visible", timeout=5000)

            # 给一些时间让动画稳定、SVG 被完全绘制
            await page.wait_for_timeout(1000)

            # 扩展：如果是带图的高级版，可注入版权水印节点
            await page.evaluate("""
                const watermark = document.createElement("div");
                watermark.style.position = "fixed";
                watermark.style.bottom = "10px";
                watermark.style.right = "20px";
                watermark.style.color = "#999";
                watermark.style.fontSize = "10px";
                watermark.style.zIndex = "9999";
                watermark.innerText = "© BaZi Report 内部专家审核版 - Auto Generated";
                document.body.appendChild(watermark);
            """)

            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "15mm", "bottom": "15mm", "left": "12mm", "right": "12mm"},
            )
            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF 渲染失败: {e}")
            raise
        finally:
            await browser.close()


async def render_html_to_pdf(html: str) -> bytes:
    """将静态 HTML 渲染为 A4 PDF（浮生报告等服务端导出）。"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(device_scale_factor=2)
        page = await context.new_page()
        try:
            await page.set_content(html, wait_until="load", timeout=20000)
            await page.wait_for_timeout(500)
            return await page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"},
            )
        except Exception as e:
            logger.error(f"HTML PDF 渲染失败: {e}")
            raise
        finally:
            await browser.close()


def _case_to_fusheng_request(case) -> "FushengReportPdfRequest":
    from app.schemas.fusheng_report import FushengReportPdfRequest

    gender_raw = (case.gender or "male").lower()
    gender = "female" if gender_raw in {"female", "女", "f"} else "male"
    birth_dt = case.birth_dt_local
    if len(birth_dt) == 16:
        birth_dt = f"{birth_dt}:00"
    return FushengReportPdfRequest(
        label=case.name or "命盘",
        birth_dt=birth_dt,
        lon=float(case.lon or 116.41),
        tz=case.tz or "Asia/Shanghai",
        gender=gender,
        solar_time_enabled=bool(getattr(case, "solar_time_enabled", False)),
        city_name=case.city or "",
        calendar_mode=getattr(case, "calendar_mode", "gregorian") or "gregorian",
        is_leap_month=bool(getattr(case, "is_leap_month", False)),
        notes=case.notes or "",
        year_divide=case.year_divide,
        day_divide=case.day_divide,
        zi_day_rule=case.zi_day_rule,
    )


async def generate_case_pdf(case, snapshot=None) -> bytes:
    """从 Case 记录生成 PDF（浮生报告管线，不依赖前端 URL）。"""
    from services.fusheng_report_service import build_fusheng_report_payload, render_fusheng_report_html

    req = _case_to_fusheng_request(case)
    payload = await build_fusheng_report_payload(req)
    html = render_fusheng_report_html(payload)
    return await render_html_to_pdf(html)


async def generate_share_card(case, snapshot=None) -> bytes:
    """生成分享卡片 PNG（精简 HTML 截图）。"""
    from services.fusheng_report_service import build_fusheng_report_payload

    req = _case_to_fusheng_request(case)
    payload = await build_fusheng_report_payload(req)
    bazi = payload.get("bazi") or {}
    ziwei = payload.get("ziwei") or {}
    geju = bazi.get("geju") or {}
    label = payload.get("meta", {}).get("label", "命盘")
    geju_line = geju.get("geju_name", "—")
    if geju.get("recorded_geju") and geju.get("recorded_geju") != geju.get("geju_name"):
        geju_line = f"{geju.get('geju_name')}（古籍：{geju.get('recorded_geju')}）"
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
    <style>body{{font-family:sans-serif;width:400px;padding:24px;background:#faf6ef;color:#2b2118}}
    h1{{font-size:18px;margin:0 0 8px}}p{{margin:4px 0;font-size:13px}}.meta{{color:#7a5c3a}}</style></head>
    <body><h1>{_html_escape(label)} · 命理档案卡</h1>
    <p>八字格局：{_html_escape(geju_line)}</p>
    <p>紫微：{_html_escape(ziwei.get('life_palace_gz') or '—')} · {_html_escape(ziwei.get('wuxing_ju_name') or '—')}</p>
    <p class="meta">{_html_escape((bazi.get('bazi_summary') or ziwei.get('summary') or '命理档案已生成')[:120])}</p>
    </body></html>"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 400, "height": 280})
        try:
            await page.set_content(html, wait_until="load", timeout=15000)
            return await page.screenshot(type="png")
        finally:
            await browser.close()
