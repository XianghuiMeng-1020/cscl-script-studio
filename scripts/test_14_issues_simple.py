#!/usr/bin/env python3
"""
简化版测试 - 直接使用requests检查页面内容
"""
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://web-production-591d6.up.railway.app'

def test_page_content():
    """测试页面内容"""
    print("="*80)
    print("CSCL应用程序 - 页面内容检查")
    print("="*80)
    
    # 创建session
    session = requests.Session()
    
    # 1. 登录为teacher_demo
    print("\n[1] 使用teacher_demo登录...")
    login_data = {
        'user_id': 'teacher_demo',
        'password': 'Demo@12345'
    }
    login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data, allow_redirects=True)
    print(f"登录状态码: {login_response.status_code}")
    if login_response.status_code == 200:
        print("✓ 登录成功")
        print(f"Cookies: {session.cookies.get_dict()}")
    else:
        print(f"✗ 登录失败: {login_response.text[:200]}")
    
    # 2. 访问教师页面
    print("\n[2] 访问教师页面...")
    response = session.get(f"{BASE_URL}/teacher", allow_redirects=True)
    print(f"状态码: {response.status_code}")
    print(f"最终URL: {response.url}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 保存HTML用于调试
    with open('/tmp/teacher_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("HTML已保存到: /tmp/teacher_page.html")
    
    # 检查侧边栏
    print("\n[3] 检查侧边栏...")
    sidebar = soup.find(class_='sidebar')
    if sidebar:
        sidebar_text = sidebar.get_text()
        print(f"侧边栏文本:\n{sidebar_text[:500]}")
        
        # Issue #11: "自动生成过程" 不应该在侧边栏
        has_pipeline_runs = "自动生成过程" in sidebar_text or "Pipeline Runs" in sidebar_text
        print(f"\n✓ Issue #11 - 侧边栏{'包含' if has_pipeline_runs else '不包含'}'自动生成过程': {'FAIL' if has_pipeline_runs else 'PASS'}")
        
        # Issue #12: "教学目标检查" 不应该在侧边栏
        has_teaching_plan = "教学目标检查" in sidebar_text or "Teaching Plan Settings" in sidebar_text
        print(f"✓ Issue #12 - 侧边栏{'包含' if has_teaching_plan else '不包含'}'教学目标检查': {'FAIL' if has_teaching_plan else 'PASS'}")
    else:
        print("未找到侧边栏")
    
    # 检查页面中的关键元素
    print("\n[4] 检查关键元素...")
    
    # Issue #2: "不提取文字"复选框
    no_extract_checkbox = soup.find(id='no-extract-text')
    if no_extract_checkbox:
        is_checked = no_extract_checkbox.get('checked') is not None
        print(f"✓ Issue #2 - '不提取文字'复选框默认{'勾选' if is_checked else '未勾选'}: {'PASS' if is_checked else 'FAIL'}")
    else:
        print("✗ Issue #2 - 未找到'不提取文字'复选框")
    
    # Issue #3: "已上传的文件"区域
    uploaded_files = soup.find(id='uploaded-files-list')
    if uploaded_files:
        print(f"✓ Issue #3 - '已上传的文件'区域存在: PASS")
    else:
        print("✗ Issue #3 - 未找到'已上传的文件'区域")
    
    # Issue #14: "初步想法"输入框
    initial_idea = soup.find(id='initial-idea')
    if initial_idea:
        print(f"✓ Issue #14 - '初步想法'输入框存在: PASS")
    else:
        print("✗ Issue #14 - 未找到'初步想法'输入框")
    
    # 检查按钮文本
    print("\n[5] 检查按钮和标签...")
    page_text = response.text
    
    # Issue #4: "开始生成"按钮
    has_start_button = "开始生成" in page_text or "Start Generation" in page_text
    print(f"✓ Issue #4 - '开始生成'按钮: {'PASS' if has_start_button else 'FAIL'}")
    
    # Issue #5: "修改并重新生成"按钮
    has_regenerate = "修改并重新生成" in page_text or "Edit & Regenerate" in page_text
    print(f"✓ Issue #5 - '修改并重新生成'按钮: {'PASS' if has_regenerate else 'FAIL'}")
    
    # Issue #6: "下载 JSON"按钮
    has_download_json = "下载 JSON" in page_text or "Download JSON" in page_text
    print(f"✓ Issue #6 - '下载 JSON'按钮: {'PASS' if has_download_json else 'FAIL'}")
    
    # Issue #7: 没有"Pipeline Summary"
    has_pipeline_summary = "Pipeline Summary" in page_text or "管道摘要" in page_text
    print(f"✓ Issue #7 - 没有'Pipeline Summary': {'PASS' if not has_pipeline_summary else 'FAIL'}")
    
    # Issue #8: 3个标签页
    has_student_worksheet = "Student Worksheet" in page_text or "学生工作表" in page_text
    has_student_slides = "Student Slides" in page_text or "学生幻灯片" in page_text
    has_teacher_sheet = "Teacher Facilitation Sheet" in page_text or "教师引导表" in page_text
    tabs_correct = has_student_worksheet and has_student_slides and has_teacher_sheet
    print(f"✓ Issue #8 - 3个标签页: {'PASS' if tabs_correct else 'FAIL'}")
    
    # Issue #13: 编辑和复制按钮
    has_edit = "Edit" in page_text or "编辑" in page_text
    has_duplicate = "Duplicate" in page_text or "复制" in page_text
    print(f"✓ Issue #13 - 编辑和复制按钮: {'PASS' if (has_edit and has_duplicate) else 'FAIL'}")
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)

if __name__ == '__main__':
    test_page_content()
