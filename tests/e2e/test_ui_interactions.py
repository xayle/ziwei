import pytest
from playwright.sync_api import Page, expect

# 需要安装: pip install pytest-playwright && playwright install

@pytest.mark.e2e
def test_front_page_load(page: Page):
    """测试系统首页加载是否存活"""
    page.goto("http://localhost:8000/static/ziwei.html")
    expect(page).to_have_title("紫微斗数 · 命盘推算")
    
    # 测试基础排盘表单是否存在
    expect(page.locator("#fy")).to_be_visible()
    expect(page.locator("#fm")).to_be_visible()
    
@pytest.mark.e2e
def test_basic_calc_flow(page: Page):
    """测试输入公历时间，点击排盘后的主要渲染流程"""
    page.goto("http://localhost:8000/static/ziwei.html")
    
    # 填充演示数据 (1995-5-26 14:30 男)
    page.fill("#fy", "1995")
    page.fill("#fm", "5")
    page.fill("#fd", "26")
    page.fill("#fh", "14")
    page.fill("#fmin", "30")
    page.select_option("#fgender", "男")
    
    # 点击排盘
    page.click("button.btn[onclick='go()']")
    
    # 等待分析结果区域显示
    result_panel = page.locator("#cr")
    result_panel.wait_for(state="visible", timeout=3000)
    
    # 验证五行局与基本盘面展示
    expect(page.locator("#ih")).to_contain_text("火六局")
    expect(page.locator(".pgrid").first).to_be_visible()

@pytest.mark.e2e
def test_tab_switching(page: Page):
    """验证排盘后，标签页切换是否正常"""
    page.goto("http://localhost:8000/static/ziwei.html?y=2000&m=4&d=1&h=8&min=0&g=%E5%A5%B3")
    
    # 点击“运势预测” Tab
    page.click("button:has-text('运势预测')")
    expect(page.locator("#tc-fc")).to_be_visible()
    
    # 点击“大运流月” Tab
    page.click("button:has-text('大运流月')")
    expect(page.locator("#tc-dy")).to_be_visible()

