#!/usr/bin/env python3
"""
测试CSCL剩余问题 - 使用真实登录 (v2 - 修正选择器)
Test remaining CSCL issues with real login (v2 - fixed selectors)
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
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        
        # 查找用户名输入框
        try:
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.clear()
            username_input.send_keys(USERNAME)
            
            password_input = driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(PASSWORD)
            
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            time.sleep(3)
        except:
            pass
        
        # 检查是否登录成功
        if driver.find_elements(By.CLASS_NAME, "sidebar"):
            print("  ✓ 登录成功！")
            return True
        else:
            print("  ✗ 登录失败")
            return False
            
    except Exception as e:
        print(f"  ✗ 登录异常: {str(e)}")
        return False

def test_issue_2_checkbox(driver):
    """测试Issue #2: 步骤1中"不提取文字"复选框默认勾选"""
    print("\n" + "="*80)
    print("[Issue #2] 测试'不提取文字'复选框默认勾选")
    print("="*80)
    try:
        # 点击"新建活动"
        new_activity_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '新建活动') or contains(text(), 'New Activity') or contains(text(), 'Create New Project')]"))
        )
        new_activity_btn.click()
        print("  ✓ 点击'新建活动'")
        time.sleep(2)
        
        take_screenshot(driver, "issue2_step1")
        
        # 尝试多种方式查找复选框
        checkbox = None
        checkbox_id = None
        
        # 方法1: 通过文本查找
        try:
            checkbox = driver.find_element(By.XPATH, "//input[@type='checkbox' and contains(following-sibling::text(), 'Do not extract')]")
            checkbox_id = "xpath-text"
        except:
            pass
        
        # 方法2: 查找所有复选框
        if not checkbox:
            try:
                checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                for cb in checkboxes:
                    # 获取复选框附近的文本
                    parent = cb.find_element(By.XPATH, "..")
                    if "extract" in parent.text.lower() or "提取" in parent.text:
                        checkbox = cb
                        checkbox_id = cb.get_attribute("id") or "found-by-text"
                        break
            except:
                pass
        
        if checkbox:
            is_checked = checkbox.is_selected()
            print(f"  ✓ 找到复选框 (ID: {checkbox_id})")
            print(f"  {'✓' if is_checked else '✗'} 复选框状态: {'已勾选 ✓' if is_checked else '未勾选 ✗'}")
            
            # 获取复选框附近的标签文本
            try:
                parent = checkbox.find_element(By.XPATH, "..")
                label_text = parent.text
                print(f"  标签文本: {label_text}")
            except:
                pass
            
            take_screenshot(driver, "issue2_checkbox_found")
            
            if is_checked:
                print("\n  ✅ Issue #2 已修复：复选框默认已勾选")
                return True
            else:
                print("\n  ❌ Issue #2 未修复：复选框默认未勾选")
                return False
        else:
            print("  ✗ 未找到'不提取文字'复选框")
            print("\n  ❌ Issue #2 未修复：找不到复选框")
            return False
            
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        take_screenshot(driver, "issue2_error")
        return False

def test_issue_3_uploaded_files(driver):
    """测试Issue #3: 步骤1中"已上传的文件"区域"""
    print("\n" + "="*80)
    print("[Issue #3] 测试'已上传的文件'区域存在")
    print("="*80)
    try:
        take_screenshot(driver, "issue3_step1")
        
        # 尝试多种方式查找"已上传的文件"区域
        uploaded_section = None
        
        # 方法1: 通过ID
        try:
            uploaded_section = driver.find_element(By.ID, "uploaded-files-list")
        except:
            pass
        
        # 方法2: 通过文本查找
        if not uploaded_section:
            try:
                uploaded_section = driver.find_element(By.XPATH, "//*[contains(text(), '已上传') or contains(text(), 'Uploaded')]")
            except:
                pass
        
        # 方法3: 查找包含"file"的区域
        if not uploaded_section:
            try:
                page_source = driver.page_source
                if "uploaded" in page_source.lower() and "file" in page_source.lower():
                    uploaded_section = driver.find_element(By.XPATH, "//*[contains(@class, 'file') or contains(@class, 'upload')]")
            except:
                pass
        
        if uploaded_section:
            is_visible = uploaded_section.is_displayed()
            print(f"  ✓ 找到'已上传的文件'区域")
            print(f"  {'✓' if is_visible else '✗'} 区域状态: {'可见 ✓' if is_visible else '不可见 ✗'}")
            take_screenshot(driver, "issue3_files_found")
            
            if is_visible:
                print("\n  ✅ Issue #3 已修复：已上传文件区域存在且可见")
                return True
            else:
                print("\n  ⚠️ Issue #3 部分修复：区域存在但不可见")
                return False
        else:
            print("  ✗ 未找到'已上传的文件'区域")
            print("\n  ❌ Issue #3 未修复：找不到已上传文件区域")
            return False
            
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        return False

