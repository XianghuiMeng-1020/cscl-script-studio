#!/usr/bin/env python3
"""
检查页面结构 - 查找初步想法输入框
"""
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = 'https://web-production-591d6.up.railway.app'
OUTPUT_DIR = Path(__file__).parent.parent / 'outputs' / 'test_results'
USERNAME = 'teacher_demo'
PASSWORD = 'Demo@12345'

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def main():
    driver = setup_driver()
    
    try:
        # 登录
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        
        try:
            username_input = driver.find_element(By.NAME, "username")
            username_input.send_keys(USERNAME)
            password_input = driver.find_element(By.NAME, "password")
            password_input.send_keys(PASSWORD)
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            time.sleep(3)
        except:
            pass
        
        # 进入新建活动
        new_activity_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Create New Project')]"))
        )
        new_activity_btn.click()
        time.sleep(2)
        
        # 点击继续到Step 2
        continue_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Continue')]"))
        )
        continue_btn.click()
        time.sleep(2)
        
        # 滚动到页面顶部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        driver.save_screenshot(str(OUTPUT_DIR / "step2_top.png"))
        print("截图已保存: step2_top.png")
        
        # 查找所有textarea
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        print(f"\n找到 {len(textareas)} 个textarea:")
        for i, ta in enumerate(textareas):
            print(f"\nTextarea {i+1}:")
            print(f"  ID: {ta.get_attribute('id')}")
            print(f"  Name: {ta.get_attribute('name')}")
            print(f"  Placeholder: {ta.get_attribute('placeholder')}")
            print(f"  位置: Y={ta.location['y']}px")
            print(f"  可见: {ta.is_displayed()}")
            
            # 获取前面的label
            try:
                parent = ta.find_element(By.XPATH, "..")
                label = parent.find_element(By.XPATH, "preceding-sibling::label | ../preceding-sibling::label")
                print(f"  Label: {label.text}")
            except:
                pass
        
        # 搜索页面源码
        page_source = driver.page_source
        print("\n搜索关键词:")
        keywords = ["initial", "想法", "idea", "thought"]
        for keyword in keywords:
            if keyword in page_source.lower():
                print(f"  ✓ 找到: {keyword}")
                # 找到关键词附近的内容
                idx = page_source.lower().find(keyword)
                context = page_source[max(0, idx-100):idx+100]
                print(f"    上下文: ...{context}...")
            else:
                print(f"  ✗ 未找到: {keyword}")
        
        print("\n按Enter继续...")
        input()
        
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
