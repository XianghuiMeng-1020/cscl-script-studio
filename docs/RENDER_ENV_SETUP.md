# Render 环境变量设置

## 可发给客户的链接（API 已可用）

| 用途 | 链接 |
|------|------|
| **应用首页（给客户用）** | **https://cscl-script-studio.onrender.com** |
| 教师端 | https://cscl-script-studio.onrender.com/teacher |
| 学生端 | https://cscl-script-studio.onrender.com/student |
| 健康检查/API 状态 | https://cscl-script-studio.onrender.com/api/health |

把 **https://cscl-script-studio.onrender.com** 发给客户即可使用；健康检查可用来确认服务与 LLM 是否就绪。

---

在 [Render Dashboard](https://dashboard.render.com) 中打开你的 Web Service **cscl-script-studio**，左侧点击 **Environment**，添加或编辑以下变量后保存。保存后如需立即生效，可在 **Manual Deploy** 中触发一次重新部署。

## 必填（用于 AI 生成，双轨互为备用）

| Key | 说明 |
|-----|------|
| `QWEN_API_KEY` | 通义千问 API Key（DashScope 控制台）。主用。 |
| `OPENAI_API_KEY` | OpenAI API Key（仅使用 gpt-4o-mini）。Qwen 不可用时自动切换到此。 |

策略：`LLM_PROVIDER_PRIMARY=qwen`、`LLM_PROVIDER_FALLBACK=openai`、`LLM_STRATEGY=primary_with_fallback`。任一不可用（超时/5xx 等）会立刻用另一个。

其他变量（如 `SECRET_KEY`、`OPENAI_MODEL=gpt-4o-mini` 等）已在 Blueprint 或默认值中配置，可按需覆盖。

## 添加步骤

1. 打开 Render Dashboard → 你的 **cscl-script-studio** 服务 → **Environment**  
2. 点击 **Add Environment Variable**，添加：
   - `QWEN_API_KEY` = 你的通义千问 Key  
   - `OPENAI_API_KEY` = 你的 OpenAI Key（用于 gpt-4o-mini）  
3. 保存后如需立即生效：顶部 **Manual Deploy** → **Deploy latest commit**

**注意：** 不要将 API Key 提交到 Git 仓库。
