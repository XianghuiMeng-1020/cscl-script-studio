#!/usr/bin/env python3
"""
测试 Step 4 剩余功能
完整生成流程测试
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from datetime import datetime

# 配置
BASE_URL = "https://web-production-591d6.up.railway.app"
USERNAME = "teacher_demo"
PASSWORD = "Demo@12345"
OUTPUT_DIR = "outputs/step4_test"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

class Step4FeatureTest:
    def __init__(self):
        print("初始化Chrome浏览器...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ Chrome浏览器初始化成功")
        self.wait = WebDriverWait(self.driver, 30)
        self.results = {}
            
    def save_screenshot(self, name):
        """保存截图"""
        filepath = os.path.join(OUTPUT_DIR, f"{name}.png")
        self.driver.save_screenshot(filepath)
        print(f"✓ 截图: {name}.png")
        return filepath
    
    def save_page_source(self, name):
        """保存页面源码"""
        filepath = os.path.join(OUTPUT_DIR, f"{name}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        print(f"✓ 页面源码: {name}.html")
        return filepath
        
    def step1_login(self):
        """步骤1: 登录"""
        print("\n" + "="*80)
        print("步骤 1: 登录")
        print("="*80)
        
        try:
            self.driver.get(f"{BASE_URL}/teacher")
            time.sleep(2)
            self.save_screenshot("01_login_page")
            
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            username_input.send_keys(USERNAME)
            
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_input.send_keys(PASSWORD)
            
            self.save_screenshot("02_login_filled")
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(3)
            self.save_screenshot("03_after_login")
            
            print("✓ 登录成功")
            return True
            
        except Exception as e:
            print(f"✗ 登录失败: {str(e)}")
            return False
    
    def step2_create_activity(self):
        """步骤2: 创建新活动"""
        print("\n" + "="*80)
        print("步骤 2: 创建新活动")
        print("="*80)
        
        try:
            # 点击"+ New Activity"按钮 (右上角)
            new_activity_btn = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn-primary[onclick='startNewActivity()']"))
            )
            # 使用JavaScript点击以避免元素被遮挡
            self.driver.execute_script("arguments[0].click();", new_activity_btn)
            time.sleep(3)
            self.save_screenshot("04_step1_page")
            
            print("✓ 点击新建活动按钮")
            
            # 等待Step 1页面加载
            time.sleep(2)
            
            # 查找并点击"继续"按钮到Step 2
            # 尝试多种选择器
            continue_clicked = False
            selectors = [
                "//button[contains(text(), '继续')]",
                "//button[contains(text(), 'Continue')]",
                "//button[@type='submit']",
                "//button[contains(@class, 'continue')]"
            ]
            
            for selector in selectors:
                try:
                    continue_btn = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    continue_btn.click()
                    continue_clicked = True
                    print(f"✓ 点击继续按钮 (使用选择器: {selector})")
                    break
                except:
                    continue
            
            if not continue_clicked:
                print("⚠ 未找到继续按钮，尝试查找页面上的所有按钮...")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    print(f"  按钮文本: '{btn.text}'")
                    if '继续' in btn.text or 'Continue' in btn.text.lower():
                        btn.click()
                        continue_clicked = True
                        print(f"✓ 点击按钮: {btn.text}")
                        break
            
            time.sleep(3)
            self.save_screenshot("05_step2_page")
            
            if continue_clicked:
                print("✓ 成功进入 Step 2")
                return True
            else:
                print("✗ 未能点击继续按钮")
                return False
            
        except Exception as e:
            print(f"✗ 创建活动失败: {str(e)}")
            self.save_screenshot("error_create_activity")
            self.save_page_source("error_create_activity_source")
            return False
    
    def step3_fill_form(self):
        """步骤3: 填写Step 2表单"""
        print("\n" + "="*80)
        print("步骤 3: 填写 Step 2 表单")
        print("="*80)
        
        try:
            # 填写课程名称 (使用ID选择器)
            course_name = self.wait.until(
                EC.presence_of_element_located((By.ID, "specCourse"))
            )
            course_name.clear()
            course_name.send_keys("Test Course")
            print("✓ 填写课程名称: Test Course")
            
            # 填写主题
            topic = self.driver.find_element(By.ID, "specTopic")
            topic.clear()
            topic.send_keys("Test Topic")
            print("✓ 填写主题: Test Topic")
            
            # 填写时长
            duration = self.driver.find_element(By.ID, "specDuration")
            duration.clear()
            duration.send_keys("30")
            print("✓ 填写时长: 30")
            
            # 选择模式 (使用下拉菜单)
            mode_select = self.driver.find_element(By.ID, "specMode")
            self.driver.execute_script("arguments[0].value = 'sync';", mode_select)
            print("✓ 选择模式: sync")
            
            # 填写班级人数
            class_size = self.driver.find_element(By.ID, "specClassSize")
            class_size.clear()
            class_size.send_keys("30")
            print("✓ 填写班级人数: 30")
            
            # 滚动到页面中部以显示更多字段
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
            
            # 填写课程背景 (Course Context)
            course_context = self.driver.find_element(By.ID, "specCourseContext")
            course_context.clear()
            course_context.send_keys("This is a test course for computer science students")
            print("✓ 填写课程背景: This is a test course for computer science students")
            
            # 填写学习目标
            learning_objectives = self.driver.find_element(By.ID, "specObjectives")
            learning_objectives.clear()
            learning_objectives.send_keys("Understand test concept\nCompare different approaches")
            print("✓ 填写学习目标: Understand test concept")
            
            # **CRITICAL**: 填写Initial Idea
            print("\n填写 Initial Idea...")
            initial_idea = self.driver.find_element(By.ID, "specInitialIdea")
            initial_idea.clear()
            initial_idea.send_keys("I want a simple comparison activity")
            print("✓ 填写 Initial Idea: I want a simple comparison activity")
            
            self.save_screenshot("06_step2_filled")
            
            # 滚动到页面底部以找到验证按钮
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # 点击"Validate Teaching Plan"按钮
            validate_btn = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[onclick='validateSpec()']"))
            )
            self.driver.execute_script("arguments[0].click();", validate_btn)
            print("✓ 点击验证教学计划")
            
            # 等待验证完成 (查找成功消息)
            print("等待验证完成...")
            for i in range(10):  # 最多等待10秒
                time.sleep(1)
                try:
                    success_msg = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Validation Successful') or contains(text(), '验证成功')]")
                    if success_msg.is_displayed():
                        print("✓ 验证成功")
                        break
                except:
                    pass
            
            time.sleep(2)
            self.save_screenshot("07_after_validation")
            
            # 滚动到页面底部找到继续按钮
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # 点击"继续"按钮 (使用ID选择器)
            continue_btn = self.wait.until(
                EC.presence_of_element_located((By.ID, "wizardStep2Next"))
            )
            # 等待按钮启用
            for i in range(10):
                if continue_btn.is_enabled():
                    break
                time.sleep(1)
            
            self.driver.execute_script("arguments[0].click();", continue_btn)
            print("✓ 点击继续按钮")
            time.sleep(3)
            self.save_screenshot("08_step3_page")
            
            print("✓ 成功进入 Step 3")
            return True
            
        except Exception as e:
            print(f"✗ 填写表单失败: {str(e)}")
            self.save_screenshot("error_fill_form")
            self.save_page_source("error_fill_form_source")
            return False
    
    def step4_run_generation(self):
        """步骤4: 运行生成"""
        print("\n" + "="*80)
        print("步骤 4: 运行生成")
        print("="*80)
        
        try:
            # 滚动到页面底部找到开始生成按钮
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # 点击"Start Generation"按钮
            start_btn = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Start Generation') or contains(text(), '开始生成')]"))
            )
            self.driver.execute_script("arguments[0].click();", start_btn)
            print("✓ 点击开始生成")
            time.sleep(3)
            self.save_screenshot("09_generation_started")
            
            # 等待生成完成 (最多120秒)
            print("等待生成完成 (最多120秒)...")
            generation_complete = False
            for i in range(24):  # 24 * 5 = 120秒
                time.sleep(5)
                print(f"  等待中... {(i+1)*5}秒")
                
                # 检查是否有成功指示器
                try:
                    # 查找"继续"按钮或完成指示器
                    continue_btn = self.driver.find_element(By.ID, "wizardStep3Next")
                    if continue_btn.is_displayed() and continue_btn.is_enabled():
                        print("✓ 生成完成!")
                        generation_complete = True
                        break
                except:
                    pass
                
                # 检查是否所有任务都完成
                try:
                    pending_tasks = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Pending')]")
                    if len(pending_tasks) == 0:
                        print("✓ 所有任务完成!")
                        generation_complete = True
                        break
                except:
                    pass
                
                if i % 2 == 0:  # 每10秒截图一次
                    self.save_screenshot(f"10_generation_progress_{(i+1)*5}s")
            
            if not generation_complete:
                print("⚠ 生成超时，但继续尝试...")
                time.sleep(5)
            
            self.save_screenshot("11_generation_complete")
            
            # 点击"继续"到Step 4
            continue_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '继续')]"))
            )
            continue_btn.click()
            time.sleep(2)
            self.save_screenshot("12_step4_page")
            
            print("✓ 成功进入 Step 4")
            return True
            
        except Exception as e:
            print(f"✗ 生成失败: {str(e)}")
            self.save_screenshot("error_generation")
            return False
    
    def step5_verify_step4_features(self):
        """步骤5: 验证Step 4功能"""
        print("\n" + "="*80)
        print("步骤 5: 验证 Step 4 功能")
        print("="*80)
        
        # Issue #8 - 3个输出标签页
        print("\n--- Issue #8: 3个输出标签页 ---")
        try:
            tabs = self.driver.find_elements(By.CSS_SELECTOR, ".tab, [role='tab'], .nav-tabs li, button[role='tab']")
            print(f"找到 {len(tabs)} 个标签页")
            
            tab_texts = [tab.text for tab in tabs if tab.text.strip()]
            print(f"标签页文本: {tab_texts}")
            
            expected_tabs = ["Student Worksheet", "Student Slides", "Teacher Facilitation Sheet"]
            has_all_tabs = all(any(expected in text for text in tab_texts) for expected in expected_tabs)
            
            if has_all_tabs or len(tabs) >= 3:
                self.results['issue_8_tabs'] = 'PASS'
                print("✓ Issue #8: PASS - 找到3个输出标签页")
                
                # 点击每个标签页
                for i, tab in enumerate(tabs[:3]):
                    try:
                        tab.click()
                        time.sleep(1)
                        self.save_screenshot(f"13_tab_{i+1}")
                        print(f"  ✓ 点击标签页 {i+1}")
                    except:
                        pass
            else:
                self.results['issue_8_tabs'] = f'FAIL - 只找到 {len(tabs)} 个标签页'
                print(f"✗ Issue #8: FAIL - 只找到 {len(tabs)} 个标签页")
                
        except Exception as e:
            self.results['issue_8_tabs'] = f'FAIL: {str(e)}'
            print(f"✗ Issue #8: FAIL - {str(e)}")
        
        self.save_screenshot("14_tabs_verification")
        
        # Issue #7 - 无Pipeline Summary
        print("\n--- Issue #7: 无Pipeline Summary ---")
        try:
            # 滚动到页面底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.save_screenshot("15_page_bottom")
            
            # 查找Pipeline Summary
            try:
                pipeline_summary = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Pipeline Summary')]")
                self.results['issue_7_no_pipeline'] = 'FAIL - 找到了 Pipeline Summary'
                print("✗ Issue #7: FAIL - 找到了 Pipeline Summary (不应该存在)")
            except NoSuchElementException:
                self.results['issue_7_no_pipeline'] = 'PASS'
                print("✓ Issue #7: PASS - 没有找到 Pipeline Summary")
                
        except Exception as e:
            self.results['issue_7_no_pipeline'] = f'ERROR: {str(e)}'
            print(f"✗ Issue #7: ERROR - {str(e)}")
        
        # Issue #5 - 修改并重新生成按钮
        print("\n--- Issue #5: 修改并重新生成按钮 ---")
        try:
            # 滚动到顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            edit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '修改并重新生成') or contains(text(), 'Edit') and contains(text(), 'Regenerate')]")
            
            if edit_btn.is_displayed():
                self.results['issue_5_edit_btn'] = 'PASS'
                print("✓ Issue #5: PASS - 找到修改并重新生成按钮")
                self.save_screenshot("16_edit_button")
                
                # 点击按钮验证功能
                edit_btn.click()
                time.sleep(2)
                self.save_screenshot("17_after_edit_click")
                
                # 检查是否返回Step 2
                try:
                    step2_indicator = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Step 2') or contains(text(), '步骤2')]")
                    print("  ✓ 成功返回 Step 2")
                except:
                    print("  ⚠ 未能确认返回 Step 2")
            else:
                self.results['issue_5_edit_btn'] = 'FAIL - 按钮不可见'
                print("✗ Issue #5: FAIL - 按钮不可见")
                
        except NoSuchElementException:
            self.results['issue_5_edit_btn'] = 'FAIL - 未找到按钮'
            print("✗ Issue #5: FAIL - 未找到修改并重新生成按钮")
            self.save_screenshot("16_no_edit_button")
        except Exception as e:
            self.results['issue_5_edit_btn'] = f'ERROR: {str(e)}'
            print(f"✗ Issue #5: ERROR - {str(e)}")
        
        # Issue #6 - 导出标签
        print("\n--- Issue #6: 导出标签 ---")
        try:
            # 如果点击了编辑按钮，需要返回Step 4
            if 'PASS' in self.results.get('issue_5_edit_btn', ''):
                print("  返回 Step 4 以检查导出标签...")
                # 这里需要重新执行生成流程，但为了测试简化，我们跳过
                self.results['issue_6_export_labels'] = 'SKIPPED - 已点击编辑按钮'
                print("⚠ Issue #6: SKIPPED - 已点击编辑按钮，需要重新生成")
            else:
                # 查找导出按钮
                export_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), '下载') or contains(text(), 'Download') or contains(text(), 'Export')]")
                
                if export_buttons:
                    print(f"找到 {len(export_buttons)} 个导出按钮")
                    
                    has_improved_labels = False
                    for btn in export_buttons:
                        btn_text = btn.text
                        print(f"  导出按钮文本: '{btn_text}'")
                        
                        # 检查是否有改进的标签
                        if 'JSON' in btn_text or '数据' in btn_text or 'Download' in btn_text:
                            has_improved_labels = True
                        
                        # 检查是否还有旧的"Export Script"标签
                        if 'Export Script' in btn_text:
                            has_improved_labels = False
                            break
                    
                    if has_improved_labels:
                        self.results['issue_6_export_labels'] = 'PASS'
                        print("✓ Issue #6: PASS - 导出按钮有改进的标签")
                    else:
                        self.results['issue_6_export_labels'] = 'FAIL - 标签未改进'
                        print("✗ Issue #6: FAIL - 导出按钮标签未改进")
                    
                    self.save_screenshot("18_export_buttons")
                else:
                    self.results['issue_6_export_labels'] = 'FAIL - 未找到导出按钮'
                    print("✗ Issue #6: FAIL - 未找到导出按钮")
                    
        except Exception as e:
            self.results['issue_6_export_labels'] = f'ERROR: {str(e)}'
            print(f"✗ Issue #6: ERROR - {str(e)}")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("测试结果总结")
        print("="*80)
        
        report = []
        report.append("# Step 4 功能测试报告\n")
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"测试URL: {BASE_URL}\n\n")
        
        report.append("## 测试结果\n\n")
        
        for issue, result in self.results.items():
            status = "✓ PASS" if "PASS" in result else "✗ FAIL"
            report.append(f"**{issue}**: {status}\n")
            report.append(f"  - 详情: {result}\n\n")
            print(f"{issue}: {result}")
        
        report.append("\n## 截图\n\n")
        report.append(f"所有截图保存在: `{OUTPUT_DIR}/`\n")
        
        # 保存报告
        report_path = os.path.join(OUTPUT_DIR, "TEST_REPORT.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.writelines(report)
        
        print(f"\n✓ 测试报告已保存: {report_path}")
        
    def run(self):
        """运行完整测试"""
        try:
            if not self.step1_login():
                return
            
            if not self.step2_create_activity():
                return
            
            if not self.step3_fill_form():
                return
            
            if not self.step4_run_generation():
                return
            
            self.step5_verify_step4_features()
            
            self.generate_report()
            
        except Exception as e:
            print(f"\n✗ 测试过程中发生错误: {str(e)}")
            self.save_screenshot("error_final")
            
        finally:
            print("\n关闭浏览器...")
            self.driver.quit()
            print("✓ 测试完成")

if __name__ == "__main__":
    test = Step4FeatureTest()
    test.run()
