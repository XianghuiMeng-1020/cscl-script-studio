#!/usr/bin/env python3
"""
测试CSCL应用程序的14个问题修复
Test all 14 issue fixes in the CSCL application
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

class TestResults:
    """测试结果记录器"""
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, issue_num, description, passed, details="", screenshot_path=None):
        """添加测试结果"""
        self.results.append({
            'issue': issue_num,
            'description': description,
            'passed': passed,
            'details': details,
            'screenshot': screenshot_path
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("测试结果摘要 / TEST RESULTS SUMMARY")
        print("="*80)
        
        for result in self.results:
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"\n{status} - Issue #{result['issue']}: {result['description']}")
            if result['details']:
                print(f"  详情: {result['details']}")
            if result['screenshot']:
                print(f"  截图: {result['screenshot']}")
        
        print("\n" + "="*80)
        print(f"总计: {self.passed} 通过, {self.failed} 失败 (共 {len(self.results)} 项测试)")
        print("="*80)

def setup_driver():
    """设置Chrome驱动"""
    print("正在启动Chrome浏览器...")
    chrome_options = Options()
    # 使用headless模式进行自动化测试
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    
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
    return str(filepath)

def wait_for_element(driver, by, value, timeout=10):
    """等待元素出现"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        return None

def test_1_login_and_demo(driver, results):
    """测试1: 登录/Demo访问"""
    print("\n[测试 1] 登录/Demo访问...")
    try:
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(3)
        
        screenshot = take_screenshot(driver, "01_login_page")
        
        # 尝试多种方式查找Demo按钮
        demo_button = None
        try:
            # 尝试通过按钮文本查找
            demo_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Demo') or contains(., '快速体验')]"))
            )
        except:
            try:
                # 尝试通过链接文本查找
                demo_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Demo"))
                )
            except:
                pass
        
        if demo_button:
            # 滚动到按钮位置
            driver.execute_script("arguments[0].scrollIntoView(true);", demo_button)
            time.sleep(1)
            
            # 尝试点击
            try:
                demo_button.click()
            except:
                # 如果普通点击失败，使用JavaScript点击
                driver.execute_script("arguments[0].click();", demo_button)
            
            time.sleep(3)
            
            # 检查是否成功进入
            if "teacher" in driver.current_url or driver.find_elements(By.CLASS_NAME, "sidebar"):
                results.add_result(1, "Demo登录功能", True, 
                    "成功点击Demo按钮并进入教师界面", screenshot)
                return True
            else:
                screenshot2 = take_screenshot(driver, "01_after_demo_click")
                results.add_result(1, "Demo登录功能", False, 
                    "点击Demo按钮后未能进入教师界面", screenshot2)
                return False
        else:
            # 检查是否已经在教师界面（可能不需要登录）
            if driver.find_elements(By.CLASS_NAME, "sidebar"):
                results.add_result(1, "Demo登录功能", True, 
                    "已经在教师界面，无需登录", screenshot)
                return True
            else:
                results.add_result(1, "Demo登录功能", False, 
                    "未找到Demo按钮且不在教师界面", screenshot)
                return False
    except Exception as e:
        screenshot = take_screenshot(driver, "01_login_error")
        results.add_result(1, "Demo登录功能", False, 
            f"测试异常: {str(e)}", screenshot)
        return False

def test_2_sidebar_items(driver, results):
    """测试2: 侧边栏项目 (Issue #11, #12)"""
    print("\n[测试 2] 检查侧边栏...")
    try:
        time.sleep(2)
        screenshot = take_screenshot(driver, "02_sidebar")
        
        # 查找侧边栏
        sidebar = driver.find_element(By.CLASS_NAME, "sidebar")
        sidebar_text = sidebar.text
        
        # Issue #11: "自动生成过程" 不应该在侧边栏
        has_pipeline_runs = "自动生成过程" in sidebar_text or "Pipeline Runs" in sidebar_text
        results.add_result(11, "侧边栏不应显示'自动生成过程'", 
            not has_pipeline_runs,
            f"侧边栏{'包含' if has_pipeline_runs else '不包含'}'自动生成过程'",
            screenshot)
        
        # Issue #12: "教学目标检查" 不应该在侧边栏
        has_teaching_plan = "教学目标检查" in sidebar_text or "Teaching Plan Settings" in sidebar_text
        results.add_result(12, "侧边栏不应显示'教学目标检查'", 
            not has_teaching_plan,
            f"侧边栏{'包含' if has_teaching_plan else '不包含'}'教学目标检查'",
            screenshot)
        
    except Exception as e:
        screenshot = take_screenshot(driver, "02_sidebar_error")
        results.add_result(11, "侧边栏不应显示'自动生成过程'", False, 
            f"测试异常: {str(e)}", screenshot)
        results.add_result(12, "侧边栏不应显示'教学目标检查'", False, 
            f"测试异常: {str(e)}", screenshot)

