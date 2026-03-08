# Render 环境变量设置

在 [Render Dashboard](https://dashboard.render.com) 中打开你的 Web Service **cscl-script-studio**，左侧点击 **Environment**，添加或编辑以下变量后保存。保存后如需立即生效，可在 **Manual Deploy** 中触发一次重新部署。

## 必填（用于 AI 生成）

| Key | 说明 |
|-----|------|
| `QWEN_API_KEY` | 通义千问 API Key（在 DashScope 控制台获取）。用于生成协作学习活动。 |

其他变量（如 `SECRET_KEY`、`LLM_PROVIDER` 等）已在 Blueprint 或默认值中配置，可按需覆盖。

## 添加步骤

1. 打开 https://dashboard.render.com/web/srv-d6mp5hpaae7s73ee3ip0/environment  
2. 点击 **Add Environment Variable**  
3. Key 填 `QWEN_API_KEY`，Value 填你的 API Key  
4. 保存后如需立即生效：顶部 **Manual Deploy** → **Deploy latest commit**

**注意：** 不要将 API Key 提交到 Git 仓库。