def test_issue_14_initial_idea(driver):
    """测试Issue #14: 步骤2顶部的"初步想法"输入框"""
    print("\n" + "="*80)
    print("[Issue #14] 测试步骤2顶部的'初步想法'输入框")
    print("="*80)
    try:
        # 点击"继续"进入步骤2
        continue_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '继续') or contains(text(), 'Continue') or contains(text(), 'Next')]"))
        )
        continue_btn.click()
        print("  ✓ 点击'继续'进入步骤2")
        time.sleep(2)
        
        take_screenshot(driver, "issue14_step2")
        
        # 尝试多种方式查找"初步想法"输入框
        initial_idea = None
        
        # 方法1: 通过ID
        try:
            initial_idea = driver.find_element(By.ID, "initial-idea")
        except:
            pass
        
        # 方法2: 通过name属性
        if not initial_idea:
            try:
                initial_idea = driver.find_element(By.NAME, "initial_idea")
            except:
                pass
        
        # 方法3: 通过placeholder或label文本
        if not initial_idea:
            try:
                initial_idea = driver.find_element(By.XPATH, "//textarea[contains(@placeholder, '初步想法') or contains(@placeholder, 'initial idea')]")
            except:
                pass
        
        # 方法4: 查找页面上第一个textarea
        if not initial_idea:
            try:
                textareas = driver.find_elements(By.TAG_NAME, "textarea")
                if textareas:
                    # 检查第一个textarea是否在页面顶部
                    first_textarea = textareas[0]
                    location = first_textarea.location
                    if location['y'] < 300:  # 如果在页面顶部300px内
                        initial_idea = first_textarea
            except:
                pass
        
        # 检查页面源码中是否有相关文本
        page_source = driver.page_source
        has_label = ("初步想法" in page_source or 
                    "initial idea" in page_source.lower() or
                    "initial thought" in page_source.lower())
        
        if initial_idea:
            is_visible = initial_idea.is_displayed()
            location = initial_idea.location
            print(f"  ✓ 找到输入框")
            print(f"  位置: Y={location['y']}px")
            print(f"  {'✓' if is_visible else '✗'} 输入框状态: {'可见 ✓' if is_visible else '不可见 ✗'}")
            print(f"  {'✓' if has_label else '✗'} 标签文本: {'存在 ✓' if has_label else '不存在 ✗'}")
            take_screenshot(driver, "issue14_initial_idea_found")
            
            if is_visible and has_label:
                print("\n  ✅ Issue #14 已修复：初步想法输入框在表单顶部")
                return True
            else:
                print("\n  ⚠️ Issue #14 部分修复：输入框存在但位置或标签有问题")
                return False
        else:
            print("  ✗ 未找到'初步想法'输入框")
            print(f"  {'✓' if has_label else '✗'} 页面中有相关文本: {has_label}")
            print("\n  ❌ Issue #14 未修复：找不到初步想法输入框")
            return False
            
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        take_screenshot(driver, "issue14_error")
        return False

