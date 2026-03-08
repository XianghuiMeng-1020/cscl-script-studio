# S2.7 Incident Playbook

## 1. 健康检查失败 (/api/health 非 200)

- 检查: `docker compose logs web --tail=200`
- 常见: 数据库连接失败、SECRET_KEY 未设置（production）
- 处置: 检查 DATABASE_URL、网络；补全 SECRET_KEY 后重启

## 2. 5xx 错误率升高

- 检查: 日志中异常堆栈、数据库连接池
- 处置: 扩容 web 实例；检查 postgres 负载；临时启用 mock provider 降级

## 3. 认证失败 (401/403)

- 检查: session/cookie 配置、CORS 白名单
- 处置: 确认 CORS_ALLOWED_ORIGINS 包含前端域名；检查 SECRET_KEY 是否一致

## 4. PDF 提取乱码 (%PDF/obj/stream 污染)

- 检查: document_service 的 _PDF_BINARY_MARKERS、normalize_text
- 处置: 确认提取失败返回 PDF_PARSE_FAILED；preview 不含二进制标记

## 5. LLM 调用失败 (provider not configured)

- 检查: OPENAI_API_KEY / QWEN_API_KEY、LLM_PROVIDER
- 处置: 切换 LLM_PROVIDER=openai 或 qwen；或临时 LLM_PROVIDER=mock 降级

## 6. 回滚决策

- 若影响核心功能且无法快速修复：执行 `./scripts/rollback_s2_7.sh`
- 数据库不执行 downgrade；需从备份恢复时另行操作
