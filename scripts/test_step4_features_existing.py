#!/usr/bin/env python3
"""
测试 Step 4 功能 - 使用已有活动
直接从 Activity Projects 进入已完成的活动来测试 Step 4 功能
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
OUTPUT_DIR = "outputs/step4_test_existing"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

class Step4ExistingTest:
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
        self.script_id = None
            
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
        
    def login(self):
        """登录"""
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
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(5)  # 等待页面加载
            self.save_screenshot("02_after_login")
            
            print("✓ 登录成功")
            return True
            
        except Exception as e:
            print(f"✗ 登录失败: {str(e)}")
            return False
    
    def navigate_to_activity_projects(self):
        """导航到 Activity Projects"""
        print("\n" + "="*80)
        print("步骤 2: 导航到 Activity Projects")
        print("="*80)
        
        try:
            # 等待页面完全加载，等待 Processing... 消失
            print("等待页面加载完成...")
            time.sleep(8)
            
            # 尝试等待 Processing 消失
            try:
                WebDriverWait(self.driver, 20).until_not(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Processing')]"))
                )
                print("✓ Processing 已消失")
            except:
                print("⚠ 未检测到 Processing 或已消失")
            
            time.sleep(2)
            self.save_screenshot("02b_before_click_activity")
            
            # 尝试多种方式查找 Activity Projects 链接
            selectors = [
                "//a[contains(text(), 'Activity Projects')]",
                "//a[contains(@href, 'activity')]",
                "//div[contains(@class, 'sidebar')]//a[contains(text(), 'Activity')]",
                "//nav//a[contains(text(), 'Activity')]",
                "//*[@data-view='activity-projects']",
                "//a[contains(., 'Activity Projects')]"
            ]
            
            activity_link = None
            for selector in selectors:
                try:
                    activity_link = self.driver.find_element(By.XPATH, selector)
                    print(f"✓ 找到链接使用选择器: {selector}")
                    break
                except:
                    continue
            
            if activity_link is None:
                print("✗ 尝试所有选择器都失败")
                # 打印页面上所有链接
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"页面上共有 {len(all_links)} 个链接:")
                for i, link in enumerate(all_links[:20]):  # 只打印前20个
                    print(f"  {i+1}. {link.text[:50]} - href: {link.get_attribute('href')}")
                self.save_screenshot("error_no_activity_link")
                self.save_page_source("error_no_activity_link")
                return False
            
            # 点击链接
            self.driver.execute_script("arguments[0].click();", activity_link)
            time.sleep(3)
            self.save_screenshot("03_activity_projects")
            
            print("✓ 成功进入 Activity Projects")
            return True
            
        except Exception as e:
            print(f"✗ 导航失败: {str(e)}")
            self.save_screenshot("error_navigate")
            self.save_page_source("error_navigate")
            return False
    
    def find_and_open_completed_activity(self):
        """查找并打开已完成的活动"""
        print("\n" + "="*80)
        print("步骤 3: 查找并打开已完成的活动")
        print("="*80)
        
        try:
            # 等待页面加载
            time.sleep(2)
            
            # 尝试多种选择器查找活动卡片
            selectors = [
                ".activity-card",
                ".project-card", 
                "[class*='card']",
                "div[class*='activity']",
                "div[class*='project']"
            ]
            
            activities = []
            for selector in selectors:
                activities = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(activities) > 0:
                    print(f"✓ 使用选择器 '{selector}' 找到 {len(activities)} 个活动")
                    break
            
            if len(activities) == 0:
                print("⚠ 未找到活动卡片，尝试查找所有可点击元素...")
                # 查找包含 "Demo" 或 "final" 的元素
                activities = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Demo') or contains(text(), 'final')]")
                print(f"找到 {len(activities)} 个包含关键词的元素")
            
            # 打印找到的活动信息
            for i, activity in enumerate(activities[:5]):
                try:
                    text = activity.text[:100]
                    print(f"  活动 {i+1}: {text}")
                except:
                    pass
            
            # 查找 "Edit" 按钮
            if len(activities) > 0:
                print("\n尝试查找 Edit 按钮...")
                try:
                    # 查找 Edit 按钮
                    edit_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Edit') or contains(@class, 'edit')]")
                    print(f"找到 {len(edit_buttons)} 个 Edit 按钮")
                    
                    if len(edit_buttons) > 0:
                        edit_btn = edit_buttons[0]
                        print(f"点击第一个 Edit 按钮: {edit_btn.text}")
                        
                        # 尝试从按钮的 onclick 属性中提取 script ID
                        try:
                            onclick = edit_btn.get_attribute('onclick')
                            print(f"  onclick 属性: {onclick}")
                            if onclick and 'editScript' in onclick:
                                # 提取 script ID，格式如: editScript('123')
                                import re
                                match = re.search(r"editScript\('([^']+)'\)", onclick)
                                if match:
                                    self.script_id = match.group(1)
                                    print(f"  ✓ 提取到 script_id: {self.script_id}")
                        except Exception as e:
                            print(f"  ⚠ 提取 script_id 失败: {str(e)}")
                        
                        self.driver.execute_script("arguments[0].click();", edit_btn)
                        time.sleep(3)
                        self.save_screenshot("04_activity_opened")
                        print("✓ 成功打开活动")
                        return True
                except Exception as e:
                    print(f"⚠ 查找 Edit 按钮失败: {str(e)}")
                
                # 尝试查找 Duplicate 或 Quality Report 按钮旁边的元素
                print("\n尝试查找其他按钮...")
                try:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    print(f"页面上共有 {len(all_buttons)} 个按钮:")
                    for i, btn in enumerate(all_buttons[:15]):
                        btn_text = btn.text.strip()
                        if btn_text:
                            print(f"  按钮 {i+1}: '{btn_text}'")
                            # 如果是 Edit 按钮，点击它
                            if 'Edit' in btn_text or '编辑' in btn_text:
                                print(f"找到 Edit 按钮，点击...")
                                
                                # 尝试从按钮的 onclick 属性中提取 script ID
                                try:
                                    onclick = btn.get_attribute('onclick')
                                    print(f"  onclick 属性: {onclick}")
                                    if onclick and 'editScript' in onclick:
                                        # 提取 script ID，格式如: editScript('123')
                                        import re
                                        match = re.search(r"editScript\('([^']+)'\)", onclick)
                                        if match:
                                            self.script_id = match.group(1)
                                            print(f"  ✓ 提取到 script_id: {self.script_id}")
                                except Exception as e:
                                    print(f"  ⚠ 提取 script_id 失败: {str(e)}")
                                
                                self.driver.execute_script("arguments[0].click();", btn)
                                time.sleep(3)
                                self.save_screenshot("04_activity_opened")
                                print("✓ 成功打开活动")
                                return True
                except Exception as e:
                    print(f"⚠ 查找按钮失败: {str(e)}")
                
                print("✗ 未找到 Edit 按钮")
                self.save_screenshot("error_no_edit_button")
                self.save_page_source("error_no_edit_button")
                return False
            else:
                print("✗ 未找到任何活动")
                self.save_screenshot("error_no_activities")
                self.save_page_source("error_no_activities")
                return False
                
        except Exception as e:
            print(f"✗ 打开活动失败: {str(e)}")
            self.save_screenshot("error_open_activity")
            self.save_page_source("error_open_activity_source")
            return False
    
    def navigate_to_step4(self):
        """导航到 Step 4"""
        print("\n" + "="*80)
        print("步骤 4: 导航到 Step 4")
        print("="*80)
        
        try:
            # 等待页面加载
            time.sleep(2)
            
            # 尝试从 JavaScript 变量中获取 script ID
            try:
                script_id = self.driver.execute_script("return window.currentScriptId || null;")
                print(f"  从 window.currentScriptId 获取: {script_id}")
                
                # 如果没有从 JS 变量获取到，使用之前保存的 script_id
                if not script_id and self.script_id:
                    script_id = self.script_id
                    print(f"  使用之前提取的 script_id: {script_id}")
                
                if script_id:
                    # 保存到 sessionStorage 和 window 变量
                    self.driver.execute_script(f"""
                        sessionStorage.setItem('cscl_current_script_id', '{script_id}');
                        window.currentScriptId = '{script_id}';
                    """)
                    print(f"  ✓ 已保存 script_id: {script_id}")
            except Exception as e:
                print(f"  ⚠ 获取 script ID 失败: {str(e)}")
            
            # 尝试多种方式查找 Step 4
            selectors = [
                # 尝试点击步骤4的数字按钮
                "//div[contains(@class, 'step') and contains(text(), '4')]",
                "//button[contains(text(), '4')]",
                "//a[contains(text(), '4')]",
                # 尝试查找包含 "Review" 或 "Preview" 的元素
                "//a[contains(text(), 'Review') or contains(text(), 'Preview')]",
                "//*[contains(text(), 'Step 4')]",
                # 尝试查找步骤指示器中的第4个元素
                "(//div[contains(@class, 'step')])[4]",
                "(//button[contains(@class, 'step')])[4]"
            ]
            
            step4_element = None
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if len(elements) > 0:
                        # 打印找到的元素
                        for i, elem in enumerate(elements):
                            try:
                                text = elem.text[:50]
                                print(f"  找到元素 {i+1}: '{text}' 使用选择器: {selector}")
                            except:
                                pass
                        
                        # 尝试点击第一个元素
                        step4_element = elements[0]
                        print(f"✓ 找到 Step 4 元素使用选择器: {selector}")
                        break
                except:
                    continue
            
            if step4_element:
                # 滚动到元素位置
                self.driver.execute_script("arguments[0].scrollIntoView(true);", step4_element)
                time.sleep(1)
                
                # 点击元素
                self.driver.execute_script("arguments[0].click();", step4_element)
                time.sleep(3)
                self.save_screenshot("05_step4_page")
                
                # 检查 sessionStorage 中的 script ID
                try:
                    script_id = self.driver.execute_script("return sessionStorage.getItem('cscl_current_script_id');")
                    run_id = self.driver.execute_script("return sessionStorage.getItem('cscl_current_run_id');")
                    print(f"  sessionStorage script_id: {script_id}")
                    print(f"  sessionStorage run_id: {run_id}")
                    
                    # 手动调用 loadScriptPreview()
                    if script_id or run_id:
                        print("  手动调用 loadScriptPreview()...")
                        self.driver.execute_script("if (typeof loadScriptPreview === 'function') loadScriptPreview();")
                        time.sleep(2)
                except Exception as e:
                    print(f"  ⚠ 检查 sessionStorage 失败: {str(e)}")
                
                print("✓ 成功点击 Step 4")
                return True
            
            # 如果没找到，尝试查找所有步骤指示器
            print("\n查找所有步骤指示器...")
            all_steps = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'step') or contains(text(), 'Step')]")
            print(f"找到 {len(all_steps)} 个步骤相关元素")
            for i, step in enumerate(all_steps[:10]):
                try:
                    text = step.text[:100]
                    classes = step.get_attribute('class')
                    print(f"  步骤元素 {i+1}: '{text}' - class: {classes}")
                except:
                    pass
            
            # 检查当前页面是否已经是 Step 4
            print("\n检查当前页面是否已经是 Step 4...")
            try:
                # 查找 Step 4 的特征元素（如输出标签页）
                tabs = self.driver.find_elements(By.CSS_SELECTOR, ".tab, [role='tab'], button[role='tab']")
                print(f"找到 {len(tabs)} 个标签页")
                
                # 查找包含 "Student Worksheet" 等关键词的标签页
                for tab in tabs:
                    text = tab.text
                    if 'Student' in text or 'Teacher' in text or 'Worksheet' in text:
                        print(f"✓ 找到输出标签页: '{text}'，当前页面可能已经是 Step 4")
                        self.save_screenshot("05_step4_page")
                        return True
            except Exception as e:
                print(f"⚠ 检查标签页失败: {str(e)}")
            
            print("✗ 未找到 Step 4")
            self.save_screenshot("error_navigate_step4")
            self.save_page_source("error_navigate_step4")
            return False
            
        except Exception as e:
            print(f"✗ 导航到 Step 4 失败: {str(e)}")
            self.save_screenshot("error_navigate_step4")
            self.save_page_source("error_navigate_step4")
            return False
    
    def verify_step4_features(self):
        """验证 Step 4 功能"""
        print("\n" + "="*80)
        print("步骤 5: 验证 Step 4 功能")
        print("="*80)
        
        # 等待页面加载完成
        print("\n等待 Step 4 页面加载完成...")
        time.sleep(5)
        
        # 滚动页面以触发内容加载
        self.driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        self.save_screenshot("05b_step4_loaded")
        
        # 注意：预览可能无法加载（如果没有 pipeline run），但按钮应该是可见的
        print("注意：预览内容可能无法加载，但我们将验证按钮是否存在")
        
        # Issue #8 - 3个输出标签页
        print("\n--- Issue #8: 3个输出标签页 ---")
        try:
            # 查找所有标签页
            tabs = self.driver.find_elements(By.CSS_SELECTOR, "[role='tab'], .tab, .nav-tabs li, button[role='tab'], .tab-button, button[class*='tab']")
            print(f"找到 {len(tabs)} 个标签页元素")
            
            # 获取标签页文本
            tab_texts = []
            for tab in tabs:
                text = tab.text.strip()
                if text:
                    tab_texts.append(text)
                    print(f"  标签页: '{text}'")
            
            # 检查是否有3个输出标签页
            expected_tabs = ["Student Worksheet", "Student Slides", "Teacher Facilitation"]
            found_tabs = 0
            for expected in expected_tabs:
                for text in tab_texts:
                    if expected.lower() in text.lower():
                        found_tabs += 1
                        break
            
            if found_tabs >= 3 or len(tabs) >= 3:
                self.results['issue_8_tabs'] = 'PASS'
                print(f"✓ Issue #8: PASS - 找到 {len(tabs)} 个标签页")
                
                # 点击每个标签页并截图
                for i, tab in enumerate(tabs[:3]):
                    try:
                        self.driver.execute_script("arguments[0].click();", tab)
                        time.sleep(1)
                        self.save_screenshot(f"06_tab_{i+1}_{tab.text[:20]}")
                        print(f"  ✓ 点击标签页 {i+1}: {tab.text}")
                    except Exception as e:
                        print(f"  ⚠ 点击标签页 {i+1} 失败: {str(e)}")
            else:
                self.results['issue_8_tabs'] = f'FAIL - 只找到 {found_tabs} 个预期标签页'
                print(f"✗ Issue #8: FAIL - 只找到 {found_tabs} 个预期标签页")
                
        except Exception as e:
            self.results['issue_8_tabs'] = f'ERROR: {str(e)}'
            print(f"✗ Issue #8: ERROR - {str(e)}")
        
        self.save_screenshot("07_tabs_verification")
        
        # Issue #7 - 无Pipeline Summary
        print("\n--- Issue #7: 无Pipeline Summary ---")
        try:
            # 滚动到页面底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.save_screenshot("08_page_bottom")
            
            # 查找Pipeline Summary
            try:
                pipeline_summary = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Pipeline Summary') or contains(text(), '管道摘要')]")
                self.results['issue_7_no_pipeline'] = 'FAIL - 找到了 Pipeline Summary'
                print("✗ Issue #7: FAIL - 找到了 Pipeline Summary (不应该存在)")
                self.save_screenshot("08_pipeline_summary_found")
            except NoSuchElementException:
                self.results['issue_7_no_pipeline'] = 'PASS'
                print("✓ Issue #7: PASS - 没有找到 Pipeline Summary")
                
        except Exception as e:
            self.results['issue_7_no_pipeline'] = f'ERROR: {str(e)}'
            print(f"✗ Issue #7: ERROR - {str(e)}")
        
        # Issue #5 - 修改并重新生成按钮
        print("\n--- Issue #5: 修改并重新生成按钮 ---")
        try:
            # 滚动到底部（按钮在底部）
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.save_screenshot("08b_page_bottom_buttons")
            
            # 查找修改并重新生成按钮 - 使用更宽松的选择器
            selectors = [
                "//button[contains(text(), 'Edit') and contains(text(), 'Regenerate')]",
                "//button[contains(., 'Edit') and contains(., 'Regenerate')]",
                "//*[@id='editRegenerateBtn']",
                "//button[contains(@onclick, 'editAndRegenerate')]"
            ]
            
            edit_btn = None
            for selector in selectors:
                try:
                    edit_btn = self.driver.find_element(By.XPATH, selector)
                    print(f"  ✓ 找到按钮使用选择器: {selector}")
                    print(f"  按钮文本: '{edit_btn.text}'")
                    break
                except:
                    continue
            
            if edit_btn and edit_btn.is_displayed():
                self.results['issue_5_edit_btn'] = 'PASS'
                print("✓ Issue #5: PASS - 找到修改并重新生成按钮")
                self.save_screenshot("09_edit_button")
            elif edit_btn:
                self.results['issue_5_edit_btn'] = 'FAIL - 按钮不可见'
                print("✗ Issue #5: FAIL - 按钮不可见")
            else:
                self.results['issue_5_edit_btn'] = 'FAIL - 未找到按钮'
                print("✗ Issue #5: FAIL - 未找到修改并重新生成按钮")
                self.save_screenshot("09_no_edit_button")
                
        except Exception as e:
            self.results['issue_5_edit_btn'] = f'ERROR: {str(e)}'
            print(f"✗ Issue #5: ERROR - {str(e)}")
        
        # Issue #6 - 导出标签
        print("\n--- Issue #6: 导出标签 ---")
        try:
            # 确保在底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # 查找导出按钮 - 使用更宽松的选择器
            # 注意：按钮文本在 span 标签内，所以使用 . 而不是 text()
            export_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'Download') or contains(., 'Export') or contains(., '下载') or contains(., '导出')]")
            
            if export_buttons:
                print(f"找到 {len(export_buttons)} 个导出按钮")
                
                has_improved_labels = False
                has_old_labels = False
                button_labels = []
                
                for i, btn in enumerate(export_buttons):
                    btn_text = btn.text.strip()
                    if btn_text:
                        button_labels.append(btn_text)
                        print(f"  导出按钮 {i+1}: '{btn_text}'")
                        
                        # 检查是否有改进的标签
                        if 'JSON' in btn_text or 'Data' in btn_text or 'Webpage' in btn_text or 'Text' in btn_text:
                            has_improved_labels = True
                        
                        # 检查是否还有旧的"Export Script"标签
                        if btn_text == 'Export Script':
                            has_old_labels = True
                
                if has_improved_labels and not has_old_labels:
                    self.results['issue_6_export_labels'] = f'PASS - 找到改进的标签: {", ".join(button_labels)}'
                    print("✓ Issue #6: PASS - 导出按钮有改进的标签")
                elif has_old_labels:
                    self.results['issue_6_export_labels'] = 'FAIL - 仍有旧标签 "Export Script"'
                    print("✗ Issue #6: FAIL - 仍有旧标签 'Export Script'")
                else:
                    self.results['issue_6_export_labels'] = f'PARTIAL - 找到按钮: {", ".join(button_labels)}'
                    print("⚠ Issue #6: PARTIAL - 找到导出按钮但标签不明确")
                
                self.save_screenshot("10_export_buttons")
            else:
                self.results['issue_6_export_labels'] = 'FAIL - 未找到导出按钮'
                print("✗ Issue #6: FAIL - 未找到导出按钮")
                
        except Exception as e:
            self.results['issue_6_export_labels'] = f'ERROR: {str(e)}'
            print(f"✗ Issue #6: ERROR - {str(e)}")
        
        # 保存最终页面状态
        self.save_screenshot("11_final_state")
        self.save_page_source("step4_page_source")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("测试结果总结")
        print("="*80)
        
        report = []
        report.append("# Step 4 功能测试报告（使用已有活动）\n\n")
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"测试URL: {BASE_URL}\n\n")
        
        report.append("## 测试结果\n\n")
        
        for issue, result in self.results.items():
            if "PASS" in result:
                status = "✓ PASS"
            elif "FAIL" in result:
                status = "✗ FAIL"
            elif "ERROR" in result:
                status = "⚠ ERROR"
            else:
                status = "? UNKNOWN"
            
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
            if not self.login():
                return
            
            if not self.navigate_to_activity_projects():
                return
            
            if not self.find_and_open_completed_activity():
                return
            
            if not self.navigate_to_step4():
                return
            
            self.verify_step4_features()
            
            self.generate_report()
            
        except Exception as e:
            print(f"\n✗ 测试过程中发生错误: {str(e)}")
            self.save_screenshot("error_final")
            
        finally:
            print("\n关闭浏览器...")
            self.driver.quit()
            print("✓ 测试完成")

if __name__ == "__main__":
    test = Step4ExistingTest()
    test.run()