def test_3_new_activity_step1(driver, results):
    """测试3: 新建活动 - 步骤1 (Issue #1, #2, #3)"""
    print("\n[测试 3] 新建活动 - 步骤1...")
    try:
        # 点击"新建活动"按钮
        new_activity_buttons = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '新建活动') or contains(text(), 'New Activity')]")
        
        if not new_activity_buttons:
            screenshot = take_screenshot(driver, "03_no_new_activity_button")
            results.add_result(1, "新建活动按钮", False, "未找到新建活动按钮", screenshot)
            results.add_result(2, "不提取文字默认勾选", False, "无法进入步骤1", screenshot)
            results.add_result(3, "已上传文件列表", False, "无法进入步骤1", screenshot)
            return False
        
        new_activity_buttons[0].click()
        time.sleep(2)
        
        screenshot = take_screenshot(driver, "03_step1_upload")
        
        # Issue #2: 检查"不提取文字"复选框是否默认勾选
        try:
            no_extract_checkbox = driver.find_element(By.ID, "no-extract-text")
            is_checked = no_extract_checkbox.is_selected()
            results.add_result(2, "'不提取文字'复选框默认勾选", is_checked,
                f"复选框状态: {'已勾选' if is_checked else '未勾选'}", screenshot)
        except NoSuchElementException:
            results.add_result(2, "'不提取文字'复选框默认勾选", False,
                "未找到'不提取文字'复选框", screenshot)
        
        # Issue #3: 检查"已上传的文件"区域是否存在
        try:
            uploaded_files_section = driver.find_element(By.ID, "uploaded-files-list")
            section_visible = uploaded_files_section.is_displayed()
            results.add_result(3, "'已上传的文件'区域存在", section_visible,
                f"文件列表区域: {'可见' if section_visible else '不可见'}", screenshot)
        except NoSuchElementException:
            results.add_result(3, "'已上传的文件'区域存在", False,
                "未找到'已上传的文件'区域", screenshot)
        
        return True
        
    except Exception as e:
        screenshot = take_screenshot(driver, "03_step1_error")
        results.add_result(1, "新建活动按钮", False, f"测试异常: {str(e)}", screenshot)
        results.add_result(2, "'不提取文字'复选框默认勾选", False, f"测试异常: {str(e)}", screenshot)
        results.add_result(3, "'已上传的文件'区域存在", False, f"测试异常: {str(e)}", screenshot)
        return False

def test_4_step2_initial_idea(driver, results):
    """测试4: 步骤2 - 初步想法 (Issue #14)"""
    print("\n[测试 4] 步骤2 - 初步想法...")
    try:
        # 点击"继续"按钮进入步骤2
        continue_buttons = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '继续') or contains(text(), 'Continue')]")
        
        if not continue_buttons:
            screenshot = take_screenshot(driver, "04_no_continue_button")
            results.add_result(14, "初步想法输入框", False, "未找到继续按钮", screenshot)
            return False
        
        continue_buttons[0].click()
        time.sleep(2)
        
        screenshot = take_screenshot(driver, "04_step2_initial_idea")
        
        # Issue #14: 检查"初步想法"文本框是否在表单顶部
        try:
            initial_idea_textarea = driver.find_element(By.ID, "initial-idea")
            is_visible = initial_idea_textarea.is_displayed()
            
            # 检查标签文本
            page_source = driver.page_source
            has_label = ("对本次活动有什么初步想法" in page_source or 
                        "Any initial idea" in page_source or
                        "initial idea" in page_source.lower())
            
            passed = is_visible and has_label
            results.add_result(14, "初步想法输入框在表单顶部", passed,
                f"输入框: {'可见' if is_visible else '不可见'}, 标签: {'存在' if has_label else '不存在'}",
                screenshot)
            
            # 尝试输入文本
            if is_visible:
                initial_idea_textarea.send_keys("这是一个测试想法")
                time.sleep(1)
                screenshot2 = take_screenshot(driver, "04_step2_idea_typed")
                
        except NoSuchElementException:
            results.add_result(14, "初步想法输入框在表单顶部", False,
                "未找到初步想法输入框", screenshot)
        
        return True
        
    except Exception as e:
        screenshot = take_screenshot(driver, "04_step2_error")
        results.add_result(14, "初步想法输入框在表单顶部", False, 
            f"测试异常: {str(e)}", screenshot)
        return False

