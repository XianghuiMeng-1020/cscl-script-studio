"""
LLM Provider抽象层
支持Qwen、OpenAI和Mock三种provider
"""
import os
import json
from typing import Optional, Dict, Any
from openai import OpenAI


class LLMProvider:
    """LLM Provider抽象基类"""
    
    def __init__(self, provider_name: str, model: str):
        self.provider_name = provider_name
        self.model = model
        self.client = None
    
    def generate(self, prompt: str, system_message: str = "You are a helpful assistant.", 
                 max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
        """
        生成文本
        
        返回格式:
        {
            "provider": str,
            "model": str,
            "content": str,
            "warnings": list[str],
            "error": Optional[str]
        }
        """
        raise NotImplementedError
    
    def _create_response(self, content: str, warnings: list = None, error: str = None) -> Dict[str, Any]:
        """创建统一格式的响应"""
        return {
            "provider": self.provider_name,
            "model": self.model,
            "content": content,
            "warnings": warnings or [],
            "error": error
        }


class QwenProvider(LLMProvider):
    """Qwen (DashScope) Provider"""
    
    def __init__(self):
        api_key = os.getenv('QWEN_API_KEY', '')
        base_url = os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        model = os.getenv('QWEN_MODEL', 'qwen-plus')
        
        super().__init__('qwen', model)
        
        if not api_key:
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
    
    def generate(self, prompt: str, system_message: str = "You are a helpful assistant.", 
                 max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
        """调用Qwen API"""
        if not self.client:
            return self._create_response(
                content="",
                error="QWEN_API_KEY not configured"
            )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content.strip()
            return self._create_response(content=content)
        except Exception as e:
            return self._create_response(
                content="",
                error=f"Qwen API error: {str(e)}"
            )


class OpenAIProvider(LLMProvider):
    """OpenAI (GPT) Provider"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY', '')
        base_url = os.getenv('OPENAI_BASE_URL', None)  # None means use default OpenAI endpoint
        model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        super().__init__('openai', model)
        
        if not api_key:
            self.client = None
        else:
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self.client = OpenAI(**kwargs)
    
    def generate(self, prompt: str, system_message: str = "You are a helpful assistant.", 
                 max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
        """调用OpenAI API"""
        if not self.client:
            return self._create_response(
                content="",
                error="OPENAI_API_KEY not configured"
            )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content.strip()
            return self._create_response(content=content)
        except Exception as e:
            return self._create_response(
                content="",
                error=f"OpenAI API error: {str(e)}"
            )


class MockProvider(LLMProvider):
    """Mock Provider for testing and reproducibility"""
    
    def __init__(self):
        model = os.getenv('MOCK_MODEL', 'mock-model-v1')
        super().__init__('mock', model)
    
    def generate(self, prompt: str, system_message: str = "You are a helpful assistant.", 
                 max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
        """返回固定的假数据"""
        # 根据prompt类型返回不同的假数据
        prompt_lower = prompt.lower()
        
        if ('rubric' in prompt_lower and 'alignment' in prompt_lower) or 'covers all dimensions' in prompt_lower or 'covered_criteria' in prompt_lower or ('check-alignment' in prompt_lower or 'check alignment' in prompt_lower):
            # 反馈对齐检查的假数据
            content = json.dumps({
                "covered_criteria": ["Argument Clarity", "Evidence Support"],
                "missing_criteria": ["Organization", "Language Expression"],
                "coverage_score": 50,
                "suggestions": ["Consider adding feedback on organization", "Mention language expression"]
            })
        elif 'quality' in prompt_lower:
            # 反馈质量分析的假数据
            content = json.dumps({
                "specificity": {"score": 4, "analysis": "Feedback is specific and references student work"},
                "feedforward": {"score": 3, "analysis": "Some improvement suggestions provided"},
                "tone": {"score": 5, "analysis": "Professional and encouraging tone"},
                "overall_score": 4,
                "improvement_suggestions": ["Add more specific examples", "Include more forward-looking guidance"]
            })
        elif 'improve' in prompt_lower or 'optimize' in prompt_lower:
            # 反馈改进的假数据
            content = "This is an improved version of the feedback with better specificity and feedforward. [MOCK RESPONSE]"
        elif 'summary' in prompt_lower or 'visual' in prompt_lower:
            # 视觉摘要的假数据
            content = json.dumps({
                "strengths": ["Clear argument structure", "Good use of evidence"],
                "improvements": ["Expand on limitations", "Add more examples"],
                "overall_comment": "Overall good work with room for improvement",
                "encouragement": "Keep up the great work!"
            })
        elif 'script' in prompt_lower or 'video' in prompt_lower:
            # 视频脚本的假数据
            content = "Hello! This is a mock video feedback script. Your work shows good understanding. [MOCK SCRIPT CONTENT]"
        elif 'suggest' in prompt_lower and 'score' in prompt_lower:
            # 评分建议的假数据
            content = json.dumps({
                "suggestions": [
                    {
                        "criterion_id": "C1",
                        "criterion_name": "Argument Clarity",
                        "suggested_level": "Good",
                        "confidence": 0.8,
                        "rationale": "Mock rationale for scoring suggestion"
                    }
                ],
                "overall_assessment": "Mock overall assessment"
            })
        else:
            # 默认假数据
            content = f"[MOCK RESPONSE] This is a mock response to: {prompt[:100]}..."
        
        return self._create_response(
            content=content,
            warnings=["This is a mock provider response for testing"]
        )


def get_llm_provider() -> LLMProvider:
    """
    根据环境变量获取LLM Provider实例
    
    环境变量:
    - LLM_PROVIDER: qwen|openai|mock
    """
    provider_name = os.getenv('LLM_PROVIDER', 'qwen').lower()
    
    if provider_name == 'qwen':
        provider = QwenProvider()
        if not provider.client:
            # 如果配置了qwen但没有key，返回错误标记的provider
            return provider
        return provider
    elif provider_name == 'openai':
        provider = OpenAIProvider()
        if not provider.client:
            # 如果配置了openai但没有key，返回错误标记的provider
            return provider
        return provider
    elif provider_name == 'mock':
        return MockProvider()
    else:
        # 未知provider，默认使用mock
        import warnings
        warnings.warn(f"Unknown LLM_PROVIDER: {provider_name}, using mock")
        return MockProvider()
