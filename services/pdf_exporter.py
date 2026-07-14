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


async def render_html_to_png(html: str, *, width: int = 400, height: int = 280) -> bytes:
    """Render static HTML to PNG screenshot."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.set_content(html, wait_until="load", timeout=15000)
            await page.wait_for_timeout(300)
            return await page.screenshot(type="png")
        except Exception as e:
            logger.error(f"HTML PNG 渲染失败: {e}")
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
        birth_time_precision=getattr(case, "birth_time_precision", "exact") or "exact",
        late_zishi=getattr(case, "late_zishi", True),
    )


async def generate_case_pdf(case, snapshot=None) -> bytes:
    """从 Case 记录生成 PDF（浮生报告管线，不依赖前端 URL）。"""
    from services.fusheng_report_service import build_fusheng_report_payload, render_fusheng_report_html

    req = _case_to_fusheng_request(case)
    payload = await build_fusheng_report_payload(req)
    html = render_fusheng_report_html(payload)
    return await render_html_to_pdf(html)


# 分享卡布局（T097 / BE-GTM-11）
SHARE_CARD_LAYOUT_DEFAULT = "default"
SHARE_CARD_LAYOUT_DOUYIN = "douyin"
SHARE_CARD_LAYOUTS = frozenset({SHARE_CARD_LAYOUT_DEFAULT, SHARE_CARD_LAYOUT_DOUYIN})
DOUYIN_CARD_WIDTH = 1080
DOUYIN_CARD_HEIGHT = 1920  # 9:16


def render_douyin_share_card_html(
    *,
    brand: str = "浮生",
    volume_title: str,
    fact_lines: list[str],
    geju_line: str = "",
    disclaimer: str,
    label: str = "",
) -> str:
    """T097：抖音竖版 9:16 分享卡 HTML（纸面 + 卷名 + 事实句）。"""
    items = "".join(f"<li>{_html_escape(line)}</li>" for line in fact_lines[:4] if line)
    if not items:
        items = "<li>命盘事实已就绪，展开六卷可读细节。</li>"
    geju_block = f'<p class="geju">格局 · {_html_escape(geju_line)}</p>' if geju_line else ""
    label_block = f'<p class="label">{_html_escape(label)}</p>' if label else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<style>
  html, body {{ margin: 0; padding: 0; }}
  body {{
    width: {DOUYIN_CARD_WIDTH}px;
    height: {DOUYIN_CARD_HEIGHT}px;
    box-sizing: border-box;
    padding: 96px 72px 80px;
    display: flex;
    flex-direction: column;
    color: #1a1410;
    background:
      radial-gradient(ellipse 90% 55% at 50% -5%, rgba(184,137,77,0.16), transparent 55%),
      linear-gradient(180deg, #f7f1e8 0%, #f5f0e6 45%, #efe6d6 100%);
    font-family: "Songti SC", "Noto Serif SC", "Source Han Serif SC", serif;
  }}
  .brand {{
    font-size: 72px;
    letter-spacing: 0.28em;
    margin: 0;
    font-weight: 600;
  }}
  .tag {{
    margin: 18px 0 0;
    font-size: 28px;
    letter-spacing: 0.18em;
    color: #6b5d4f;
  }}
  .volume {{
    margin: 120px 0 0;
    font-size: 56px;
    letter-spacing: 0.12em;
    border-left: 6px solid #8b3a2a;
    padding-left: 28px;
    line-height: 1.35;
  }}
  .geju {{
    margin: 36px 0 0;
    font-size: 30px;
    color: #8b5e34;
    letter-spacing: 0.06em;
  }}
  .label {{
    margin: 16px 0 0;
    font-size: 26px;
    color: #9a8b7a;
  }}
  ul {{
    list-style: none;
    margin: 72px 0 0;
    padding: 0;
    flex: 1;
  }}
  li {{
    margin: 0 0 28px;
    font-size: 36px;
    line-height: 1.55;
    letter-spacing: 0.04em;
  }}
  li::before {{
    content: "·";
    color: #b8894d;
    margin-right: 14px;
  }}
  .disclaimer {{
    margin-top: auto;
    padding-top: 40px;
    border-top: 1px solid #d4c4a8;
    font-size: 22px;
    line-height: 1.5;
    color: #9a8b7a;
    letter-spacing: 0.04em;
  }}
</style></head>
<body>
  <p class="brand">{_html_escape(brand)}</p>
  <p class="tag">人生六卷 · 命书可读</p>
  <h1 class="volume">{_html_escape(volume_title)}</h1>
  {geju_block}
  {label_block}
  <ul>{items}</ul>
  <p class="disclaimer">{_html_escape(disclaimer)}</p>
</body></html>"""


