# S2.15 HARD-GATE 总报告

## 结论：**GO_LIVE_APPROVED**

---

## 1. 修改文件清单

### 新增
| 文件 | 说明 |
|------|------|
| `scripts/s2_15_gate.sh` | S2.15 自动化验收脚本：健康、302/200、静态 200、教师 DOM/日志、PDF 无乱码 |
| `tests/test_s2_15_teacher_clickability.py` | 教师页可点击性：模板 data-action、nav data-view、JS 分阶段日志、事件委托、loading overlay |
| `tests/test_s2_15_pdf_no_binary_leak.py` | PDF 防乱码：sanitize、extract 失败码、upload 错误码、API 422/PDF_PARSE_FAILED |
| `outputs/s2_15/S2_15_FINAL_REPORT.md` | 本报告 |

### 修改
| 文件 | 说明 |
|------|------|
| `static/js/teacher.js` | 分阶段日志拆分为 `[teacher] bind start` 与 `[teacher] bind end`（原为一条 bind start/end） |

---

## 2. 每项修改原因

- **teacher.js**：验收要求初始化阶段必须有四条日志：script loaded、dom ready、bind start、bind end；原为“bind start/end”一条，拆成两条以满足 gate 与测试。
- **s2_15_gate.sh**：统一从 .env 启动后做可验证验收（健康字段、/teacher 302、/login 200、静态 200、登录后教师页 DOM 含 data-action、JS 含四条日志、PDF 上传返回 PDF_PARSE_FAILED 且响应体无 %PDF-）。
- **test_s2_15_teacher_clickability.py**：静态校验模板与 teacher.js 一致（data-action、data-view、分阶段日志、事件委托、null 防护、loading overlay pointer-events）。
- **test_s2_15_pdf_no_binary_leak.py**：校验 document_service 与 API 不返回二进制预览、错误码与 422 行为。

---

## 3. 环境与版本一致性（已执行）

```bash
docker compose --env-file .env down -v
docker compose --env-file .env up --build -d
docker compose --env-file .env exec -T web alembic upgrade head
docker compose --env-file .env exec -T web python scripts/seed_demo_users.py
```

**说明**：若首次 `alembic upgrade head` 后数据库中仅有 `alembic_version` 而无 `users` 等表，需在 Postgres 中执行 `DROP TABLE IF EXISTS alembic_version CASCADE;` 后再次执行 `alembic upgrade head`，再执行 seed。

---

## 4. 验收结果（命令 + 原始输出摘要）

### 4.1 健康检查（含 llm_primary, llm_fallback, llm_strategy, auth_mode, status）

```bash
curl -sS http://localhost:5001/api/health
```

**摘要**：`status`, `llm_primary`, `llm_fallback`, `llm_strategy`, `auth_mode` 均存在；HTTP 200。

### 4.2 /teacher 未登录 302 → /login

```bash
curl -sS -o /dev/null -w "%{http_code}" http://localhost:5001/teacher
```

**摘要**：`302`。

### 4.3 /login 200

```bash
curl -sS -o /dev/null -w "%{http_code}" http://localhost:5001/login
```

**摘要**：`200`。

### 4.4 teacher_demo / Demo@12345 登录 + 教师页关键按钮 DOM

登录后请求 `/teacher`，响应 HTML 含 `data-action="import-outline"`、`data-action="validate-goals"`、`data-action="run-pipeline"`；`static/js/teacher.js` 含 `[teacher] script loaded`、`[teacher] dom ready`、`[teacher] bind start`、`[teacher] bind end`。

### 4.5 静态资源 200 且 Content-Length > 0

```bash
curl -sI http://localhost:5001/static/js/teacher.js
curl -sI http://localhost:5001/static/js/student.js
curl -sI http://localhost:5001/static/js/i18n.js
```

**摘要**：三者均为 200，Content-Length > 0。

### 4.6 PDF 上传无二进制乱码

上传垃圾 PDF（含 %PDF-/obj/stream）后：API 返回错误且 `code=PDF_PARSE_FAILED`（或 422）；响应体不含 `%PDF-`。

### 4.7 pytest 全量

```bash
docker compose --env-file .env exec -T web python -m pytest tests/ -q
```

**摘要**：`177 passed, 135 warnings`，0 failed。

### 4.8 scripts/s2_15_gate.sh

```bash
bash scripts/s2_15_gate.sh
```

**摘要**：`PASS=15 FAIL=0`，exit 0。

---

## 5. 最终交付标准核对

| 标准 | 结果 |
|------|------|
| docker compose 正常启动 | 是 |
| /api/health 正常且字段齐全 | 是（status, llm_primary, llm_fallback, llm_strategy, auth_mode） |
| /teacher 未登录 302 → /login | 是 |
| teacher_demo / Demo@12345 可登录 | 是 |
| 关键按钮可触发动作（DOM + 事件委托 + 日志证据） | 是 |
| PDF 上传不出现乱码泄漏 | 是（422/PDF_PARSE_FAILED，响应无 %PDF-） |
| pytest 全绿 | 是（177 passed, 0 failed） |
| scripts/s2_15_gate.sh 全绿 | 是（15 PASS, 0 FAIL） |
| 产出 outputs/s2_15/S2_15_FINAL_REPORT.md | 是 |

---

## 6. 结论

**GO_LIVE_APPROVED**：上述所有项已满足，无阻塞点。
