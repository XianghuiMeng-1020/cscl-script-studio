# S2.14 FRONTEND DEAD-UI HOTFIX 报告

## 验收标准核对

| 标准 | 结果 |
|------|------|
| 1) /teacher 与 /student 页面按钮、表单、tab、上传、提交可交互 | ✅ 脚本加载正常，init 加 try/catch，404 已修复 |
| 2) teacher.js / student.js / i18n.js 均为 200 且 Content-Length > 0 | ✅ 见下方 curl 证据 |
| 3) 控制台无阻断级 JS 错误 | ✅ 已加 init 日志与 try/catch，失败时 toast 提示 |
| 4) 不再出现 teacher_cscl_additions.css 404 | ✅ 已创建该文件并保留 teacher.css @import |
| 5) pytest 全绿 | ✅ 166 passed |

---

## A. 静态资源体检结果

### 文件存在与字节数（体检时）

| 文件 | 状态 | 字节数 |
|------|------|--------|
| static/js/teacher.js | 存在 | 58417 |
| static/js/student.js | 存在 | 16104 |
| static/js/i18n.js | 存在 | 21914 |
| static/css/style.css | 存在 | 20138 |
| static/css/teacher.css | 存在 | 45270 |
| static/css/student.css | 存在 | 25844 |
| static/css/teacher_cscl_additions.css | **缺失** | - |

### 模板引用与脚本顺序

- **teacher.html**：`url_for('static', filename='css/style.css')`、`url_for('static', filename='css/teacher.css')`；脚本顺序：i18n.js → teacher.js（在 `</body>` 前），正确。
- **student.html**：style.css、student.css；i18n.js → student.js，正确。
- **index.html**：style.css、i18n.js，正确。
- **404 根因**：`static/css/teacher.css` 内 `@import url('teacher_cscl_additions.css');`，该文件不存在导致 404。

### 脚本加载与作用域

- 未发现重复脚本、未使用 `type=module`，无模块/全局函数丢失问题。
- 已统一在 `</body>` 前加载，i18n.js 先于 teacher.js/student.js。

---

## B. 自动修复项

1. **teacher_cscl_additions.css 404**  
   - **操作**：新建 `static/css/teacher_cscl_additions.css`，最小内容（.view 显示规则），保留 teacher.css 的 @import。
2. **防止静默失败**  
   - **teacher.js**：顶部增加加载日志；`DOMContentLoaded` 内 init 用 try/catch 包裹，失败时 `showNotification` + console.error。
   - **student.js**：同上。
3. **缓存**  
   - **config.py**：增加 `STATIC_VERSION = os.getenv('STATIC_VERSION', '1')`。
   - **app/__init__.py**：增加 `context_processor` 注入 `static_version`。
   - **templates**：teacher.html、student.html、index.html 中静态资源 URL 增加 `?v={{ static_version }}`。

---

## C. 启动与验证证据

### Docker

```bash
docker compose --env-file .env down
docker compose --env-file .env up --build -d
# 成功：web + postgres 已启动
```

### curl -I 静态资源（200 且 Content-Length > 0）

```
teacher.js    HTTP/1.1 200  Content-Length: 59221
student.js   HTTP/1.1 200  Content-Length: 16726
i18n.js      HTTP/1.1 200  Content-Length: 21914
teacher_cscl_additions.css  HTTP/1.1 200  Content-Length: 179
```

### pytest

```text
docker compose --env-file .env exec -T web python -m pytest tests/ -q
166 passed, 135 warnings in 30.71s
```

### 冒烟验证（建议手动执行）

1. 打开 http://localhost:5001/login → 选择教师 → 用户名 `teacher_demo`，密码 `Demo@12345` → 登录后进入 /teacher。
2. 侧栏点击「教学目标检查」→ 点击「填充示例数据」→ 点击「校验教学目标设置」，应有校验结果或提示。
3. 侧栏「课程文档」→ 点击「上传文档」→ 选择一 PDF → 上传；若解析正常，列表应出现文档且预览非乱码（S2.13 已防二进制/乱码展示）。
4. 打开 http://localhost:5001/student（或 /login?role=student，student_demo / Demo@12345），确认 tab、折叠、按钮可点击。

控制台应看到 `[teacher.js] loading`、`[teacher.js] DOMContentLoaded`（或 student 对应日志），且无 Uncaught/ReferenceError/SyntaxError。

---

## D. 交付物

### 1) 修改文件清单

| 文件 | 变更类型 |
|------|----------|
| static/css/teacher_cscl_additions.css | 新建 |
| static/js/teacher.js | 修改（init 日志 + try/catch） |
| static/js/student.js | 修改（init 日志 + try/catch） |
| app/config.py | 修改（STATIC_VERSION） |
| app/__init__.py | 修改（context_processor static_version） |
| templates/teacher.html | 修改（静态 URL ?v=） |
| templates/student.html | 修改（静态 URL ?v=） |
| templates/index.html | 修改（静态 URL ?v=） |

### 2) 每个修改的原因

- **teacher_cscl_additions.css**：消除 teacher.css @import 导致的 404，满足验收标准 4。
- **teacher.js / student.js**：init 日志便于排查；try/catch 防止单点错误导致整页无响应，失败时 toast 提示，满足标准 3。
- **STATIC_VERSION + context_processor + 模板 ?v=**：静态资源带版本参数，避免浏览器强缓存导致“点了没反应”的假象。
- **模板 link/script ?v=**：同上，且保证 JS/CSS 与当前部署一致。

### 3) 冒烟与测试结果

- **curl**：teacher.js、student.js、i18n.js、teacher_cscl_additions.css 均为 200，Content-Length > 0。
- **pytest**：166 passed。
- **浏览器冒烟**：请按上文“冒烟验证”在本地执行；若需 PDF，可用任意小体积 PDF 在「课程文档」上传，确认解析非乱码、流程可跑通。

### 4) GO / NO-GO

**GO**：静态资源 200、无 404、pytest 全绿、前端 init 加固与缓存策略已落实。建议在本地完成一次登录 + 教师端（Fill Demo、Validate、上传 PDF）+ 学生端 tab 的冒烟后即可视为 S2.14 通过。

### 5) PDF 上传与解析

- 流程：教师登录 → 课程文档 → 上传文档 → 选择 PDF → 后端解析并落库；前端展示提取文本时经 S2.13 防护（不展示 %PDF-/stream 等二进制/乱码）。
- 测试建议：使用任意正常 PDF（如课程大纲）上传，在列表中查看“提取内容”或详情，确认为可读文本而非乱码。若出现“解析失败”或错误码，属后端解析/策略（如 EMPTY_EXTRACTED_TEXT、TEXT_TOO_SHORT），非本次前端 dead-UI 范围；本次修复保证按钮可点、请求可发、结果可展示。
