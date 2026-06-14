import logging
import urllib.parse

from markupsafe import escape as _html_escape
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


def _sanitize_params(params: dict) -> dict:
    """B5: 对 params 中所有字符串值做 HTML 转义，防止 XSS 注入到渲染页面。"""
    return {k: str(_html_escape(v)) if isinstance(v, str) else v for k, v in params.items()}


async def generate_pdf(base_url: str, params: dict, output_path: str = None) -> bytes:
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
