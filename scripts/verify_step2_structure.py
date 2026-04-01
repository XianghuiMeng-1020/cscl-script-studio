#!/usr/bin/env python3
"""
深入验证Step 2表单结构
Deep verification of Step 2 form structure
"""
import os
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# 测试配置
BASE_URL = 'https://web-production-591d6.up.railway.app'
OUTPUT_DIR = Path(__file__).parent.parent / 'outputs' / 'step2_verification'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def setup_driver():
    """设置Chrome驱动"""
    print("正在启动Chrome浏览器...")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ Chrome浏览器启动成功")
        return driver
    except Exception as e:
        print(f"✗ 启动Chrome失败: {e}")
        sys.exit(1)

def take_screenshot(driver, name):
    """截取屏幕截图"""
    filepath = OUTPUT_DIR / f"{name}.png"
    driver.save_screenshot(str(filepath))
    print(f"  📸 截图: {filepath.name}")
    return str(filepath)

def login(driver):
    """登录系统"""
    print("\n[登录] 尝试登录系统...")
    try:
        # 检查是否有登录表单
        try:
            username_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            print("  发现登录表单,进行登录...")
            username_input.clear()
            username_input.send_keys("teacher_demo")
            
            password_input = driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys("Demo@12345")
            
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            time.sleep(3)
            print("  ✓ 登录成功")
            return True
        except TimeoutException:
            print("  ℹ 未发现登录表单,可能已登录或在Demo模式")
            return False
            
    except Exception as e:
        print(f"  ✗ 登录异常: {str(e)}")
        return False

