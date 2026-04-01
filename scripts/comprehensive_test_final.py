#!/usr/bin/env python3
"""
全面测试所有14个问题 + Initial Idea功能 - 最终版
使用正确的选择器
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
OUTPUT_DIR = "outputs/comprehensive_test_final"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

class ComprehensiveTestFinal:
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
        self.wait = WebDriverWait(self.driver, 20)
        self.results = {}
            
    def save_screenshot(self, name):
        """保存截图"""
        filepath = os.path.join(OUTPUT_DIR, f"{name}.png")
        self.driver.save_screenshot(filepath)
        print(f"✓ 截图: {name}.png")
        return filepath
        
    def test_login_and_sidebar(self):
        """测试1: 登录和侧边栏 (Issue #11, #12)"""
        print("\n" + "="*80)
        print("测试 1: 登录和侧边栏 (Issue #11, #12)")
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
            
            # 验证侧边栏
            sidebar = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "aside.sidebar")))
            self.save_screenshot("04_sidebar")
            
            # 检查侧边栏链接
            sidebar_links = sidebar.find_elements(By.TAG_NAME, "a")
            print(f"✓ 找到 {len(sidebar_links)} 个侧边栏链接")
            
            self.results['login'] = 'PASS'
            self.results['issue_11_12_sidebar'] = 'PASS'
            print("✓ Issue #11, #12: 侧边栏验证通过")
            
        except Exception as e:
            self.results['login'] = f'FAIL: {str(e)}'
            print(f"✗ 登录失败: {str(e)}")
            raise
            
    def test_activity_projects(self):
        """测试2: 活动项目 (Issue #13)"""
        print("\n" + "="*80)
        print("测试 2: 活动项目 (Issue #13 - Edit/Duplicate按钮)")
        print("="*80)
        
        try:
            # 点击Activity Projects链接 (使用data-view属性)
            projects_link = self.driver.find_element(By.CSS_SELECTOR, "a[data-view='scripts']")
            projects_link.click()
            time.sleep(2)
            self.save_screenshot("05_activity_projects")
            
            # 查找Edit和Duplicate按钮
            page_source = self.driver.page_source
            
            # 查找所有按钮
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            edit_buttons = [btn for btn in all_buttons if 'Edit' in btn.text or '编辑' in btn.text]
            duplicate_buttons = [btn for btn in all_buttons if 'Duplicate' in btn.text or '复制' in btn.text]
            
            print(f"找到 {len(edit_buttons)} 个Edit按钮")
            print(f"找到 {len(duplicate_buttons)} 个Duplicate按钮")
            
            if len(edit_buttons) > 0 and len(duplicate_buttons) > 0:
                self.results['issue_13_edit_duplicate'] = 'PASS'
                print("✓ Issue #13: Edit和Duplicate按钮存在 - PASS")
            else:
                self.results['issue_13_edit_duplicate'] = f'FAIL: Edit={len(edit_buttons)}, Duplicate={len(duplicate_buttons)}'
                print(f"✗ Issue #13: Edit={len(edit_buttons)}, Duplicate={len(duplicate_buttons)} - FAIL")
                
        except Exception as e:
            self.results['issue_13_edit_duplicate'] = f'FAIL: {str(e)}'
            print(f"✗ Issue #13: {str(e)}")
            
    def test_course_documents(self):
        """测试3: 课程文档 (Issue #10)"""
        print("\n" + "="*80)
        print("测试 3: 课程文档 (Issue #10 - 无提取文本预览)")
        print("="*80)
        
        try:
            docs_link = self.driver.find_element(By.CSS_SELECTOR, "a[data-view='documents']")
            docs_link.click()
            time.sleep(2)
            self.save_screenshot("06_course_documents")
            
            # 检查是否有长文本预览
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # 查找可能的长文本块
            all_divs = self.driver.find_elements(By.TAG_NAME, "div")
            long_text_found = False
            
            for div in all_divs:
                try:
                    if len(div.text) > 500:  # 如果某个div包含超过500字符
                        # 检查是否是提取的文本内容
                        if any(keyword in div.get_attribute('class') or '' for keyword in ['extract', 'content', 'preview']):
                            long_text_found = True
                            print(f"发现长文本预览: {len(div.text)} 字符")
                            break
                except:
                    pass
            
            if not long_text_found:
                self.results['issue_10_course_documents'] = 'PASS'
                print("✓ Issue #10: 没有显示提取文本预览 - PASS")
            else:
                self.results['issue_10_course_documents'] = 'FAIL: 显示了提取文本预览'
                print("✗ Issue #10: 显示了提取文本预览 - FAIL")
                
        except Exception as e:
            self.results['issue_10_course_documents'] = f'FAIL: {str(e)}'
            print(f"✗ Issue #10: {str(e)}")
            
    def test_quality_reports(self):
        """测试4: 质量报告 (Issue #9)"""
        print("\n" + "="*80)
        print("测试 4: 质量报告 (Issue #9 - 0/100显示'尚未评估')")
        print("="*80)
        
        try:
            quality_link = self.driver.find_element(By.CSS_SELECTOR, "a[data-view='quality']")
            quality_link.click()
            time.sleep(2)
            self.save_screenshot("07_quality_reports")
            
            page_source = self.driver.page_source
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            has_not_evaluated = ("尚未评估" in page_text or 
                                "Not Evaluated" in page_text or 
                                "Not evaluated" in page_text or
                                "not evaluated" in page_text.lower())
            has_poor = "POOR" in page_text
            
            if has_not_evaluated and not has_poor:
                self.results['issue_9_quality_report'] = 'PASS'
                print("✓ Issue #9: 0/100显示'尚未评估',没有'POOR' - PASS")
            elif has_poor:
                self.results['issue_9_quality_report'] = 'FAIL: 显示POOR'
                print("✗ Issue #9: 显示'POOR' - FAIL")
            else:
                self.results['issue_9_quality_report'] = 'PARTIAL: 未找到明确标识'
                print("? Issue #9: 未找到'尚未评估'或'POOR'")
                
        except Exception as e:
            self.results['issue_9_quality_report'] = f'FAIL: {str(e)}'
            print(f"✗ Issue #9: {str(e)}")
            
    def test_new_activity_step1(self):
        """测试5: Step 1 (Issue #1, #2, #3)"""
        print("\n" + "="*80)
        print("测试 5: Step 1 - 上传 (Issue #1, #2, #3)")
        print("="*80)
        
        try:
            # 返回Dashboard
            dashboard_link = self.driver.find_element(By.CSS_SELECTOR, "a[data-view='dashboard']")
            dashboard_link.click()
            time.sleep(2)
            
            # 点击New Activity按钮
            new_activity_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary"))
            )
            new_activity_btn.click()
            time.sleep(3)
            self.save_screenshot("08_step1_page")
            
            # Issue #2: 验证"不提取文字"复选框
            print("\n检查 Issue #2: '不提取文字'复选框...")
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            print(f"找到 {len(checkboxes)} 个复选框")
            
            no_extract_found = False
            no_extract_checked = False
            
            for cb in checkboxes:
                try:
                    # 获取复选框的label或父元素文本
                    parent = cb.find_element(By.XPATH, "./..")
                    parent_text = parent.text.lower()
                    
                    if "extract" in parent_text or "提取" in parent_text:
                        no_extract_found = True
                        no_extract_checked = cb.is_selected()
                        print(f"找到提取文字相关复选框: '{parent.text}', 选中={no_extract_checked}")
                        break
                except:
                    pass
            
            if no_extract_found and no_extract_checked:
                self.results['issue_2_no_extract'] = 'PASS'
                print("✓ Issue #2: '不提取文字'复选框默认选中 - PASS")
            else:
                self.results['issue_2_no_extract'] = f'FAIL: 找到={no_extract_found}, 选中={no_extract_checked}'
                print(f"✗ Issue #2: 找到={no_extract_found}, 选中={no_extract_checked} - FAIL")
            
            # Issue #3: 验证"已上传的文件"区域
            print("\n检查 Issue #3: '已上传的文件'区域...")
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            has_uploaded_section = ("已上传" in page_text or 
                                   "Uploaded" in page_text or
                                   "uploaded" in page_text.lower())
            
            if has_uploaded_section:
                self.results['issue_3_uploaded_files'] = 'PASS'
                print("✓ Issue #3: '已上传的文件'区域存在 - PASS")
            else:
                self.results['issue_3_uploaded_files'] = 'FAIL: 找不到已上传文件区域'
                print("✗ Issue #3: 找不到'已上传的文件'区域 - FAIL")
            
            # Issue #1: 验证没有material_level单选按钮
            print("\n检查 Issue #1: 无material_level单选按钮...")
            radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            material_level_radios = []
            
            for radio in radio_buttons:
                name = radio.get_attribute('name') or ''
                id_attr = radio.get_attribute('id') or ''
                if 'material_level' in name.lower() or 'material_level' in id_attr.lower():
                    material_level_radios.append(radio)
            
            if len(material_level_radios) == 0:
                self.results['issue_1_no_material_level'] = 'PASS'
                print("✓ Issue #1: 没有material_level单选按钮 - PASS")
            else:
                self.results['issue_1_no_material_level'] = f'FAIL: 找到{len(material_level_radios)}个'
                print(f"✗ Issue #1: 找到{len(material_level_radios)}个material_level单选按钮 - FAIL")
            
            return True
            
        except Exception as e:
            print(f"✗ Step 1测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def test_step2_initial_idea(self):
        """测试6: Step 2 Initial Idea (Issue #14)"""
        print("\n" + "="*80)
        print("测试 6: Step 2 - Initial Idea (Issue #14)")
        print("="*80)
        
        try:
            # 点击Continue到Step 2
            continue_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue') or contains(text(), '继续')]")
            if continue_btns:
                continue_btns[0].click()
                time.sleep(2)
                self.save_screenshot("09_step2_page")
            else:
                print("警告: 找不到Continue按钮")
                return False
            
            # 滚动到顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            self.save_screenshot("10_step2_top")
            
            # 查找Initial Idea字段
            print("\n检查 Issue #14: Initial Idea字段...")
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            has_initial_idea = ("初步想法" in page_text or 
                               "initial idea" in page_text.lower() or
                               "Initial Idea" in page_text)
            
            # 也检查是否有对应的textarea
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            print(f"找到 {len(textareas)} 个textarea")
            
            # 尝试在第一个textarea输入
            initial_idea_textarea = None
            if textareas:
                try:
                    # 检查第一个textarea是否在"课程名称"之前
                    first_textarea = textareas[0]
                    textarea_y = first_textarea.location['y']
                    
                    # 查找课程名称元素
                    course_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '课程名称') or contains(text(), 'Course Name')]")
                    if course_elements:
                        course_y = course_elements[0].location['y']
                        if textarea_y < course_y:
                            initial_idea_textarea = first_textarea
                            print(f"✓ 找到位于课程名称之前的textarea (y={textarea_y} < {course_y})")
                except Exception as e:
                    print(f"位置检查失败: {str(e)}")
            
            if has_initial_idea or initial_idea_textarea:
                self.results['issue_14_initial_idea'] = 'PASS'
                print("✓ Issue #14: Initial Idea字段存在 - PASS")
                
                # 尝试输入文本
                if initial_idea_textarea:
                    try:
                        initial_idea_textarea.send_keys("I want a simple 15-minute comparison activity")
                        time.sleep(1)
                        self.save_screenshot("11_initial_idea_filled")
                        print("✓ 成功输入Initial Idea文本")
                    except Exception as e:
                        print(f"输入失败: {str(e)}")
            else:
                self.results['issue_14_initial_idea'] = 'FAIL: 找不到Initial Idea字段'
                print("✗ Issue #14: 找不到Initial Idea字段 - FAIL")
            
            return True
            
        except Exception as e:
            self.results['issue_14_initial_idea'] = f'FAIL: {str(e)}'
            print(f"✗ Issue #14: {str(e)}")
            return False
            
    def test_step3_button_i18n(self):
        """测试7: Step 3 按钮国际化 (Issue #4)"""
        print("\n" + "="*80)
        print("测试 7: Step 3 - 按钮国际化 (Issue #4)")
        print("="*80)
        
        try:
            # 填写必填字段
            print("填写Step 2必填字段...")
            self.fill_step2_fields()
            
            # 验证教学目标
            validate_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Confirm') or contains(text(), '验证')]")
            if validate_btns:
                validate_btns[0].click()
                time.sleep(3)
                print("✓ 点击验证按钮")
            
            # 继续到Step 3
            continue_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue') or contains(text(), '继续')]")
            if continue_btns:
                continue_btns[0].click()
                time.sleep(2)
                self.save_screenshot("12_step3_page")
                print("✓ 进入Step 3")
            
            # 检查Start Generation按钮
            start_gen_btns = self.driver.find_elements(By.XPATH, "//button[text()='Start Generation']")
            
            if start_gen_btns:
                self.results['issue_4_button_i18n'] = 'PASS'
                print("✓ Issue #4: 按钮显示'Start Generation' - PASS")
                self.save_screenshot("13_start_generation_button")
            else:
                # 检查是否显示中文
                chinese_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), '开始生成')]")
                if chinese_btns:
                    self.results['issue_4_button_i18n'] = 'FAIL: 按钮显示中文'
                    print("✗ Issue #4: 按钮显示中文 - FAIL")
                else:
                    self.results['issue_4_button_i18n'] = 'FAIL: 找不到生成按钮'
                    print("✗ Issue #4: 找不到生成按钮 - FAIL")
            
            print("\n注意: Issue #5, #6, #7, #8需要完成生成流程,耗时较长,本次测试跳过")
            
        except Exception as e:
            self.results['issue_4_button_i18n'] = f'FAIL: {str(e)}'
            print(f"✗ Issue #4: {str(e)}")
            
    def fill_step2_fields(self):
        """填写Step 2必填字段"""
        try:
            # 查找所有input和textarea
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            
            # 课程名称
            for inp in inputs:
                placeholder = inp.get_attribute('placeholder') or ''
                if 'course' in placeholder.lower() or '课程' in placeholder:
                    inp.clear()
                    inp.send_keys("Test Course")
                    print("✓ 填写课程名称")
                    break
            
            # 主题
            for inp in inputs:
                placeholder = inp.get_attribute('placeholder') or ''
                if 'topic' in placeholder.lower() or '主题' in placeholder:
                    inp.clear()
                    inp.send_keys("Test Topic")
                    print("✓ 填写主题")
                    break
            
            # 时长
            number_inputs = [inp for inp in inputs if inp.get_attribute('type') == 'number']
            if number_inputs:
                number_inputs[0].clear()
                number_inputs[0].send_keys("45")
                print("✓ 填写时长")
            
            # 教学目标
            for ta in textareas:
                placeholder = ta.get_attribute('placeholder') or ''
                if 'objective' in placeholder.lower() or '目标' in placeholder:
                    ta.clear()
                    ta.send_keys("Test learning objectives for this activity")
                    print("✓ 填写教学目标")
                    break
            
            time.sleep(1)
            self.save_screenshot("14_step2_filled")
            
        except Exception as e:
            print(f"警告: 填写字段时出错 - {str(e)}")
            
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("生成测试报告")
        print("="*80)
        
        report = []
        report.append("# 全面测试报告 - 所有14个问题 + Initial Idea功能")
        report.append(f"\n**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n**测试URL**: {BASE_URL}/teacher")
        report.append("\n---\n")
        
        pass_count = sum(1 for v in self.results.values() if v == 'PASS')
        fail_count = sum(1 for v in self.results.values() if v.startswith('FAIL'))
        partial_count = sum(1 for v in self.results.values() if v.startswith('PARTIAL'))
        
        report.append("## 测试结果摘要\n")
        report.append(f"- ✅ **通过**: {pass_count}")
        report.append(f"- ❌ **失败**: {fail_count}")
        report.append(f"- ⚠️ **部分通过**: {partial_count}")
        report.append(f"- 📊 **总计**: {len(self.results)}")
        
        report.append("\n---\n")
        report.append("## 详细结果\n")
        
        for test_name, result in sorted(self.results.items()):
            if result == "PASS":
                status = "✅ PASS"
            elif result.startswith("FAIL"):
                status = "❌ FAIL"
            elif result.startswith("PARTIAL"):
                status = "⚠️ PARTIAL"
            else:
                status = "❓ UNKNOWN"
                
            report.append(f"### {test_name}")
            report.append(f"**状态**: {status}")
            if result != "PASS":
                report.append(f"**详情**: {result}")
            report.append("")
        
        report_text = "\n".join(report)
        
        # 保存报告
        report_path = os.path.join(OUTPUT_DIR, "TEST_REPORT.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"\n✓ 报告已保存: {report_path}")
        
    def run_all_tests(self):
        """运行所有测试"""
        try:
            self.test_login_and_sidebar()
            self.test_activity_projects()
            self.test_course_documents()
            self.test_quality_reports()
            
            if self.test_new_activity_step1():
                if self.test_step2_initial_idea():
                    self.test_step3_button_i18n()
            
        except Exception as e:
            print(f"\n测试过程中出现错误: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.generate_report()
            self.driver.quit()
            print("\n✓ 测试完成,浏览器已关闭")

if __name__ == "__main__":
    print("="*80)
    print("CSCL应用程序 - 全面测试所有14个问题 + Initial Idea功能")
    print("="*80)
    
    tester = ComprehensiveTestFinal()
    tester.run_all_tests()
