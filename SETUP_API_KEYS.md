# API Key配置指南

## 重要安全提示

⚠️ **不要将真实API key提交到仓库！**

- `.env.example`只包含占位符
- `.env`文件已在`.gitignore`中，不会被提交
- 所有真实API key应配置在本地`.env`文件中

---

## 快速配置步骤

### 1. 复制环境变量模板

```bash
cp .env.example .env
```

### 2. 编辑`.env`文件，填入真实API key

```bash
# 使用你喜欢的编辑器
nano .env
# 或
vim .env
# 或
code .env
```

### 3. 设置Qwen API Key（如果使用Qwen）

```bash
# 在.env文件中找到并修改：
QWEN_API_KEY=your-actual-qwen-api-key-here
```

获取Qwen API Key: https://dashscope.console.aliyun.com/

### 4. 设置OpenAI API Key（如果使用OpenAI）

```bash
# 在.env文件中找到并修改：
OPENAI_API_KEY=your-actual-openai-api-key-here
```

获取OpenAI API Key: https://platform.openai.com/api-keys

### 5. 选择Provider

```bash
# 在.env文件中设置：
LLM_PROVIDER=qwen    # 或 openai 或 mock
```

### 6. 重启服务

```bash
# 如果使用Docker
docker compose restart web

# 如果直接运行Python
# 停止当前进程，然后重新运行
python app.py
```

---

## 验证配置

### 方法1: 使用Mock Provider（无需API key）

```bash
# 在.env中设置
LLM_PROVIDER=mock

# 重启服务后测试
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{"feedback":"test","rubric_criteria":[]}' | jq '.provider'
# 预期输出: "mock"
```

### 方法2: 使用真实Provider

```bash
# 确保.env中已设置API key和LLM_PROVIDER
# 重启服务后测试
curl -X POST http://localhost:5000/api/ai/check-alignment \
  -H "Content-Type: application/json" \
  -d '{"feedback":"test","rubric_criteria":[]}' | jq '.provider'
# 预期输出: "qwen" 或 "openai"
```

---

## 故障排查

### API key未生效

1. 检查`.env`文件是否存在且包含API key
2. 检查`.env`文件格式（不要有多余空格，不要用引号）
3. 重启服务（环境变量只在启动时加载）

### Docker环境变量

如果使用Docker Compose，`.env`文件会自动加载。确保：
- `.env`文件在项目根目录
- `docker-compose.yml`中引用了环境变量（已配置）

### 直接运行Python

如果直接运行`python app.py`，需要确保环境变量已设置：

```bash
# 方法1: 使用.env文件（需要python-dotenv，可选）
pip install python-dotenv
# 然后在代码中加载（当前未实现，需要手动export）

# 方法2: 手动export
export LLM_PROVIDER=qwen
export QWEN_API_KEY="your-key"
python app.py
```

---

## 安全最佳实践

1. ✅ 使用`.env`文件存储API key（已在`.gitignore`中）
2. ✅ `.env.example`只包含占位符
3. ✅ 不要将`.env`文件提交到Git
4. ✅ 不要将API key硬编码在代码中
5. ✅ 不要将API key写在文档或注释中
6. ✅ 定期轮换API key
7. ✅ 使用最小权限原则（只授予必要的API权限）

---

**文档版本**: 1.0  
**创建日期**: 2026-02-05