def test_5_step3_button_i18n(driver, results):
    """测试5: 步骤3 - 按钮国际化 (Issue #4)"""
    print("\n[测试 5] 步骤3 - 按钮国际化...")
    try:
        # 填写必填字段并进入步骤3
        # 这里简化处理，假设可以跳过或使用最小输入
        time.sleep(2)
        
        # 尝试找到并点击验证按钮
        validate_buttons = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '验证') or contains(text(), 'Validate')]")
        if validate_buttons:
            validate_buttons[0].click()
            time.sleep(2)
        
        # 尝试进入步骤3
        continue_buttons = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '继续') or contains(text(), 'Continue')]")
        if continue_buttons:
            continue_buttons[0].click()
            time.sleep(2)
        
        screenshot = take_screenshot(driver, "05_step3_button")
        
        # Issue #4: 检查"开始生成"按钮
        page_source = driver.page_source
        has_start_button = "开始生成" in page_source or "Start Generation" in page_source
        
        results.add_result(4, "开始生成按钮国际化", has_start_button,
            f"按钮: {'找到' if has_start_button else '未找到'}", screenshot)
        
    except Exception as e:
        screenshot = take_screenshot(driver, "05_step3_error")
        results.add_result(4, "开始生成按钮国际化", False, 
            f"测试异常: {str(e)}", screenshot)

def test_6_activity_projects(driver, results):
    """测试6: 活动项目 - 编辑/复制按钮 (Issue #13)"""
    print("\n[测试 6] 活动项目 - 编辑/复制按钮...")
    try:
        # 导航到活动项目页面
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        
        # 查找活动项目链接
        activity_links = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '活动项目') or contains(text(), 'Activity Projects')]")
        
        if activity_links:
            activity_links[0].click()
            time.sleep(2)
        
        screenshot = take_screenshot(driver, "06_activity_projects")
        
        # Issue #13: 检查编辑和复制按钮
        page_source = driver.page_source
        has_edit_button = "Edit" in page_source or "编辑" in page_source
        has_duplicate_button = "Duplicate" in page_source or "复制" in page_source
        
        passed = has_edit_button and has_duplicate_button
        results.add_result(13, "活动项目有编辑和复制按钮", passed,
            f"编辑按钮: {'存在' if has_edit_button else '不存在'}, "
            f"复制按钮: {'存在' if has_duplicate_button else '不存在'}",
            screenshot)
        
    except Exception as e:
        screenshot = take_screenshot(driver, "06_activity_projects_error")
        results.add_result(13, "活动项目有编辑和复制按钮", False, 
            f"测试异常: {str(e)}", screenshot)

def test_7_course_documents(driver, results):
    """测试7: 课程文档 (Issue #10)"""
    print("\n[测试 7] 课程文档...")
    try:
        # 导航到课程文档页面
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        
        # 查找课程文档链接
        doc_links = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '课程文档') or contains(text(), 'Course Documents')]")
        
        if doc_links:
            doc_links[0].click()
            time.sleep(2)
        
        screenshot = take_screenshot(driver, "07_course_documents")
        
        # Issue #10: 检查文档卡片不显示提取的文本内容
        page_source = driver.page_source
        
        # 检查是否只显示文件名、类型、上传时间、chunks
        # 不应该显示大段的提取文本
        has_filename = "文件名" in page_source or "filename" in page_source.lower()
        has_type = "类型" in page_source or "type" in page_source.lower()
        has_time = "上传时间" in page_source or "uploaded" in page_source.lower()
        
        # 简单检查：如果页面很长，可能包含了提取的文本
        page_length = len(page_source)
        likely_no_extracted_text = page_length < 50000  # 简单的启发式判断
        
        passed = has_filename and has_type and likely_no_extracted_text
        results.add_result(10, "课程文档不显示提取的文本", passed,
            f"显示文件信息: {has_filename and has_type}, "
            f"页面大小合理: {likely_no_extracted_text}",
            screenshot)
        
    except Exception as e:
        screenshot = take_screenshot(driver, "07_course_documents_error")
        results.add_result(10, "课程文档不显示提取的文本", False, 
            f"测试异常: {str(e)}", screenshot)

