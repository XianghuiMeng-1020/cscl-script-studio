#!/usr/bin/env python3
"""
独立的LLM Provider测试脚本
不依赖Flask应用，直接测试provider功能
"""
import os
import sys
import json

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

# 直接导入provider模块，避免触发app.py
import importlib.util
spec = importlib.util.spec_from_file_location("llm_provider", "app/services/llm_provider.py")
llm_provider_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_provider_module)

get_llm_provider = llm_provider_module.get_llm_provider
MockProvider = llm_provider_module.MockProvider
QwenProvider = llm_provider_module.QwenProvider
OpenAIProvider = llm_provider_module.OpenAIProvider

def test_mock_provider():
    """测试Mock Provider"""
    print("=" * 60)
    print("测试1: Mock Provider")
    print("=" * 60)
    
    # 设置环境变量
    os.environ['LLM_PROVIDER'] = 'mock'
    if 'QWEN_API_KEY' in os.environ:
        del os.environ['QWEN_API_KEY']
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
    
    provider = get_llm_provider()
    print(f"Provider类型: {type(provider).__name__}")
    print(f"Provider名称: {provider.provider_name}")
    print(f"Model: {provider.model}")
    
    # 测试调用
    prompt = """Analyze whether the following instructor feedback covers all dimensions in the rubric criteria.

Rubric Criteria:
- Argument Clarity: Is the thesis clear?
- Evidence Support: Are there sufficient evidence?

Instructor Feedback:
"This feedback covers argument clarity and evidence support."

Please return the analysis result in JSON format:
{
    "covered_criteria": ["list of covered criteria names"],
    "missing_criteria": ["list of missing criteria names"],
    "coverage_score": coverage score from 0-100,
    "suggestions": ["list of improvement suggestions"]
}

Return only JSON, no other content."""
    
    system_message = "You are an educational assessment expert."
    
    print("\n调用generate()...")
    result = provider.generate(prompt, system_message)
    
    print("\n返回结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 验证
    assert result['provider'] == 'mock', f"Expected provider='mock', got '{result['provider']}'"
    assert 'content' in result, "Missing 'content' field"
    assert result.get('error') is None, f"Unexpected error: {result.get('error')}"
    
    print("\n✅ Mock Provider测试通过")
    return result


def test_qwen_provider():
    """测试Qwen Provider"""
    print("\n" + "=" * 60)
    print("测试2: Qwen Provider")
    print("=" * 60)
    
    # 设置环境变量
    os.environ['LLM_PROVIDER'] = 'qwen'
    # 检查是否有API key
    qwen_key = os.getenv('QWEN_API_KEY', '')
    
    if not qwen_key or qwen_key == 'your-qwen-api-key-here':
        print("⚠️  QWEN_API_KEY未设置或使用占位符，测试未配置情况")
        os.environ['QWEN_API_KEY'] = ''  # 确保未设置
    else:
        print(f"✅ QWEN_API_KEY已设置: {qwen_key[:10]}...")
    
    provider = get_llm_provider()
    print(f"Provider类型: {type(provider).__name__}")
    print(f"Provider名称: {provider.provider_name}")
    print(f"Model: {provider.model}")
    print(f"Client初始化: {provider.client is not None}")
    
    # 测试调用
    prompt = "Test prompt for Qwen"
    system_message = "You are a helpful assistant."
    
    print("\n调用generate()...")
    result = provider.generate(prompt, system_message, max_tokens=100)
    
    print("\n返回结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 验证
    assert result['provider'] == 'qwen', f"Expected provider='qwen', got '{result['provider']}'"
    
    if provider.client is None:
        assert result.get('error') is not None, "Expected error when API key not configured"
        assert 'QWEN_API_KEY' in result['error'], "Error message should mention QWEN_API_KEY"
        print("\n✅ Qwen Provider未配置测试通过（正确返回错误）")
    else:
        assert 'content' in result or result.get('error'), "Should have content or error"
        if result.get('error'):
            print(f"\n⚠️  Qwen API调用失败: {result['error']}")
        else:
            print("\n✅ Qwen Provider API调用成功")
    
    return result


def test_openai_provider():
    """测试OpenAI Provider"""
    print("\n" + "=" * 60)
    print("测试3: OpenAI Provider")
    print("=" * 60)
    
    # 设置环境变量
    os.environ['LLM_PROVIDER'] = 'openai'
    # 检查是否有API key
    openai_key = os.getenv('OPENAI_API_KEY', '')
    
    if not openai_key or openai_key == 'your-openai-api-key-here':
        print("⚠️  OPENAI_API_KEY未设置或使用占位符，测试未配置情况")
        os.environ['OPENAI_API_KEY'] = ''  # 确保未设置
    else:
        print(f"✅ OPENAI_API_KEY已设置: {openai_key[:10]}...")
    
    provider = get_llm_provider()
    print(f"Provider类型: {type(provider).__name__}")
    print(f"Provider名称: {provider.provider_name}")
    print(f"Model: {provider.model}")
    print(f"Client初始化: {provider.client is not None}")
    
    # 测试调用
    prompt = "Test prompt for OpenAI"
    system_message = "You are a helpful assistant."
    
    print("\n调用generate()...")
    result = provider.generate(prompt, system_message, max_tokens=100)
    
    print("\n返回结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 验证
    assert result['provider'] == 'openai', f"Expected provider='openai', got '{result['provider']}'"
    
    if provider.client is None:
        assert result.get('error') is not None, "Expected error when API key not configured"
        assert 'OPENAI_API_KEY' in result['error'], "Error message should mention OPENAI_API_KEY"
        print("\n✅ OpenAI Provider未配置测试通过（正确返回错误）")
    else:
        assert 'content' in result or result.get('error'), "Should have content or error"
        if result.get('error'):
            print(f"\n⚠️  OpenAI API调用失败: {result['error']}")
        else:
            print("\n✅ OpenAI Provider API调用成功")
    
    return result


if __name__ == '__main__':
    print("LLM Provider抽象层测试")
    print("=" * 60)
    
    try:
        # 测试Mock Provider
        mock_result = test_mock_provider()
        
        # 测试Qwen Provider
        qwen_result = test_qwen_provider()
        
        # 测试OpenAI Provider
        openai_result = test_openai_provider()
        
        print("\n" + "=" * 60)
        print("✅ 所有Provider基础测试通过")
        print("=" * 60)
        print("\n注意: 如果Qwen/OpenAI API key未配置，会返回错误，这是预期的行为。")
        print("要测试真实API调用，请在.env文件中配置相应的API key。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
