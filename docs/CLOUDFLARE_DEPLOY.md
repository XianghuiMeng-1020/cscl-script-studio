# 推送到 Cloudflare 可访问的 link 与后端 serverless 配置

## 1. 用你提供的 link 配置远程并推送

把你**授权的 Git 仓库 URL**（link）交给脚本即可完成 `remote add` 与 `push`：

```bash
# 方式一：直接传入 link
./scripts/set_remote_and_push.sh https://github.com/你的用户名/仓库名.git

# 方式二：用环境变量
export GIT_REMOTE_URL=https://github.com/你的用户名/仓库名.git
./scripts/set_remote_and_push.sh
```

脚本会：若尚未配置 `origin` 则添加，然后执行 `git push -u origin <当前分支>`。  
推送成功后，在 Cloudflare Dashboard 里连接该仓库即可得到用户可访问的 link。

---

## 2. 在 Cloudflare 上得到用户可用的 link

- **Cloudflare Pages**  
  - Dashboard → Pages → Create project → Connect to Git → 选择你推送的仓库。  
  - 构建命令、输出目录：本项目为 **Flask 服务端渲染**，若只做静态站点需单独构建前端；若希望整站由 Cloudflare 提供，见下「后端 serverless」。

- **分支与域名**  
  - 选择分支（如 `main`），保存后 Cloudflare 会给出 `https://<项目名>.pages.dev` 这类 link。

---

## 3. 后端 serverless（server free）配置

本应用是 **Flask（Python）**，需要常驻进程或 serverless 跑后端。可选方式：

| 方式 | 说明 |
|------|------|
| **Cloudflare Workers（Python）** | 若将 API 迁到 Workers 或通过 Worker 反向代理到外部后端，可在 Cloudflare 上实现「后端 serverless」。当前代码为 Flask，需单独拆 API 或代理。 |
| **外部 serverless/免费后端** | 将 Flask 部署到支持 Python 的 serverless 或免费主机（如 **Railway**、**Render**、**Fly.io**、**Google Cloud Run**），在 Cloudflare Pages 或 Worker 里把 API 请求代理到该后端；或直接让前端请求后端域名。 |

**建议**：  
- 先在本仓库同一 Git 上连接 Cloudflare Pages，用于前端/静态资源或整站（若 Pages 支持 Python 构建）。  
- 后端单独部署到上述任一 serverless/免费服务，配置 `DATABASE_URL`、`SECRET_KEY`、`USE_DB_STORAGE` 等（见 [DEPLOY_RUNBOOK.md](../DEPLOY_RUNBOOK.md)），再在 Cloudflare 或前端里配置「后端 API 地址」指向该服务。

---

## 4. 部署后多用户测试

部署完成并拿到 **用户可访问的 link** 后，在同一仓库的 [scripts/README_LOAD_TEST_20_USERS.md](../scripts/README_LOAD_TEST_20_USERS.md) 第 6 节执行 20 用户负载测试，确认无文档混淆、无 5xx。

---

## 5. 小结

1. 你提供 **Git 仓库 link** → 运行 `./scripts/set_remote_and_push.sh <link>` 完成推送。  
2. 在 Cloudflare 连接该仓库，得到 **用户可用的 link**。  
3. 后端用 **serverless/免费服务** 部署 Flask，并配置环境变量；如需全部在 Cloudflare，再考虑 Workers 代理或迁移 API。