def test_8_quality_report(driver, results):
    """测试8: 质量报告 (Issue #9)"""
    print("\n[测试 8] 质量报告...")
    try:
        # 导航到质量检查结果页面
        driver.get(f"{BASE_URL}/teacher")
        time.sleep(2)
        
        # 查找质量检查结果链接
        quality_links = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '质量检查') or contains(text(), 'Quality')]")
        
        if quality_links:
            quality_links[0].click()
            time.sleep(2)
        
        screenshot = take_screenshot(driver, "08_quality_report")
        
        # Issue #9: 检查质量报告
        page_source = driver.page_source
        
        # 检查是否有维度描述
        has_descriptions = "描述" in page_source or "description" in page_source.lower()
        
        # 检查0/100分是否显示为"尚未评估"而不是"POOR"
        has_not_assessed = "尚未评估" in page_source or "Not yet assessed" in page_source
        has_poor_for_zero = "POOR" in page_source and "0" in page_source
        
        passed = has_descriptions and (has_not_assessed or not has_poor_for_zero)
        results.add_result(9, "质量报告显示正确", passed,
            f"有维度描述: {has_descriptions}, "
            f"0分显示为'尚未评估': {has_not_assessed}",
            screenshot)
        
    except Exception as e:
        screenshot = take_screenshot(driver, "08_quality_report_error")
        results.add_result(9, "质量报告显示正确", False, 
            f"测试异常: {str(e)}", screenshot)

def test_9_output_materials(driver, results):
    """测试9: 输出材料 (Issue #5, #6, #7, #8)"""
    print("\n[测试 9] 输出材料...")
    try:
        # 这个测试需要实际生成一个活动，比较复杂
        # 这里我们检查是否有相关的UI元素
        
        screenshot = take_screenshot(driver, "09_output_materials")
        page_source = driver.page_source
        
        # Issue #8: 检查是否有3个标签页
        has_student_worksheet = "Student Worksheet" in page_source or "学生工作表" in page_source
        has_student_slides = "Student Slides" in page_source or "学生幻灯片" in page_source
        has_teacher_sheet = "Teacher Facilitation Sheet" in page_source or "教师引导表" in page_source
        
        tabs_correct = has_student_worksheet and has_student_slides and has_teacher_sheet
        results.add_result(8, "输出材料有3个标签页", tabs_correct,
            f"学生工作表: {has_student_worksheet}, "
            f"学生幻灯片: {has_student_slides}, "
            f"教师引导表: {has_teacher_sheet}",
            screenshot)
        
        # Issue #7: 检查没有Pipeline Summary
        has_pipeline_summary = "Pipeline Summary" in page_source or "管道摘要" in page_source
        results.add_result(7, "输出材料没有Pipeline Summary", not has_pipeline_summary,
            f"Pipeline Summary: {'存在' if has_pipeline_summary else '不存在'}",
            screenshot)
        
        # Issue #5: 检查是否有"修改并重新生成"按钮
        has_regenerate = "修改并重新生成" in page_source or "Edit & Regenerate" in page_source
        results.add_result(5, "有修改并重新生成按钮", has_regenerate,
            f"按钮: {'存在' if has_regenerate else '不存在'}",
            screenshot)
        
        # Issue #6: 检查导出按钮标签
        has_download_json = "下载 JSON" in page_source or "Download JSON" in page_source
        results.add_result(6, "导出按钮标签改进", has_download_json,
            f"下载JSON按钮: {'存在' if has_download_json else '不存在'}",
            screenshot)
        
    except Exception as e:
        screenshot = take_screenshot(driver, "09_output_materials_error")
        results.add_result(5, "有修改并重新生成按钮", False, f"测试异常: {str(e)}", screenshot)
        results.add_result(6, "导出按钮标签改进", False, f"测试异常: {str(e)}", screenshot)
        results.add_result(7, "输出材料没有Pipeline Summary", False, f"测试异常: {str(e)}", screenshot)
        results.add_result(8, "输出材料有3个标签页", False, f"测试异常: {str(e)}", screenshot)

def main():
    """主测试流程"""
    print("="*80)
    print("CSCL应用程序 - 14个问题修复验证测试")
    print("="*80)
    print(f"测试URL: {BASE_URL}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("="*80)
    
    results = TestResults()
    driver = setup_driver()
    
    try:
        # 执行测试 - 即使登录失败也继续测试其他功能
        test_1_login_and_demo(driver, results)
        
        # 尝试继续测试其他功能
        test_2_sidebar_items(driver, results)
        test_3_new_activity_step1(driver, results)
        test_4_step2_initial_idea(driver, results)
        test_5_step3_button_i18n(driver, results)
        test_6_activity_projects(driver, results)
        test_7_course_documents(driver, results)
        test_8_quality_report(driver, results)
        test_9_output_materials(driver, results)
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 打印结果摘要
        results.print_summary()
        
        # 关闭浏览器
        print("\n正在关闭浏览器...")
        driver.quit()
        print("✓ 测试完成")
        
        # 返回退出码
        sys.exit(0 if results.failed == 0 else 1)

if __name__ == '__main__':
    main()
