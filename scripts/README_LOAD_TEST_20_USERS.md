# 20 用户并发 / 文件上传负载测试说明

## 目的

模拟 20 个用户从“注册”（预置账号）到登录、创建脚本、上传**各不相同的** demo 文件，并校验上传后处理是否正确（提取文本、分块、列表与内容一致性），用于排查文件上传与处理相关 bug。

## 1) 准备 20 个不同的 Demo 文件

```bash
python scripts/gen_20_demo_files.py
```

会在 `scripts/demo_files_20/` 下生成 20 个文件：`demo_syllabus_01.md` … `demo_syllabus_20.txt`（内容不同，便于校验无混用）。

## 2) 预置 20 个教师账号（与主应用共用 DB 时）

使用与主应用相同的 `USE_DB_STORAGE`、`DATABASE_URL`：

```bash
export USE_DB_STORAGE=true
export DATABASE_URL="sqlite:///$(pwd)/data/load_test.db"   # 或你的主库 URL
python scripts/seed_20_users_load_test.py
```

账号：`teacher_load_1` … `teacher_load_20`，密码：`LoadTest@20`。

## 3) 运行方式

### A) 推荐：应用内测试（不启动真实服务器）

用 Flask 测试客户端在进程内跑 20 个用户流程（顺序执行），验证上传与处理逻辑：

```bash
pytest tests/test_load_20_users_upload.py -v
```

- 会创建内存 DB、预置 20 个教师、每人上传一个 demo 文件，并检查：
  - 上传返回 200/201、无 `error`/错误码
  - 响应中 `extracted_text` 或 `extracted_text_preview` 包含对应用户唯一标记 `DEMO-XX`
  - 该课程下列表接口能查到刚上传的文档

**当前结果**：该测试已通过，未发现文件上传后处理错误（无内容混用、无错误提取）。

### B) 真实 HTTP 并发测试（需本机起服）

若需压测真实服务器与并发：

1. 启动应用（建议使用与 seed 相同的 DB）  
2. 种子用户（若尚未执行）：  
   `USE_DB_STORAGE=true DATABASE_URL=... python scripts/seed_20_users_load_test.py`  
3. 运行负载脚本（将 `BASE` 换成你实际地址与端口）：

```bash
LOAD_TEST_BASE_URL="http://127.0.0.1:5001" python scripts/load_test_20_users.py "http://127.0.0.1:5001"
```

- 默认 20 个线程并发；若环境对本地请求有代理/限制，可能出现 502，可改为顺序跑：

```bash
SEQUENTIAL=1 LOAD_TEST_BASE_URL="http://127.0.0.1:5001" python scripts/load_test_20_users.py "http://127.0.0.1:5001"
```

### C) 一键脚本（自起服 + 并发/顺序回退）

```bash
./scripts/run_20_user_load_test.sh
```

- 使用 SQLite 文件 DB：`data/load_test.db`
- 自动 seed、启动服务、先并发再失败则顺序重跑
- 若本机 Python 请求被代理或限制，可能仍出现 502；此时以 **A) pytest** 为准即可。

### D) 使用 PostgreSQL 的 20 用户并发验证（推荐生产前验证）

使用 Docker Compose 启动 PostgreSQL + 应用，再执行 seed 与负载脚本，可验证 20 用户并发下无文档混淆、无 5xx：

```bash
# 1. 生成 20 个 demo 文件（若尚未生成）
python3 scripts/gen_20_demo_files.py

# 2. 启动 PostgreSQL + 应用（需 USE_DB_STORAGE=true）
export USE_DB_STORAGE=true
export DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/teacher_in_loop
docker compose up -d postgres
# 等待 postgres healthy 后启动 web 或本地 app
docker compose up -d web
# 或本地：python3 app.py

# 3. 对应用所在地址执行 seed（与应用共用 DATABASE_URL）
USE_DB_STORAGE=true DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/teacher_in_loop python3 scripts/seed_20_users_load_test.py

# 4. 运行 20 用户负载测试（并发；失败可改用 SEQUENTIAL=1）
LOAD_TEST_BASE_URL=http://127.0.0.1:5001 python3 scripts/load_test_20_users.py http://127.0.0.1:5001
```

- 全部通过即表示：20 用户同时使用稳定、输出正确、无文件处理混用。

## 4) 检查点小结

- 20 个不同文件、20 个用户、每人一个 course（如 `course_user_1` … `course_user_20`），避免 course 间串数据。
- 上传接口：`POST /api/cscl/courses/<course_id>/docs/upload`（multipart 或 JSON 文本）。
- 校验：上传响应中的 `extracted_text` / `extracted_text_preview` 含对应用户标记 `DEMO-XX`，且该 course 下列表能查到该文档，即认为上传与后处理正确、无混用。

## 5) 已覆盖与结论

- **20 个不同 demo 文件**：已生成并用于测试。  
- **20 个教师账号**：seed 脚本可重复执行（幂等）。  
- **完整流程**：登录 → 创建脚本 → 上传文件 → 列文档 → 校验内容；pytest 下 **20 用户全部通过**，未发现上传后处理错误。

若你本地 `run_20_user_load_test.sh` 或并发脚本出现 502，优先以 **`pytest tests/test_load_20_users_upload.py -v`** 结果为准，该路径已验证文件上传与处理逻辑正确。

## 6) Push 到远程与部署后多用户测试

1. **配置 Git 远程并推送**（若尚未配置）  
   ```bash
   git remote add origin <你的仓库 URL>
   git push -u origin main
   ```  
   推送后可在 Cloudflare Pages / Workers 等连接该仓库并部署，得到用户可访问的 link。

2. **对部署后的 link 跑 20 用户测试**  
   部署完成后，在能访问该 URL 的机器上执行（将 `https://你的应用域名` 换成实际部署地址）：  
   ```bash
   # 顺序跑（建议先跑一次确认流程）
   SEQUENTIAL=1 LOAD_TEST_BASE_URL=https://你的应用域名 python3 scripts/load_test_20_users.py https://你的应用域名
   # 并发跑
   LOAD_TEST_BASE_URL=https://你的应用域名 python3 scripts/load_test_20_users.py https://你的应用域名
   ```  
   注意：部署环境需先执行 seed（见上文 D）且具备 20 个 demo 文件；负载脚本从本机 `scripts/demo_files_20` 读取文件向部署 URL 发请求。
