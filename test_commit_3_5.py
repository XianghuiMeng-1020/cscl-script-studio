#!/usr/bin/env python3
"""快速验证 Commit 3.5 功能"""
import os
import sys
import json
from datetime import datetime

# 设置环境变量
os.environ['USE_DB_STORAGE'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///test_commit35.db'
os.environ['SECRET_KEY'] = 'test-secret-key'

# 导入应用
from app import create_app
from app.db import db
from app.repositories import get_assignment_repo, get_submission_repo, get_rubric_repo, get_user_repo
from app.config import Config

def test_db_mode():
    """测试 DB 模式"""
    print("=" * 60)
    print("A) DB 模式测试 (USE_DB_STORAGE=true)")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # 创建表
        db.create_all()
        print("✓ 数据库表创建成功")
        
        # 测试 Repository
        user_repo = get_user_repo()
        rubric_repo = get_rubric_repo()
        assignment_repo = get_assignment_repo()
        submission_repo = get_submission_repo()
        
        print(f"✓ Repository 初始化成功 (USE_DB_STORAGE={Config.USE_DB_STORAGE})")
        
        # 清空数据（幂等性）
        submission_repo.delete_all()
        assignment_repo.delete_all()
        rubric_repo.delete_all()
        user_repo.delete_all()
        print("✓ 数据清空成功（幂等性验证）")
        
        # 创建 demo 数据
        user_repo.create({
            'id': 'S001',
            'role': 'student',
            'created_at': datetime.now().isoformat()
        })
        user_repo.create({
            'id': 'S002',
            'role': 'student',
            'created_at': datetime.now().isoformat()
        })
        
        rubric_data = {
            'id': 'R001',
            'name': 'Essay Writing Rubric',
            'description': 'Test rubric',
            'criteria': [{'id': 'C1', 'name': 'Test'}],
            'created_at': datetime.now().isoformat()
        }
        rubric_repo.create(rubric_data)
        
        assignment_data = {
            'id': 'A001',
            'title': 'Test Assignment',
            'description': 'Test',
            'course_id': 'CS101',
            'due_date': '2025-12-20',
            'rubric_id': 'R001',
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        assignment_repo.create(assignment_data)
        
        submission1_data = {
            'id': 'SUB001',
            'assignment_id': 'A001',
            'student_id': 'S001',
            'student_name': 'John Smith',
            'content': 'Test submission content',
            'submitted_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        submission_repo.create(submission1_data)
        
        submission2_data = {
            'id': 'SUB002',
            'assignment_id': 'A001',
            'student_id': 'S002',
            'student_name': 'Emily Johnson',
            'content': 'Another test submission',
            'submitted_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        submission_repo.create(submission2_data)
        
        print("✓ Demo 数据创建成功")
        
        # 测试查询
        pending = submission_repo.get_all(status='pending')
        print(f"✓ 查询 pending submissions: {len(pending)} 条")
        if pending:
            print(f"  第一条: {pending[0]['id']} - {pending[0]['student_name']}")
        
        student_subs = submission_repo.get_all(student_id='S001')
        print(f"✓ 查询 S001 的 submissions: {len(student_subs)} 条")
        
        assignments = assignment_repo.get_all()
        print(f"✓ 查询 assignments: {len(assignments)} 条")
        
        rubrics = rubric_repo.get_all()
        print(f"✓ 查询 rubrics: {len(rubrics)} 条")
        
        # 清理
        db.drop_all()
        print("✓ 测试完成，数据已清理")

def test_json_mode():
    """测试 JSON 模式"""
    print("\n" + "=" * 60)
    print("B) JSON fallback 模式测试 (USE_DB_STORAGE=false)")
    print("=" * 60)
    
    # 使用新的进程/模块来测试 JSON 模式
    # 由于 Python 模块缓存，我们需要直接测试 JSON Repository
    from app.repositories.submission_repository import JsonSubmissionRepository
    from app.utils import save_json, load_json
    from app.config import Config
    
    # 确保使用 JSON 模式
    original_use_db = Config.USE_DB_STORAGE
    Config.USE_DB_STORAGE = False
    print(f"✓ USE_DB_STORAGE={Config.USE_DB_STORAGE}")
    
    # 创建测试数据
    test_data = [{
        'id': 'SUB001',
        'assignment_id': 'A001',
        'student_id': 'S001',
        'student_name': 'Test Student',
        'content': 'Test',
        'status': 'pending',
        'submitted_at': datetime.now().isoformat()
    }]
    save_json(Config.SUBMISSIONS_FILE, test_data)
    
    submission_repo = JsonSubmissionRepository()
    submissions = submission_repo.get_all(status='pending')
    print(f"✓ JSON 模式查询 pending submissions: {len(submissions)} 条")
    if submissions:
        print(f"  第一条: {submissions[0]['id']} - {submissions[0]['student_name']}")
    
    # 清理
    save_json(Config.SUBMISSIONS_FILE, [])
    Config.USE_DB_STORAGE = original_use_db
    print("✓ JSON 模式测试完成")

if __name__ == '__main__':
    try:
        test_db_mode()
        test_json_mode()
        print("\n" + "=" * 60)
        print("✓ Commit 3.5 功能验证通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
