#!/usr/bin/env python3
"""
测试CSCL剩余问题 - 使用真实登录
Test remaining CSCL issues with real login
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
OUTPUT_DIR = Path(__file__).parent.parent / 'outputs' / 'test_results'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 登录凭据
USERNAME = 'teacher_demo'
PASSWORD = 'Demo@12345'

def setup_driver():
    """设置Chrome驱动"""
    print("正在启动Chrome浏览器...")
    chrome_options = Options()
    # 不使用headless模式，以便观察测试过程
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

def take_screenshot(driver, name):
    """截取屏幕截图"""
    filepath = OUTPUT_DIR / f"{name}.png"
    driver.save_screenshot(str(filepath))
    print(f"  📸 截图已保存: {filepath}")
    return str(filepath)

def login(driver):
    """登录系统"""
    print("\n[登录] 尝试登录系统...")
    try:
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        
        take_screenshot(driver, "login_01_page")
        
        # 查找用户名输入框
        username_input = None
        try:
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
        except:
            try:
                username_input = driver.find_element(By.ID, "username")
            except:
                try:
                    username_input = driver.find_element(By.XPATH, "//input[@type='text' or @type='email']")
                except:
                    pass
        
        if not username_input:
            print("  ⚠️ 未找到用户名输入框，可能已经登录或页面结构不同")
            # 检查是否已经在教师界面
            if "teacher" in driver.current_url or driver.find_elements(By.CLASS_NAME, "sidebar"):
                print("  ✓ 已经在教师界面")
                return True
            return False
        
        # 输入用户名
        username_input.clear()
        username_input.send_keys(USERNAME)
        print(f"  ✓ 输入用户名: {USERNAME}")
        
        # 查找密码输入框
        password_input = driver.find_element(By.NAME, "password")
        password_input.clear()
        password_input.send_keys(PASSWORD)
        print(f"  ✓ 输入密码")
        
        take_screenshot(driver, "login_02_filled")
        
        # 查找并点击登录按钮
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        print("  ✓ 点击登录按钮")
        
        # 等待登录完成
        time.sleep(3)
        take_screenshot(driver, "login_03_after")
        
        # 检查是否登录成功
        if driver.find_elements(By.CLASS_NAME, "sidebar"):
            print("  ✓ 登录成功！")
            return True
        else:
            print("  ✗ 登录失败")
            return False
            
    except Exception as e:
        print(f"  ✗ 登录异常: {str(e)}")
        take_screenshot(driver, "login_error")
        import traceback
        traceback.print_exc()
        return False

def test_issue_2_checkbox(driver):
    """测试Issue #2: 步骤1中"不提取文字"复选框默认勾选"""
    print("\n[Issue #2] 测试'不提取文字'复选框...")
    try:
        # 点击"新建活动"
        new_activity_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '新建活动') or contains(text(), 'New Activity')]"))
        )
        new_activity_btn.click()
        print("  ✓ 点击'新建活动'")
        time.sleep(2)
        
        take_screenshot(driver, "issue2_01_step1")
        
        # 查找"不提取文字"复选框
        try:
            checkbox = driver.find_element(By.ID, "no-extract-text")
            is_checked = checkbox.is_selected()
            
            print(f"  {'✓' if is_checked else '✗'} 复选框状态: {'已勾选' if is_checked else '未勾选'}")
            take_screenshot(driver, "issue2_02_checkbox")
            return is_checked
        except NoSuchElementException:
            print("  ✗ 未找到'不提取文字'复选框")
            return False
            
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        take_screenshot(driver, "issue2_error")
        return False

def test_issue_3_uploaded_files(driver):
    """测试Issue #3: 步骤1中"已上传的文件"区域"""
    print("\n[Issue #3] 测试'已上传的文件'区域...")
    try:
        # 应该已经在步骤1
        take_screenshot(driver, "issue3_01_step1")
        
        # 查找"已上传的文件"区域
        try:
            uploaded_section = driver.find_element(By.ID, "uploaded-files-list")
            is_visible = uploaded_section.is_displayed()
            
            print(f"  {'✓' if is_visible else '✗'} '已上传的文件'区域: {'可见' if is_visible else '不可见'}")
            take_screenshot(driver, "issue3_02_files_list")
            return is_visible
        except NoSuchElementException:
            print("  ✗ 未找到'已上传的文件'区域")
            return False
            
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        take_screenshot(driver, "issue3_error")
        return False

