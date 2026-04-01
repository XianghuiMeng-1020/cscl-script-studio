#!/usr/bin/env python3
"""
分析页面结构,找出正确的选择器
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

BASE_URL = "https://web-production-591d6.up.railway.app"
USERNAME = "teacher_demo"
PASSWORD = "Demo@12345"

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20)

try:
    # 登录
    print("登录中...")
    driver.get(f"{BASE_URL}/teacher")
    time.sleep(2)
    
    username_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[name='username']"))
    )
    username_input.send_keys(USERNAME)
    
    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    password_input.send_keys(PASSWORD)
    
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()
    
    time.sleep(3)
    print("✓ 登录成功\n")
    
    # 分析侧边栏
    print("="*80)
    print("分析侧边栏结构")
    print("="*80)
    
    # 查找所有可能的侧边栏元素
    possible_sidebars = []
    
    # 尝试不同的选择器
    selectors = [
        "aside",
        "nav",
        "[class*='sidebar']",
        "[class*='Sidebar']",
        "[class*='side-bar']",
        "[class*='navigation']",
        "[class*='Navigation']",
        "[class*='menu']",
        "[class*='Menu']",
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"\n找到 {len(elements)} 个元素匹配选择器: {selector}")
                for i, elem in enumerate(elements):
                    print(f"  元素 {i+1}:")
                    print(f"    标签: {elem.tag_name}")
                    print(f"    类名: {elem.get_attribute('class')}")
                    print(f"    ID: {elem.get_attribute('id')}")
                    
                    # 查找其中的链接
                    links = elem.find_elements(By.TAG_NAME, "a")
                    if links:
                        print(f"    包含 {len(links)} 个链接:")
                        for link in links[:5]:  # 只显示前5个
                            print(f"      - 文本: '{link.text}' | href: {link.get_attribute('href')}")
                    
                    # 查找按钮
                    buttons = elem.find_elements(By.TAG_NAME, "button")
                    if buttons:
                        print(f"    包含 {len(buttons)} 个按钮:")
                        for btn in buttons[:5]:
                            print(f"      - 文本: '{btn.text}'")
        except Exception as e:
            pass
    
    # 查找所有链接
    print("\n" + "="*80)
    print("所有可见链接")
    print("="*80)
    all_links = driver.find_elements(By.TAG_NAME, "a")
    print(f"\n找到 {len(all_links)} 个链接:")
    for i, link in enumerate(all_links[:20]):  # 只显示前20个
        if link.is_displayed():
            print(f"{i+1}. 文本: '{link.text}' | href: {link.get_attribute('href')}")
    
    # 查找所有按钮
    print("\n" + "="*80)
    print("所有可见按钮")
    print("="*80)
    all_buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"\n找到 {len(all_buttons)} 个按钮:")
    for i, btn in enumerate(all_buttons[:20]):
        if btn.is_displayed():
            print(f"{i+1}. 文本: '{btn.text}' | 类名: {btn.get_attribute('class')}")
    
    # 保存页面源代码
    print("\n" + "="*80)
    print("保存页面源代码")
    print("="*80)
    with open("outputs/comprehensive_test_v2/page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("✓ 页面源代码已保存到: outputs/comprehensive_test_v2/page_source.html")
    
finally:
    driver.quit()
    print("\n✓ 分析完成")