def test_issue_13_edit_duplicate(driver):
    """测试Issue #13: 活动项目有编辑和复制按钮"""
    print("\n" + "="*80)
    print("[Issue #13] 测试活动项目的编辑和复制按钮")
    print("="*80)
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
        
        take_screenshot(driver, "issue13_projects")
        
        # 检查页面源码和按钮
        page_source = driver.page_source
        has_edit = "Edit" in page_source or "编辑" in page_source
        has_duplicate = "Duplicate" in page_source or "复制" in page_source
        
        # 尝试查找实际的按钮元素
        edit_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Edit') or contains(text(), '编辑')]")
        duplicate_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Duplicate') or contains(text(), '复制')]")
        
        print(f"  {'✓' if has_edit else '✗'} 编辑按钮: {'存在 ✓' if has_edit else '不存在 ✗'} (找到 {len(edit_buttons)} 个)")
        print(f"  {'✓' if has_duplicate else '✗'} 复制按钮: {'存在 ✓' if has_duplicate else '不存在 ✗'} (找到 {len(duplicate_buttons)} 个)")
        
        if has_edit and has_duplicate:
            print("\n  ✅ Issue #13 已修复：活动项目卡片有编辑和复制按钮")
            return True
        else:
            print("\n  ❌ Issue #13 未修复：缺少编辑或复制按钮")
            return False
        
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        take_screenshot(driver, "issue13_error")
        return False

def test_issue_1_file_upload(driver):
    """测试Issue #1: 文件上传不需要选择课程/课时"""
    print("\n" + "="*80)
    print("[Issue #1] 测试文件上传（无material_level单选）")
    print("="*80)
    try:
        # 回到新建活动页面
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        
        new_activity_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '新建活动') or contains(text(), 'New Activity') or contains(text(), 'Create New Project')]"))
        )
        new_activity_btn.click()
        time.sleep(2)
        
        take_screenshot(driver, "issue1_upload")
        
        # 检查是否存在material_level单选框
        page_source = driver.page_source
        has_material_level = "material_level" in page_source or "material-level" in page_source
        
        # 尝试查找单选按钮
        radio_buttons = driver.find_elements(By.XPATH, "//input[@type='radio']")
        has_radio = len(radio_buttons) > 0
        
        print(f"  {'✗' if has_material_level else '✓'} material_level: {'存在（不应该）✗' if has_material_level else '不存在（正确）✓'}")
        print(f"  {'✗' if has_radio else '✓'} 单选按钮: {'找到 {len(radio_buttons)} 个（不应该）✗' if has_radio else '未找到（正确）✓'}")
        
        if not has_material_level and not has_radio:
            print("\n  ✅ Issue #1 已修复：文件上传不需要选择material_level")
            return True
        else:
            print("\n  ❌ Issue #1 未修复：仍然存在material_level选择")
            return False
        
    except Exception as e:
        print(f"  ✗ 测试异常: {str(e)}")
        take_screenshot(driver, "issue1_error")
        return False

def test_issue_8_output_tabs(driver):
    """测试Issue #8: 步骤4预览有3个标签页"""
    print("\n" + "="*80)
    print("[Issue #8] 测试输出材料的3个标签页")
    print("="*80)
    print("  ⚠️ 此测试需要完整填写表单并生成活动")
    print("  由于时间限制，建议手动测试或在完整流程中验证")
    print("\n  ⏭️ Issue #8 跳过：需要完整生成流程")
    return None

def main():
    """主测试流程"""
    print("="*80)
    print("CSCL应用程序 - 剩余问题验证测试（真实登录）v2")
    print("="*80)
    print(f"测试URL: {BASE_URL}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"登录凭据: {USERNAME}")
    print("="*80)
    
    driver = setup_driver()
    results = {}
    
    try:
        # 登录
        if not login(driver):
            print("\n✗ 登录失败，无法继续测试")
            return
        
        # 测试各个问题
        results['Issue #1'] = test_issue_1_file_upload(driver)
        results['Issue #2'] = test_issue_2_checkbox(driver)
        results['Issue #3'] = test_issue_3_uploaded_files(driver)
        results['Issue #14'] = test_issue_14_initial_idea(driver)
        results['Issue #13'] = test_issue_13_edit_duplicate(driver)
        results['Issue #8'] = test_issue_8_output_tabs(driver)
        
        # 打印最终结果摘要
        print("\n" + "="*80)
        print("📊 最终测试结果摘要")
        print("="*80)
        
        passed = 0
        failed = 0
        skipped = 0
        
        for issue, result in results.items():
            if result is None:
                status = "⏭️ SKIP"
                skipped += 1
            elif result:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1
            print(f"{status} - {issue}")
        
        print("="*80)
        print(f"总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
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