def test_issue_14_initial_idea(driver):
    """测试Issue #14: 步骤2顶部的"初步想法"输入框"""
    print("\n[Issue #14] 测试'初步想法'输入框...")
    try:
        # 点击"继续"进入步骤2
        continue_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '继续') or contains(text(), 'Continue')]"))
        )
        continue_btn.click()
        print("  ✓ 点击'继续'进入步骤2")
        time.sleep(2)
        
        take_screenshot(driver, "issue14_01_step2")
        
        # 查找"初步想法"输入框
        try:
            initial_idea = driver.find_element(By.ID, "initial-idea")
            is_visible = initial_idea.is_displayed()
            
            # 检查标签文本
            page_source = driver.page_source
            has_label = "对本次活动有什么初步想法" in page_source or "initial idea" in page_source.lower()
            
            print(f"  {'✓' if is_visible else '✗'} 输入框: {'可见' if is_visible else '不可见'}")
            print(f"  {'✓' if has_label else '✗'} 标签文本: {'存在' if has_label else '不存在'}")
            
            take_screenshot(driver, "issue14_02_initial_idea")
            return is_visible and has_label
        except NoSuchElementException:
            print("  ✗ 未找到'初步想法'输入框")
            return False
            
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        take_screenshot(driver, "issue14_error")
        return False

def test_issue_8_output_tabs(driver):
    """测试Issue #8: 步骤4预览有3个标签页"""
    print("\n[Issue #8] 测试输出材料的3个标签页...")
    print("  ⚠️ 此测试需要完整填写表单并生成，暂时跳过")
    return None

def test_issue_13_edit_duplicate(driver):
    """测试Issue #13: 活动项目有编辑和复制按钮"""
    print("\n[Issue #13] 测试活动项目的编辑和复制按钮...")
    try:
        # 导航回主页
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        
        # 查找并点击"活动项目"
        activity_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '活动项目') or contains(text(), 'Activity Projects')]"))
        )
        activity_link.click()
        print("  ✓ 点击'活动项目'")
        time.sleep(2)
        
        take_screenshot(driver, "issue13_01_projects")
        
        # 检查页面源码中是否有编辑和复制按钮
        page_source = driver.page_source
        has_edit = "Edit" in page_source or "编辑" in page_source
        has_duplicate = "Duplicate" in page_source or "复制" in page_source
        
        print(f"  {'✓' if has_edit else '✗'} 编辑按钮: {'存在' if has_edit else '不存在'}")
        print(f"  {'✓' if has_duplicate else '✗'} 复制按钮: {'存在' if has_duplicate else '不存在'}")
        
        take_screenshot(driver, "issue13_02_buttons")
        return has_edit and has_duplicate
        
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        take_screenshot(driver, "issue13_error")
        return False

def test_issue_1_file_upload(driver):
    """测试Issue #1: 文件上传不需要选择课程/课时"""
    print("\n[Issue #1] 测试文件上传（无material_level单选）...")
    try:
        # 回到新建活动页面
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        
        new_activity_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '新建活动') or contains(text(), 'New Activity')]"))
        )
        new_activity_btn.click()
        time.sleep(2)
        
        take_screenshot(driver, "issue1_01_upload")
        
        # 检查是否存在material_level单选框
        page_source = driver.page_source
        has_material_level = "material_level" in page_source or "material-level" in page_source
        
        print(f"  {'✗' if has_material_level else '✓'} material_level单选: {'存在（不应该）' if has_material_level else '不存在（正确）'}")
        
        take_screenshot(driver, "issue1_02_no_radio")
        return not has_material_level
        
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        take_screenshot(driver, "issue1_error")
        return False

def main():
    """主测试流程"""
    print("="*80)
    print("CSCL应用程序 - 剩余问题验证测试（真实登录）")
    print("="*80)
    print(f"测试URL: {BASE_URL}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"登录凭据: {USERNAME} / {PASSWORD}")
    print("="*80)
    
    driver = setup_driver()
    results = {}
    
    try:
        # 登录
        if not login(driver):
            print("\n✗ 登录失败，无法继续测试")
            return
        
        # 测试各个问题
        results['Issue #2'] = test_issue_2_checkbox(driver)
        results['Issue #3'] = test_issue_3_uploaded_files(driver)
        results['Issue #14'] = test_issue_14_initial_idea(driver)
        results['Issue #13'] = test_issue_13_edit_duplicate(driver)
        results['Issue #1'] = test_issue_1_file_upload(driver)
        # Issue #8 需要完整流程，暂时跳过
        
        # 打印结果摘要
        print("\n" + "="*80)
        print("测试结果摘要")
        print("="*80)
        for issue, result in results.items():
            if result is None:
                status = "⚠️ SKIP"
            elif result:
                status = "✓ PASS"
            else:
                status = "✗ FAIL"
            print(f"{status} - {issue}")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n按Enter键关闭浏览器...")
        input()
        driver.quit()
        print("✓ 测试完成")

if __name__ == '__main__':
    main()
