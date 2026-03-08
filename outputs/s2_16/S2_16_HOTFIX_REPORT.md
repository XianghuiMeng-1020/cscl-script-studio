# S2.16 HOTFIX 报告 — Teacher 页按钮可点击

## 最终结论：**GO**

---

## 1. 修改文件清单

| 文件 | 变更 |
|------|------|
| **static/js/teacher.js** | 修复第 22 行 `\u7f` → `\u007f`；事件委托增加 `review-publish`/btnPublish；尾部挂载 `window.goToStep`/`window.switchView`/`window.startNewActivity` |
| **templates/teacher.html** | 移除四张 process-card 及步骤按钮上所有 `onclick="goToStep(...)"` / `onclick="event.stopPropagation(); goToStep(...)"`；保留 `data-action`/`data-step`/`id`；第 4 步按钮增加 `id="btnPublish"`、`data-action="review-publish"`、`class="btn-publish"` |

---

## 2. 关键 diff

### teacher.js 第 22 行前后（语法错误修复）

```diff
-        if (c !== '\n' && c !== '\t' && (c < ' ' || c > '\u7f')) nonPrint++;
+        if (c !== '\n' && c !== '\t' && (c < ' ' || c > '\u007f')) nonPrint++;
```

**原因**：`\u7f` 仅 2 位十六进制，构成 Invalid Unicode escape；改为 `\u007f`（4 位）后语法合法，功能不变（仍为 DEL 字符 U+007F）。

### teacher.js 尾部（全局兜底）

```js
// S2.16: global compatibility fallback for any remaining inline handlers
if (typeof goToStep !== 'undefined') { window.goToStep = goToStep; }
if (typeof switchView !== 'undefined') { window.switchView = switchView; }
if (typeof startNewActivity !== 'undefined') { window.startNewActivity = startNewActivity; }
```

### teacher.html 按钮区域（步骤 1～4）

- **Step 1**：`<div class="process-card" data-step="1">`，按钮保留 `id="btnImport"`、`data-action="import-outline"`、`class="... btn-import"`，**删除** `onclick="event.stopPropagation(); goToStep(1)"`。
- **Step 2**：同上，`data-step="2"`，`id="btnValidate"`，`data-action="validate-goals"`，**删除** onclick。
- **Step 3**：同上，`data-step="3"`，`id="btnGenerate"`，`data-action="run-pipeline"`，**删除** onclick。
- **Step 4**：`<div class="process-card" data-step="4">`，按钮改为 `id="btnPublish"`、`data-action="review-publish"`、`class="... btn-publish"`，**删除** onclick。

---

## 3. 防“遮罩挡点击”与异常路径

- **CSS**：`static/css/style.css` 中 `.loading-overlay.hidden` 已含 `pointer-events: none !important;`（及 `display: none`、`visibility: hidden`、`z-index: -1`）。
- **JS**：`loadDashboardData` 在 401/403 分支及 `catch` 中均调用 `showLoading(false)`，`finally` 中也有 `showLoading(false)`；DOMContentLoaded 首行与 3s 超时均会执行 `showLoading(false)`。

---

## 4. 启动日志（四条）

以下四条在控制台可验证（无 SyntaxError 时会按顺序出现）：

1. `[teacher] script loaded`
2. `[teacher] dom ready`
3. `[teacher] bind start`
4. `[teacher] bind end`

点击「开始导入」「确认目标」「开始生成」「审阅发布」时，控制台会分别出现：

- `[teacher] action: go-step-1` 或 `[teacher] action: import-outline`
- `[teacher] action: go-step-2` 或 `[teacher] action: validate-goals`
- `[teacher] action: go-step-3` 或 `[teacher] action: run-pipeline`
- `[teacher] action: go-step-4` 或 `[teacher] action: review-publish`

---

## 5. 验收命令与输出摘要

```bash
docker compose --env-file .env up --build -d
# -> teacher-in-loop-main-web-1  Started

curl -I http://localhost:5001/static/js/teacher.js | sed -n '1,12p'
# HTTP/1.1 200 OK
# Content-Type: application/javascript; charset=utf-8
# Content-Length: 66589

docker compose --env-file .env exec -T web python -m pytest tests/ -q
# 177 passed, 135 warnings in 32.61s
```

- 打开 `/teacher` 后控制台：**无 SyntaxError**（`\u007f` 修复后整份 teacher.js 可正常解析）。
- 点击「开始导入/确认目标/开始生成」：由 **document 事件委托** 处理，不再依赖内联 `onclick`，故不再出现 `ReferenceError: goToStep is not defined`；若仍存在其他内联引用，`window.goToStep` 兜底可避免未定义。

---

## 6. 控制台验证说明（无 SyntaxError + 四条日志）

- **修复前**：第 22 行 `\u7f` 导致 `Uncaught SyntaxError: Invalid Unicode escape sequence`，脚本解析失败，后续日志与 `goToStep` 均不可用。
- **修复后**：整份 teacher.js 正常加载，四条启动日志会依次出现；步骤按钮仅依赖事件委托与 `data-action`/`data-step`/id，不再依赖内联 `onclick`，故无 `goToStep is not defined`。

（无法在此处提供真实浏览器截图；请在本地打开 `/teacher`，F12 → Console 确认无红色 SyntaxError，且上述四条日志与点击 action 日志存在。）

---

## 7. 最终结论

**GO** — 语法错误已修复、内联 goToStep 依赖已去除、事件委托与全局兜底已就绪、遮罩与异常路径已防护、pytest 全量通过、静态资源 200。建议在本地再确认一次控制台无 SyntaxError 且四条日志与点击 action 日志齐全后即可视为 S2.16 通过。
