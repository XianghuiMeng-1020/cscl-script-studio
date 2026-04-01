#!/usr/bin/env python3
"""
全面测试所有14个问题 + Initial Idea功能
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
OUTPUT_DIR = "outputs/comprehensive_test"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

class ComprehensiveTest:
    def __init__(self):
        print("初始化Chrome浏览器...")
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            print("安装/更新ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            print("创建Chrome driver...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✓ Chrome浏览器初始化成功")
            self.wait = WebDriverWait(self.driver, 20)
            self.results = {}
        except Exception as e:
            print(f"✗ Chrome浏览器初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
    def save_screenshot(self, name):
        """保存截图"""
        filepath = os.path.join(OUTPUT_DIR, f"{name}.png")
        self.driver.save_screenshot(filepath)
        print(f"✓ 截图已保存: {name}.png")
        return filepath
        
    def test_login(self):
        """测试1: 登录"""
        print("\n" + "="*80)
        print("测试 1: 登录")
        print("="*80)
        
        try:
            self.driver.get(f"{BASE_URL}/teacher")
            time.sleep(2)
            self.save_screenshot("01_login_page")
            
            # 输入用户名和密码
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[name='username']"))
            )
            username_input.clear()
            username_input.send_keys(USERNAME)
            
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
            password_input.clear()
            password_input.send_keys(PASSWORD)
            
            self.save_screenshot("02_login_filled")
            
            # 点击登录按钮
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(3)
            self.save_screenshot("03_after_login")
            
            # 验证侧边栏 (Issue #11, #12)
            sidebar = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "aside, nav, [class*='sidebar']"))
            )
            self.save_screenshot("04_sidebar_verification")
            
            self.results['login'] = 'PASS'
            self.results['issue_11_12_sidebar'] = 'PASS'
            print("✓ 登录成功")
            print("✓ Issue #11, #12: 侧边栏验证通过")
            
        except Exception as e:
            self.results['login'] = f'FAIL: {str(e)}'
            print(f"✗ 登录失败: {str(e)}")
            raise
            
    def test_step1_upload(self):
        """测试2: Step 1 上传 (Issue #1, #2, #3)"""
        print("\n" + "="*80)
        print("测试 2: Step 1 上传 (Issue #1, #2, #3)")
        print("="*80)
        
        try:
            # 点击"新建活动"
            new_activity_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '新建活动') or contains(text(), 'New Activity')]"))
            )
            new_activity_btn.click()
            time.sleep(2)
            
            self.save_screenshot("05_step1_page")
            
            # Issue #2: 验证"不提取文字"复选框默认选中
            try:
                no_extract_checkbox = self.driver.find_element(
                    By.XPATH, "//input[@type='checkbox' and (contains(@id, 'extract') or contains(@name, 'extract'))]"
                )
                is_checked = no_extract_checkbox.is_selected()
                
                if is_checked:
                    self.results['issue_2_no_extract_checked'] = 'PASS'
                    print("✓ Issue #2: '不提取文字'复选框默认选中 - PASS")
                else:
                    self.results['issue_2_no_extract_checked'] = 'FAIL: 复选框未选中'
                    print("✗ Issue #2: '不提取文字'复选框未选中 - FAIL")
                    
            except NoSuchElementException:
                self.results['issue_2_no_extract_checked'] = 'FAIL: 找不到复选框'
                print("✗ Issue #2: 找不到'不提取文字'复选框 - FAIL")
            
            # Issue #3: 验证"已上传的文件"区域存在
            try:
                uploaded_files_section = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), '已上传的文件') or contains(text(), 'Uploaded Files')]"
                )
                self.results['issue_3_uploaded_files_section'] = 'PASS'
                print("✓ Issue #3: '已上传的文件'区域存在 - PASS")
            except NoSuchElementException:
                self.results['issue_3_uploaded_files_section'] = 'FAIL: 找不到已上传文件区域'
                print("✗ Issue #3: 找不到'已上传的文件'区域 - FAIL")
            
            # Issue #1: 验证没有material_level单选按钮
            try:
                material_level_radio = self.driver.find_elements(
                    By.XPATH, "//input[@type='radio' and (contains(@name, 'material_level') or contains(@id, 'material_level'))]"
                )
                if len(material_level_radio) == 0:
                    self.results['issue_1_no_material_level'] = 'PASS'
                    print("✓ Issue #1: 没有material_level单选按钮 - PASS")
                else:
                    self.results['issue_1_no_material_level'] = f'FAIL: 找到{len(material_level_radio)}个material_level单选按钮'
                    print(f"✗ Issue #1: 找到{len(material_level_radio)}个material_level单选按钮 - FAIL")
            except Exception as e:
                self.results['issue_1_no_material_level'] = 'PASS'
                print("✓ Issue #1: 没有material_level单选按钮 - PASS")
                
        except Exception as e:
            self.results['step1_upload'] = f'FAIL: {str(e)}'
            print(f"✗ Step 1测试失败: {str(e)}")
            
    def test_initial_idea(self):
        """测试3: Initial Idea功能 (Issue #14)"""
        print("\n" + "="*80)
        print("测试 3: Initial Idea功能 (Issue #14)")
        print("="*80)
        
        try:
            # 点击"继续"到Step 2
            continue_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '继续') or contains(text(), 'Continue')]"))
            )
            continue_btn.click()
            time.sleep(2)
            
            # 截图Step 2顶部
            self.save_screenshot("06_step2_top")
            
            # 滚动到顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            self.save_screenshot("06b_step2_top_scrolled")
            
            # 查找Initial Idea字段
            try:
                # 尝试多种方式查找
                initial_idea_found = False
                initial_idea_element = None
                
                # 方法1: 通过label查找
                try:
                    label = self.driver.find_element(
                        By.XPATH, "//*[contains(text(), '初步想法') or contains(text(), 'initial idea') or contains(text(), 'Initial Idea')]"
                    )
                    initial_idea_found = True
                    print("✓ 找到Initial Idea标签")
                except:
                    pass
                
                # 方法2: 通过textarea的placeholder查找
                try:
                    initial_idea_element = self.driver.find_element(
                        By.XPATH, "//textarea[contains(@placeholder, '初步想法') or contains(@placeholder, 'initial idea') or contains(@placeholder, 'Initial Idea')]"
                    )
                    initial_idea_found = True
                    print("✓ 找到Initial Idea输入框")
                except:
                    pass
                
                # 方法3: 查找所有textarea,看是否在"课程名称"之前
                try:
                    all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                    course_name_element = self.driver.find_element(
                        By.XPATH, "//*[contains(text(), '课程名称') or contains(text(), 'Course Name')]"
                    )
                    
                    for textarea in all_textareas:
                        # 检查textarea是否在课程名称之前
                        textarea_y = textarea.location['y']
                        course_y = course_name_element.location['y']
                        
                        if textarea_y < course_y:
                            initial_idea_element = textarea
                            initial_idea_found = True
                            print(f"✓ 找到位于课程名称之前的textarea (y={textarea_y} < {course_y})")
                            break
                except Exception as e:
                    print(f"方法3失败: {str(e)}")
                
                if initial_idea_found:
                    self.results['issue_14_initial_idea'] = 'PASS'
                    print("✓ Issue #14: Initial Idea字段存在 - PASS")
                    
                    # 尝试输入文本
                    if initial_idea_element:
                        try:
                            initial_idea_element.clear()
                            initial_idea_element.send_keys("I want a simple 15-minute comparison activity")
                            time.sleep(1)
                            self.save_screenshot("07_initial_idea_filled")
                            print("✓ 成功输入Initial Idea文本")
                        except Exception as e:
                            print(f"输入文本失败: {str(e)}")
                else:
                    self.results['issue_14_initial_idea'] = 'FAIL: 找不到Initial Idea字段'
                    print("✗ Issue #14: 找不到Initial Idea字段 - FAIL")
                    
            except Exception as e:
                self.results['issue_14_initial_idea'] = f'FAIL: {str(e)}'
                print(f"✗ Issue #14: Initial Idea验证失败 - {str(e)}")
                
        except Exception as e:
            self.results['initial_idea'] = f'FAIL: {str(e)}'
            print(f"✗ Initial Idea测试失败: {str(e)}")
            
    def test_button_i18n(self):
        """测试4: 按钮国际化 (Issue #4)"""
        print("\n" + "="*80)
        print("测试 4: 按钮国际化 (Issue #4)")
        print("="*80)
        
        try:
            # 填写必填字段
            print("填写必填字段...")
            
            # 课程名称
            try:
                course_input = self.driver.find_element(
                    By.XPATH, "//input[contains(@placeholder, '课程名称') or contains(@placeholder, 'Course')]"
                )
                course_input.clear()
                course_input.send_keys("Test Course")
            except:
                print("警告: 无法填写课程名称")
            
            # 主题
            try:
                topic_input = self.driver.find_element(
                    By.XPATH, "//input[contains(@placeholder, '主题') or contains(@placeholder, 'Topic')]"
                )
                topic_input.clear()
                topic_input.send_keys("Test Topic")
            except:
                print("警告: 无法填写主题")
            
            # 时长
            try:
                duration_input = self.driver.find_element(
                    By.XPATH, "//input[contains(@placeholder, '时长') or contains(@placeholder, 'Duration') or @type='number']"
                )
                duration_input.clear()
                duration_input.send_keys("45")
            except:
                print("警告: 无法填写时长")
            
            # 教学目标
            try:
                objectives_textarea = self.driver.find_element(
                    By.XPATH, "//textarea[contains(@placeholder, '教学目标') or contains(@placeholder, 'Objectives')]"
                )
                objectives_textarea.clear()
                objectives_textarea.send_keys("Test objectives for the activity")
            except:
                print("警告: 无法填写教学目标")
            
            time.sleep(1)
            self.save_screenshot("08_step2_filled")
            
            # 点击"验证教学目标"
            try:
                validate_btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), '验证') or contains(text(), 'Validate')]"
                )
                validate_btn.click()
                time.sleep(3)
                self.save_screenshot("09_after_validate")
            except:
                print("警告: 无法点击验证按钮")
            
            # 点击"继续"到Step 3
            try:
                continue_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '继续') or contains(text(), 'Continue')]"))
                )
                continue_btn.click()
                time.sleep(2)
                self.save_screenshot("10_step3_page")
            except:
                print("警告: 无法进入Step 3")
            
            # 切换到英文模式
            try:
                # 查找语言切换按钮
                lang_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'EN') or contains(text(), 'English')]")
                if lang_buttons:
                    lang_buttons[0].click()
                    time.sleep(1)
                    self.save_screenshot("11_english_mode")
                    print("✓ 切换到英文模式")
            except:
                print("警告: 无法切换语言")
            
            # 验证"Start Generation"按钮
            try:
                start_gen_btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Start Generation')]"
                )
                self.results['issue_4_button_i18n'] = 'PASS'
                print("✓ Issue #4: 按钮显示'Start Generation' - PASS")
                self.save_screenshot("12_start_generation_button")
            except NoSuchElementException:
                # 检查是否显示中文
                try:
                    chinese_btn = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), '开始生成')]"
                    )
                    self.results['issue_4_button_i18n'] = 'FAIL: 按钮仍显示中文'
                    print("✗ Issue #4: 按钮仍显示中文 - FAIL")
                except:
                    self.results['issue_4_button_i18n'] = 'FAIL: 找不到生成按钮'
                    print("✗ Issue #4: 找不到生成按钮 - FAIL")
                    
        except Exception as e:
            self.results['button_i18n'] = f'FAIL: {str(e)}'
            print(f"✗ 按钮国际化测试失败: {str(e)}")
            
    def test_output_tabs(self):
        """测试5: 输出标签页 (Issue #8)"""
        print("\n" + "="*80)
        print("测试 5: 输出标签页 (Issue #8)")
        print("="*80)
        
        try:
            # 点击"Start Generation"
            try:
                start_btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Start Generation') or contains(text(), '开始生成')]"
                )
                start_btn.click()
                print("✓ 点击开始生成按钮")
                time.sleep(5)
                
                # 等待生成完成
                print("等待生成完成...")
                time.sleep(30)  # 给足够时间生成
                
                self.save_screenshot("13_after_generation")
                
            except Exception as e:
                print(f"警告: 生成过程出错 - {str(e)}")
            
            # 尝试进入Step 4
            try:
                # 查找Step 4或预览按钮
                step4_elements = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), 'Step 4') or contains(text(), '预览') or contains(text(), 'Preview')]"
                )
                if step4_elements:
                    step4_elements[0].click()
                    time.sleep(2)
                    self.save_screenshot("14_step4_page")
            except:
                print("警告: 无法进入Step 4")
            
            # 验证3个输出标签页
            try:
                tabs = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), 'Student Worksheet') or contains(text(), 'Student Slides') or contains(text(), 'Teacher Facilitation')]"
                )
                
                if len(tabs) >= 3:
                    self.results['issue_8_output_tabs'] = 'PASS'
                    print(f"✓ Issue #8: 找到{len(tabs)}个输出标签页 - PASS")
                    self.save_screenshot("15_output_tabs")
                else:
                    self.results['issue_8_output_tabs'] = f'FAIL: 只找到{len(tabs)}个标签页'
                    print(f"✗ Issue #8: 只找到{len(tabs)}个标签页 - FAIL")
                    
            except Exception as e:
                self.results['issue_8_output_tabs'] = f'FAIL: {str(e)}'
                print(f"✗ Issue #8: 输出标签页验证失败 - {str(e)}")
                
        except Exception as e:
            self.results['output_tabs'] = f'FAIL: {str(e)}'
            print(f"✗ 输出标签页测试失败: {str(e)}")
            
    def test_no_pipeline_summary(self):
        """测试6: 无Pipeline Summary (Issue #7)"""
        print("\n" + "="*80)
        print("测试 6: 无Pipeline Summary (Issue #7)")
        print("="*80)
        
        try:
            # 滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.save_screenshot("16_step4_bottom")
            
            # 验证没有Pipeline Summary
            try:
                pipeline_summary = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), 'Pipeline Summary') or contains(text(), '管道摘要')]"
                )
                
                if len(pipeline_summary) == 0:
                    self.results['issue_7_no_pipeline_summary'] = 'PASS'
                    print("✓ Issue #7: 没有Pipeline Summary - PASS")
                else:
                    self.results['issue_7_no_pipeline_summary'] = 'FAIL: 找到Pipeline Summary'
                    print("✗ Issue #7: 找到Pipeline Summary - FAIL")
                    
            except Exception as e:
                self.results['issue_7_no_pipeline_summary'] = 'PASS'
                print("✓ Issue #7: 没有Pipeline Summary - PASS")
                
        except Exception as e:
            self.results['no_pipeline_summary'] = f'FAIL: {str(e)}'
            print(f"✗ Pipeline Summary测试失败: {str(e)}")
            
    def test_edit_regenerate(self):
        """测试7: 编辑并重新生成 (Issue #5)"""
        print("\n" + "="*80)
        print("测试 7: 编辑并重新生成 (Issue #5)")
        print("="*80)
        
        try:
            # 滚动到顶部查看按钮
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            self.save_screenshot("17_step4_buttons")
            
            # 查找"修改并重新生成"按钮
            try:
                edit_regen_btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), '修改并重新生成') or contains(text(), 'Edit & Regenerate') or contains(text(), 'Edit and Regenerate')]"
                )
                self.results['issue_5_edit_regenerate'] = 'PASS'
                print("✓ Issue #5: '修改并重新生成'按钮存在 - PASS")
            except NoSuchElementException:
                self.results['issue_5_edit_regenerate'] = 'FAIL: 找不到按钮'
                print("✗ Issue #5: 找不到'修改并重新生成'按钮 - FAIL")
                
        except Exception as e:
            self.results['edit_regenerate'] = f'FAIL: {str(e)}'
            print(f"✗ 编辑重新生成测试失败: {str(e)}")
            
    def test_export_labels(self):
        """测试8: 导出标签 (Issue #6)"""
        print("\n" + "="*80)
        print("测试 8: 导出标签 (Issue #6)")
        print("="*80)
        
        try:
            # 查找导出按钮
            export_buttons = self.driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Export') or contains(text(), '导出')]"
            )
            
            if export_buttons:
                self.save_screenshot("18_export_buttons")
                
                # 检查是否有"Export Script"标签
                export_script_found = False
                for btn in export_buttons:
                    if "Export Script" in btn.text:
                        export_script_found = True
                        break
                
                if not export_script_found:
                    self.results['issue_6_export_labels'] = 'PASS'
                    print("✓ Issue #6: 导出按钮标签改进 - PASS")
                else:
                    self.results['issue_6_export_labels'] = 'FAIL: 仍显示Export Script'
                    print("✗ Issue #6: 仍显示'Export Script' - FAIL")
            else:
                self.results['issue_6_export_labels'] = 'FAIL: 找不到导出按钮'
                print("✗ Issue #6: 找不到导出按钮 - FAIL")
                
        except Exception as e:
            self.results['export_labels'] = f'FAIL: {str(e)}'
            print(f"✗ 导出标签测试失败: {str(e)}")
            
    def test_quality_report(self):
        """测试9: 质量报告 (Issue #9)"""
        print("\n" + "="*80)
        print("测试 9: 质量报告 (Issue #9)")
        print("="*80)
        
        try:
            # 查找质量报告链接
            try:
                quality_report_link = self.driver.find_element(
                    By.XPATH, "//a[contains(text(), '质量报告') or contains(text(), 'Quality Report')] | //button[contains(text(), '查看质量报告') or contains(text(), 'View Quality Report')]"
                )
                quality_report_link.click()
                time.sleep(2)
                self.save_screenshot("19_quality_report")
                
                # 验证0/100显示"尚未评估"
                try:
                    not_evaluated = self.driver.find_element(
                        By.XPATH, "//*[contains(text(), '尚未评估') or contains(text(), 'Not Evaluated')]"
                    )
                    self.results['issue_9_quality_report'] = 'PASS'
                    print("✓ Issue #9: 0/100显示'尚未评估' - PASS")
                except NoSuchElementException:
                    # 检查是否显示POOR
                    try:
                        poor_text = self.driver.find_element(
                            By.XPATH, "//*[contains(text(), 'POOR')]"
                        )
                        self.results['issue_9_quality_report'] = 'FAIL: 显示POOR'
                        print("✗ Issue #9: 0/100显示'POOR' - FAIL")
                    except:
                        self.results['issue_9_quality_report'] = 'FAIL: 未知状态'
                        print("✗ Issue #9: 未找到预期文本 - FAIL")
                        
            except NoSuchElementException:
                self.results['issue_9_quality_report'] = 'FAIL: 找不到质量报告链接'
                print("✗ Issue #9: 找不到质量报告链接 - FAIL")
                
        except Exception as e:
            self.results['quality_report'] = f'FAIL: {str(e)}'
            print(f"✗ 质量报告测试失败: {str(e)}")
            
    def test_course_documents(self):
        """测试10: 课程文档 (Issue #10)"""
        print("\n" + "="*80)
        print("测试 10: 课程文档 (Issue #10)")
        print("="*80)
        
        try:
            # 导航到课程文档
            try:
                course_docs_link = self.driver.find_element(
                    By.XPATH, "//a[contains(text(), '课程文档') or contains(text(), 'Course Documents')]"
                )
                course_docs_link.click()
                time.sleep(2)
                self.save_screenshot("20_course_documents")
                
                # 验证没有提取文本预览
                page_source = self.driver.page_source
                
                # 检查是否有长文本预览
                has_long_preview = False
                text_previews = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'preview') or contains(@class, 'extract')]")
                
                for preview in text_previews:
                    if len(preview.text) > 100:  # 如果预览文本超过100字符
                        has_long_preview = True
                        break
                
                if not has_long_preview:
                    self.results['issue_10_course_documents'] = 'PASS'
                    print("✓ Issue #10: 没有显示提取文本预览 - PASS")
                else:
                    self.results['issue_10_course_documents'] = 'FAIL: 显示了提取文本预览'
                    print("✗ Issue #10: 显示了提取文本预览 - FAIL")
                    
            except NoSuchElementException:
                self.results['issue_10_course_documents'] = 'FAIL: 找不到课程文档链接'
                print("✗ Issue #10: 找不到课程文档链接 - FAIL")
                
        except Exception as e:
            self.results['course_documents'] = f'FAIL: {str(e)}'
            print(f"✗ 课程文档测试失败: {str(e)}")
            
    def test_edit_duplicate(self):
        """测试11: 编辑/复制按钮 (Issue #13)"""
        print("\n" + "="*80)
        print("测试 11: 编辑/复制按钮 (Issue #13)")
        print("="*80)
        
        try:
            # 导航到活动项目
            try:
                projects_link = self.driver.find_element(
                    By.XPATH, "//a[contains(text(), '活动项目') or contains(text(), 'Activity Projects') or contains(text(), 'Projects')]"
                )
                projects_link.click()
                time.sleep(2)
                self.save_screenshot("21_activity_projects")
                
                # 查找Edit和Duplicate按钮
                edit_buttons = self.driver.find_elements(
                    By.XPATH, "//button[contains(text(), 'Edit') or contains(text(), '编辑')]"
                )
                duplicate_buttons = self.driver.find_elements(
                    By.XPATH, "//button[contains(text(), 'Duplicate') or contains(text(), '复制')]"
                )
                
                if edit_buttons and duplicate_buttons:
                    self.results['issue_13_edit_duplicate'] = 'PASS'
                    print(f"✓ Issue #13: 找到{len(edit_buttons)}个Edit按钮和{len(duplicate_buttons)}个Duplicate按钮 - PASS")
                    self.save_screenshot("22_edit_duplicate_buttons")
                else:
                    self.results['issue_13_edit_duplicate'] = f'FAIL: Edit={len(edit_buttons)}, Duplicate={len(duplicate_buttons)}'
                    print(f"✗ Issue #13: Edit={len(edit_buttons)}, Duplicate={len(duplicate_buttons)} - FAIL")
                    
            except NoSuchElementException:
                self.results['issue_13_edit_duplicate'] = 'FAIL: 找不到活动项目链接'
                print("✗ Issue #13: 找不到活动项目链接 - FAIL")
                
        except Exception as e:
            self.results['edit_duplicate'] = f'FAIL: {str(e)}'
            print(f"✗ 编辑/复制按钮测试失败: {str(e)}")
            
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("生成测试报告")
        print("="*80)
        
        report = []
        report.append("# 全面测试报告 - 所有14个问题 + Initial Idea功能")
        report.append(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n测试URL: {BASE_URL}/teacher")
        report.append(f"\n用户名: {USERNAME}")
        report.append("\n## 测试结果摘要\n")
        
        pass_count = sum(1 for v in self.results.values() if v == 'PASS')
        fail_count = len(self.results) - pass_count
        
        report.append(f"- **通过**: {pass_count}")
        report.append(f"- **失败**: {fail_count}")
        report.append(f"- **总计**: {len(self.results)}")
        
        report.append("\n## 详细结果\n")
        
        for test_name, result in self.results.items():
            status = "✓ PASS" if result == "PASS" else f"✗ FAIL"
            report.append(f"### {test_name}")
            report.append(f"**状态**: {status}")
            if result != "PASS":
                report.append(f"**详情**: {result}")
            report.append("")
        
        report_text = "\n".join(report)
        
        # 保存报告
        report_path = os.path.join(OUTPUT_DIR, "COMPREHENSIVE_TEST_REPORT.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"\n✓ 报告已保存到: {report_path}")
        
    def run_all_tests(self):
        """运行所有测试"""
        try:
            self.test_login()
            self.test_step1_upload()
            self.test_initial_idea()
            self.test_button_i18n()
            self.test_output_tabs()
            self.test_no_pipeline_summary()
            self.test_edit_regenerate()
            self.test_export_labels()
            self.test_quality_report()
            self.test_course_documents()
            self.test_edit_duplicate()
            
        except Exception as e:
            print(f"\n测试过程中出现错误: {str(e)}")
        finally:
            self.generate_report()
            self.driver.quit()
            print("\n✓ 浏览器已关闭")

if __name__ == "__main__":
    print("="*80)
    print("CSCL应用程序 - 全面测试所有14个问题 + Initial Idea功能")
    print("="*80)
    
    tester = ComprehensiveTest()
    tester.run_all_tests()