async def generate_share_card(
    case,
    snapshot=None,
    *,
    layout: str = SHARE_CARD_LAYOUT_DEFAULT,
) -> bytes:
    """生成分享卡片 PNG（精简 HTML 截图）。

    layout:
      - default: 400×280 横卡
      - douyin: 1080×1920（9:16）竖版卡（T097 / BE-GTM-11）
    """
    from app.schemas.life_volume import LIFE_VOLUME_LABELS
    from services.content_policy import default_disclaimer_block
    from services.fusheng_report_service import build_fusheng_report_payload
    from services.life_snippets_service import build_hooks_from_bazi

    layout_key = (layout or SHARE_CARD_LAYOUT_DEFAULT).strip().lower()
    if layout_key not in SHARE_CARD_LAYOUTS:
        layout_key = SHARE_CARD_LAYOUT_DEFAULT

    req = _case_to_fusheng_request(case)
    payload = await build_fusheng_report_payload(req)
    bazi = payload.get("bazi") or {}
    ziwei = payload.get("ziwei") or {}
    geju = bazi.get("geju") or {}
    label = payload.get("meta", {}).get("label", "命盘")
    geju_line = geju.get("geju_name", "—")
    if geju.get("recorded_geju") and geju.get("recorded_geju") != geju.get("geju_name"):
        geju_line = f"{geju.get('geju_name')}（古籍：{geju.get('recorded_geju')}）"

    if layout_key == SHARE_CARD_LAYOUT_DOUYIN:
        hooks = build_hooks_from_bazi(bazi, limit=3)
        fact_lines = [h.text for h in hooks if h.text]
        disclaimer = str(default_disclaimer_block().get("text") or "")
        if len(disclaimer) > 80:
            disclaimer = disclaimer[:79] + "…"
        html = render_douyin_share_card_html(
            brand="浮生",
            volume_title=LIFE_VOLUME_LABELS.get("vol1", "卷一·命之根"),
            fact_lines=fact_lines,
            geju_line=str(geju_line or ""),
            disclaimer=disclaimer or "传统文化与自我认知参考，非命运断言。",
            label=str(label or ""),
        )
        return await render_html_to_png(html, width=DOUYIN_CARD_WIDTH, height=DOUYIN_CARD_HEIGHT)

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
    <style>body{{font-family:sans-serif;width:400px;padding:24px;background:#faf6ef;color:#2b2118}}
    h1{{font-size:18px;margin:0 0 8px}}p{{margin:4px 0;font-size:13px}}.meta{{color:#7a5c3a}}</style></head>
    <body><h1>{_html_escape(label)} · 命理档案卡</h1>
    <p>八字格局：{_html_escape(geju_line)}</p>
    <p>紫微：{_html_escape(ziwei.get('life_palace_gz') or '—')} · {_html_escape(ziwei.get('wuxing_ju_name') or '—')}</p>
    <p class="meta">{_html_escape((bazi.get('bazi_summary') or ziwei.get('summary') or '命理档案已生成')[:120])}</p>
    </body></html>"""
    return await render_html_to_png(html, width=400, height=280)


async def generate_relation_share_card(payload: dict) -> bytes:
    """Generate relation-compat share card PNG from API response dict."""
    from services.relation_pdf_service import render_relation_share_card_html

    html = render_relation_share_card_html(payload)
    return await render_html_to_png(html)