def main():
    """主测试流程"""
    print("="*80)
    print("CSCL应用程序 - Step 2 表单结构深入验证")
    print("="*80)
    
    driver = setup_driver()
    
    try:
        # 步骤1: 访问教师页面
        print("\n[步骤1] 访问教师页面...")
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        take_screenshot(driver, "01_teacher_page")
        
        # 步骤1.5: 尝试登录(如果需要)
        login(driver)
        time.sleep(1)
        take_screenshot(driver, "01b_after_login")
        
        # 步骤2: 点击"快速体验 Demo"
        print("\n[步骤2] 点击'快速体验 Demo'...")
        try:
            demo_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '快速体验') or contains(text(), 'Demo')]"))
            )
            demo_button.click()
            time.sleep(2)
            take_screenshot(driver, "02_after_demo_click")
            print("  ✓ 成功点击Demo按钮")
        except Exception as e:
            print(f"  ✗ 点击Demo按钮失败: {e}")
            print("  ℹ 可能已经在主页面,继续...")
            take_screenshot(driver, "02_no_demo_button")
        
        # 步骤3: 点击"新建活动"
        print("\n[步骤3] 点击'新建活动'...")
        try:
            new_activity_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '新建活动') or contains(text(), 'New Activity')]"))
            )
            new_activity_btn.click()
            time.sleep(2)
            take_screenshot(driver, "03_step1_page")
            print("  ✓ 成功进入Step 1")
        except Exception as e:
            print(f"  ✗ 点击新建活动失败: {e}")
            take_screenshot(driver, "03_new_activity_error")
        
        # 步骤4: 点击"继续"进入Step 2
        print("\n[步骤4] 点击'继续'进入Step 2...")
        try:
            continue_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '继续') or contains(text(), 'Continue')]"))
            )
            continue_btn.click()
            time.sleep(2)
            take_screenshot(driver, "04_step2_page")
            print("  ✓ 成功进入Step 2")
        except Exception as e:
            print(f"  ✗ 点击继续按钮失败: {e}")
            take_screenshot(driver, "04_continue_error")
        
        # 步骤5: 深入检查Step 2表单结构
        print("\n[步骤5] 深入检查Step 2表单结构...")
        print("="*80)
        
        # 先滚动到页面顶部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        take_screenshot(driver, "05a_step2_top")
        
        # 5.1 检查是否存在id="specInitialIdea"的元素
        print("\n5.1 检查元素 id='specInitialIdea':")
        try:
            spec_initial_idea = driver.find_element(By.ID, "specInitialIdea")
            print(f"  ✓ 找到元素 id='specInitialIdea'")
            print(f"    - 标签名: {spec_initial_idea.tag_name}")
            print(f"    - 类型: {spec_initial_idea.get_attribute('type')}")
            print(f"    - 类名: {spec_initial_idea.get_attribute('class')}")
            print(f"    - 占位符: {spec_initial_idea.get_attribute('placeholder')}")
            print(f"    - 是否可见: {spec_initial_idea.is_displayed()}")
            print(f"    - 位置: {spec_initial_idea.location}")
            print(f"    - 大小: {spec_initial_idea.size}")
        except NoSuchElementException:
            print(f"  ✗ 未找到元素 id='specInitialIdea'")
        
        # 5.2 检查是否存在"课程名称"字段
        print("\n5.2 检查'课程名称'字段:")
        try:
            course_name_label = driver.find_element(By.XPATH, "//*[contains(text(), '课程名称')]")
            print(f"  ✓ 找到'课程名称'标签")
            print(f"    - 位置: {course_name_label.location}")
            
            # 查找课程名称输入框
            course_name_input = driver.find_element(By.ID, "specCourseName")
            print(f"  ✓ 找到课程名称输入框 id='specCourseName'")
            print(f"    - 位置: {course_name_input.location}")
        except NoSuchElementException as e:
            print(f"  ✗ 未找到课程名称相关元素: {e}")
        
        # 5.3 检查所有textarea元素
        print("\n5.3 检查所有textarea元素:")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        print(f"  找到 {len(textareas)} 个textarea元素:")
        for i, textarea in enumerate(textareas, 1):
            print(f"\n  Textarea #{i}:")
            print(f"    - ID: {textarea.get_attribute('id')}")
            print(f"    - Name: {textarea.get_attribute('name')}")
            print(f"    - 类名: {textarea.get_attribute('class')}")
            print(f"    - 占位符: {textarea.get_attribute('placeholder')}")
            print(f"    - 是否可见: {textarea.is_displayed()}")
            print(f"    - 位置: {textarea.location}")
            print(f"    - 大小: {textarea.size}")
        
        # 5.4 搜索包含"初步想法"或"initial idea"的文本
        print("\n5.4 搜索包含'初步想法'或'initial idea'的文本:")
        try:
            initial_idea_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '初步想法') or contains(text(), 'initial idea') or contains(text(), 'Initial Idea')]")
            if initial_idea_elements:
                print(f"  ✓ 找到 {len(initial_idea_elements)} 个包含'初步想法'的元素:")
                for i, elem in enumerate(initial_idea_elements, 1):
                    print(f"\n  元素 #{i}:")
                    print(f"    - 标签名: {elem.tag_name}")
                    print(f"    - 文本内容: {elem.text}")
                    print(f"    - 位置: {elem.location}")
            else:
                print(f"  ✗ 未找到包含'初步想法'的元素")
        except Exception as e:
            print(f"  ✗ 搜索失败: {e}")
        
        # 5.5 获取Step 2表单的完整HTML结构
        print("\n5.5 获取Step 2表单的HTML结构:")
        try:
            # 获取整个页面的HTML
            page_html = driver.page_source
            
            # 保存完整页面HTML到文件
            html_file = OUTPUT_DIR / "step2_full_page.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page_html)
            print(f"  ✓ 完整页面HTML已保存到: {html_file.name}")
            
            # 尝试获取包含specInitialIdea的表单
            try:
                initial_idea_field = driver.find_element(By.ID, "specInitialIdea")
                # 获取父表单
                form_element = initial_idea_field.find_element(By.XPATH, "./ancestor::form")
                form_html = form_element.get_attribute('outerHTML')
                
                # 保存表单HTML到文件
                form_file = OUTPUT_DIR / "step2_spec_form.html"
                with open(form_file, 'w', encoding='utf-8') as f:
                    f.write(form_html)
                print(f"  ✓ Step 2表单HTML已保存到: {form_file.name}")
                
                # 打印前500个字符
                print(f"\n  表单HTML前500个字符:")
                print(f"  {form_html[:500]}...")
            except Exception as e2:
                print(f"  ⚠ 获取specInitialIdea表单失败: {e2}")
        except Exception as e:
            print(f"  ✗ 获取HTML失败: {e}")
        
        # 5.6 检查所有输入字段的顺序
        print("\n5.6 检查所有输入字段的顺序:")
        all_inputs = driver.find_elements(By.XPATH, "//input[@type='text'] | //textarea | //select")
        print(f"  找到 {len(all_inputs)} 个输入字段:")
        for i, input_elem in enumerate(all_inputs, 1):
            print(f"\n  字段 #{i}:")
            print(f"    - 标签名: {input_elem.tag_name}")
            print(f"    - ID: {input_elem.get_attribute('id')}")
            print(f"    - Name: {input_elem.get_attribute('name')}")
            print(f"    - 占位符: {input_elem.get_attribute('placeholder')}")
            print(f"    - Y坐标: {input_elem.location['y']}")
        
        # 最终截图
        take_screenshot(driver, "05_final_step2_view")
        
        print("\n" + "="*80)
        print("验证完成！")
        print("="*80)
        print(f"\n所有截图和HTML文件已保存到: {OUTPUT_DIR}")
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        take_screenshot(driver, "error_final")
    
    finally:
        print("\n正在关闭浏览器...")
        time.sleep(2)
        driver.quit()
        print("✓ 浏览器已关闭")

if __name__ == "__main__":
    main()
