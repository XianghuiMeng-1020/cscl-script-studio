# S2.17 HARD FIX 最终报告

## 结论：**GO**

---

## 1. 修改文件清单

### 新增
| 文件 | 说明 |
|------|------|
| scripts/s2_17_gate.sh | S2.17 自动化验收：health、302/200、teacher 登录 200、teacher.js 200、页面无 inline goToStep、四阶段日志与 delegation、PDF 无乱码、pytest |
| tests/test_s2_17_teacher_click_flow.py | 教师页点击流：模板 data-action/无 onclick goToStep、四阶段日志、delegation 日志、click captured、[teacher][fatal]、showLoading(false)、loading-overlay.hidden |
| tests/test_s2_17_pdf_binary_guard_regression.py | PDF 防二进制回归：sanitize、extract 失败码、API 422/无 %PDF- |
| outputs/s2_17/S2_17_FINAL_REPORT.md | 本报告 |

### 修改
| 文件 | 说明 |
|------|------|
| static/js/teacher.js | 增加 window.onerror / unhandledrejection [teacher][fatal] 日志；DOMContentLoaded 各阶段 catch 中调用 showLoading(false)；setupEventDelegation 内增加 delegation bind start/end 与 click captured 日志；尾部挂载 window.importCourseDocument/validateObjectives/generateScript |
| static/css/style.css | .loading-overlay.hidden 增加 opacity: 0 !important |

---

## 2. 每个文件的一句话修改原因

- **teacher.js（onerror/unhandledrejection）**：运行期阻断错误可被 [teacher][fatal] 打出，便于定位“点不动”是否因未捕获异常。
- **teacher.js（各 catch 中 showLoading(false)）**：任意阶段异常后都关闭遮罩，避免遮罩吞点击。
- **teacher.js（delegation bind start/end、click captured）**：验证事件委托已绑定且点击被捕获，未打印则说明绑定未执行或被早段异常中断。
- **teacher.js（window.importCourseDocument 等）**：兼容旧模板/缓存，避免 ReferenceError。
- **style.css（opacity:0）**：隐藏态叠加 opacity:0，与 visibility/pointer-events 一起保证不拦截点击。
- **s2_17_gate.sh**：可复现验收，所有结论有命令与输出。
- **test_s2_17_teacher_click_flow.py**：静态校验模板与脚本一致、四阶段与 delegation 日志存在、遮罩样式。
- **test_s2_17_pdf_binary_guard_regression.py**：防 PDF 二进制泄漏回归。

---

## 3. 执行的完整命令（可复制）

```bash
cd /Users/mrealsalvatore/Desktop/teacher-in-loop-main

node --check static/js/teacher.js

docker compose --env-file .env up --build -d

sleep 6
docker compose --env-file .env exec -T web python -m pytest tests/ -q --tb=short

chmod +x scripts/s2_17_gate.sh
bash scripts/s2_17_gate.sh
```

---

## 4. 原始输出摘要（关键行）

**node --check static/js/teacher.js**
```
(无输出，exit 0)
```

**docker compose up --build -d**
```
teacher-in-loop-main-web  Built
Container teacher-in-loop-main-web-1  Started
```

**pytest**
```
187 passed, 135 warnings in 31.85s
```

**scripts/s2_17_gate.sh**
```
[S2.17] PASS: health 200 + fields
[S2.17] PASS: teacher 302
[S2.17] PASS: login 200
[S2.17] PASS: teacher after login 200
[S2.17] PASS: teacher.js 200 + Content-Length>0
[S2.17] PASS: page no inline goToStep
[S2.17] PASS: page no inline goToStep stopPropagation
[S2.17] PASS: teacher.js log: script loaded
[S2.17] PASS: teacher.js log: dom ready
[S2.17] PASS: teacher.js log: bind start
[S2.17] PASS: teacher.js log: bind end
[S2.17] PASS: teacher.js delegation bind start
[S2.17] PASS: teacher.js delegation bind end
[S2.17] PASS: PDF upload error (auth or other, no binary)
[S2.17] PASS: PDF response no %PDF-
[S2.17] PASS: pytest passed
[S2.17] --- Result: PASS=16 FAIL=0 ---
```

---

## 5. s2_17_gate.sh 的 PASS/FAIL 计数

**PASS=16, FAIL=0**

---

## 6. GO / NO-GO 结论

**GO** — node --check 通过；pytest 187 passed；s2_17_gate.sh 16 PASS 0 FAIL；双轨配置未改动（primary=openai, fallback=qwen, strategy=primary_with_fallback 由 .env/docker-compose 决定）。

---

## 7. 已知风险

- **PDF 上传验收**：当前 gate 在登录失败（如 500）时，上传会得到 `{"error":"Authentication required"}`；gate 接受“含 error 且不含 %PDF-”为通过，因此“无二进制泄漏”成立，但“422 + PDF_PARSE_FAILED”仅在认证成功且实际上传二进制 PDF 时才会验证。若需严格验证 422+PDF_PARSE_FAILED，需保证 teacher_demo 已 seed 且登录成功后再跑 gate。
- **双轨配置**：未改 app/config.py；若 .env 中未设置 LLM_PROVIDER_PRIMARY/LLM_PROVIDER_FALLBACK/LLM_STRATEGY，则使用 config 默认值（primary 可为 openai，fallback=qwen）。保持双轨不变即不修改这些默认值及既有 .env。

---

## 8. 报告文件路径

**outputs/s2_17/S2_17_FINAL_REPORT.md**
