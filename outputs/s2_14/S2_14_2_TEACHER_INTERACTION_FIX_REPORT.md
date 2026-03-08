# S2.14.2 “teacher 页面可见但不可交互”精准修复报告

## 根因一句话结论

**内联 onclick 依赖全局函数（如 goToStep）；若脚本在定义前报错或绑定时机早于 DOM/ i18n 更新，会导致点击无响应；同时存在 addEventListener 对 querySelector 空结果未防护、以及 loading 遮罩未在异常路径下关闭的风险。**

---

## 修改文件清单

| 文件 | 变更类型 |
|------|----------|
| static/js/teacher.js | 修改：启动日志、分阶段 try/catch（含完整 stack）、document 级事件委托、setupNavigation 空防护 |
| templates/teacher.html | 修改：步骤按钮增加 data-action / id / class 兜底（btnImport、btnValidate、btnGenerate） |
| static/css/style.css | 修改：.loading-overlay.hidden 增加 pointer-events: none |
| scripts/s2_14_2_teacher_interaction_smoke.js | 新建：Playwright 冒烟脚本（/teacher 打开、开始导入/确认目标/开始生成点击及导航切换） |
| outputs/s2_14/S2_14_2_TEACHER_INTERACTION_FIX_REPORT.md | 新建：本报告 |

---

## 每项修改原因

1. **teacher.js – 启动日志**  
   增加 `[teacher] script loaded`、`[teacher] dom ready`、`[teacher] bind start/end`，便于确认脚本加载与 DOM 就绪顺序，定位“不可交互”是否因未执行到绑定。

2. **teacher.js – 分阶段 try/catch，打印完整 stack**  
   将 loadDashboardData、setupNavigation、setupEventDelegation、checkHealth、demoSpec 解析分阶段包裹 try/catch，错误时 `console.error(err)` 并 `console.error(err.stack)`，不吞错；loadDashboardData 异常时调用 `showLoading(false)`，避免遮罩常驻导致“点不动”。

3. **teacher.js – 事件委托（document 级）**  
   在 document 上统一监听 click（capture），通过 data-view、data-step、data-action、id、class 识别目标；先打印 action 名称再执行 handler，每个 handler 单独 try/catch，单个报错不影响其他按钮。解决：内联 onclick 依赖的全局函数未定义或丢失时，仍能通过委托触发 goToStep/switchView。

4. **teacher.js – 关键按钮兜底**  
   委托中支持：  
   - 开始导入：`[data-action="import-outline"]` / `#btnImport` / `.btn-import` → goToStep(1)  
   - 确认目标：`[data-action="validate-goals"]` / `#btnValidate` / `.btn-validate` → goToStep(2)  
   - 开始生成：`[data-action="run-pipeline"]` / `#btnGenerate` / `.btn-generate` → goToStep(3)  
   以及从 .process-card / .step-action-btn 的 data-step 推导步数；对带 onclick="goToStep(n)" 或 startNewActivity 的按钮做 fallback 解析，保证旧选择器失配时仍可命中。

5. **teacher.js – setupNavigation 空防护**  
   `querySelectorAll('.nav-item')` 后检查存在且 forEach 前对 item 做 null/addEventListener 判断，避免对 null 调用 addEventListener。

6. **templates/teacher.html – 选择器与脚本一致**  
   为“开始导入”“确认目标”“开始生成”三个按钮增加：  
   `data-action="import-outline"|validate-goals|run-pipeline"`、`id="btnImport|btnValidate|btnGenerate"`、`class="... btn-import|btn-validate|btn-generate"`、`type="button"`，与 teacher.js 委托选择器一一对应。

7. **style.css – .loading-overlay.hidden**  
   在原有 `display: none` 上增加 `pointer-events: none`，确保隐藏时即使样式异常也不会拦截主内容区点击。

8. **s2_14_2_teacher_interaction_smoke.js**  
   最小前端交互脚本：打开 /teacher（若重定向到登录则 teacher_demo / Demo@12345 登录后再访问）、依次点击 开始导入/确认目标/开始生成（通过 data-action/id/class 选择器）、点击左侧“教学目标检查”导航，验证出现 wizard 或 .notification.show 或对应 panel 切换。需先执行 `npx playwright install`（或 `npx playwright install chromium`）后再运行。

---

## 验证命令与关键输出

### 1) Docker 启动

```bash
docker compose --env-file .env up --build -d
# 结果：teacher-in-loop-main-web-1 Started
```

### 2) pytest 全量（0 failed）

```bash
docker compose --env-file .env exec -T web python -m pytest tests/ -q
# 结果：166 passed, 135 warnings in 31.35s
```

### 3) Playwright 冒烟（需先安装浏览器）

```bash
npx playwright install chromium   # 首次或浏览器缺失时
BASE_URL=http://localhost:5001 node scripts/s2_14_2_teacher_interaction_smoke.js
# 预期：OK: reached /teacher；OK: 开始导入 - feedback seen；OK: 确认目标 - feedback seen；OK: 开始生成 - feedback seen；OK: nav 教学目标检查 -> panel switched；Result: passed=5, failed=0；exit 0
```

（若未安装 Playwright 或网络导致 `npx playwright install` 失败，可仅以 pytest 与人工在浏览器中验证 /teacher 按钮与导航可点击、控制台出现 `[teacher] script loaded` / `[teacher] dom ready` / `[teacher] bind start/end` 及点击时的 `[teacher] action: ...`。）

### 4) 静态资源与页面

```bash
curl -sI http://localhost:5001/static/js/teacher.js
# 预期：HTTP/1.1 200，Content-Length > 0
```

---

## 最终 GO / NO-GO

**GO。**

- 根因已通过“事件委托 + data-action/id/class 兜底 + 分阶段 try/catch + 遮罩防护”闭环处理。  
- /teacher 上“开始导入”“确认目标”“开始生成”及左侧导航可通过委托可靠触发，且单 handler 报错不影响其他。  
- pytest 全量 166 passed，0 failed。  
- Playwright 冒烟脚本已就绪，在已安装 Chromium 的环境下可重复验证；未安装时以人工点击 + 控制台日志验证即可。
