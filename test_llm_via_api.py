#!/usr/bin/env python3
"""
通过HTTP API测试LLM Provider
模拟curl请求，测试三种模式
"""
import os
import sys
import json
import subprocess
import time
import requests

def check_server_running():
    """检查服务器是否运行"""
    try:
        response = requests.get('http://localhost:5000/', timeout=2)
        return True
    except:
        return False

def start_server():
    """启动Flask服务器"""
    print("启动Flask服务器...")
    # 检查是否有.env文件
    if not os.path.exists('.env'):
        print("⚠️  未找到.env文件，创建临时.env用于测试...")
        with open('.env', 'w') as f:
            f.write("SECRET_KEY=test-secret-key\n")
            f.write("LLM_PROVIDER=mock\n")
    
    # 启动服务器（后台）
    process = subprocess.Popen(
        [sys.executable, 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    
    # 等待服务器启动
    for i in range(30):
        if check_server_running():
            print("✅ 服务器已启动")
            return process
        time.sleep(0.5)
    
    print("❌ 服务器启动超时")
    process.terminate()
    return None

def test_api_endpoint(provider_name, api_key_env=None):
    """测试API端点"""
    print(f"\n{'='*60}")
    print(f"测试: {provider_name.upper()} Provider")
    print(f"{'='*60}")
    
    # 设置环境变量
    os.environ['LLM_PROVIDER'] = provider_name
    
    if api_key_env:
        # 从.env文件读取API key
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith(api_key_env + '='):
                        key_value = line.strip().split('=', 1)[1]
                        if key_value and key_value != f'your-{api_key_env.lower().replace("_", "-")}-here':
                            os.environ[api_key_env] = key_value
                            print(f"✅ {api_key_env}已从.env加载")
                        else:
                            print(f"⚠️  {api_key_env}未配置或使用占位符")
                            os.environ[api_key_env] = ''
                        break
        else:
            os.environ[api_key_env] = ''
    else:
        # Mock provider不需要key
        if 'QWEN_API_KEY' in os.environ:
            del os.environ['QWEN_API_KEY']
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
    
    # 准备测试数据
    test_data = {
        "feedback": "This feedback covers argument clarity and evidence support.",
        "rubric_criteria": [
            {"id": "C1", "name": "Argument Clarity", "description": "Is the thesis clear?"},
            {"id": "C2", "name": "Evidence Support", "description": "Are there sufficient evidence?"}
        ]
    }
    
    # 发送请求
    url = 'http://localhost:5000/api/ai/check-alignment'
    print(f"\n请求URL: {url}")
    print(f"请求数据: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\nHTTP状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            result = response.json()
            print(f"\n响应JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except:
            print(f"\n响应文本: {response.text}")
            result = {"raw": response.text}
        
        # 验证结果
        if provider_name == 'mock':
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert 'provider' in result, "Missing 'provider' field"
            assert result['provider'] == 'mock', f"Expected provider='mock', got '{result['provider']}'"
            print("\n✅ Mock Provider测试通过")
        else:
            # Qwen/OpenAI可能成功或失败（取决于API key）
            if response.status_code == 503:
                assert 'error' in result, "Missing 'error' field in 503 response"
                assert result.get('provider') == provider_name, f"Expected provider='{provider_name}'"
                print(f"\n✅ {provider_name} Provider未配置测试通过（正确返回503）")
            elif response.status_code == 200:
                assert 'provider' in result, "Missing 'provider' field"
                assert result['provider'] == provider_name, f"Expected provider='{provider_name}'"
                print(f"\n✅ {provider_name} Provider API调用成功")
            else:
                print(f"\n⚠️  意外的状态码: {response.status_code}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求失败: {e}")
        return None

def main():
    print("="*60)
    print("LLM Provider HTTP API测试")
    print("="*60)
    
    # 检查服务器是否运行
    if not check_server_running():
        print("服务器未运行，尝试启动...")
        process = start_server()
        if not process:
            print("❌ 无法启动服务器，请手动启动: python3 app.py")
            return
        server_process = process
    else:
        print("✅ 服务器已在运行")
        server_process = None
    
    try:
        # 测试Mock Provider
        mock_result = test_api_endpoint('mock')
        
        # 测试Qwen Provider
        qwen_result = test_api_endpoint('qwen', 'QWEN_API_KEY')
        
        # 测试OpenAI Provider
        openai_result = test_api_endpoint('openai', 'OPENAI_API_KEY')
        
        print("\n" + "="*60)
        print("✅ 所有API测试完成")
        print("="*60)
        
    finally:
        if server_process:
            print("\n停止服务器...")
            server_process.terminate()
            server_process.wait()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
