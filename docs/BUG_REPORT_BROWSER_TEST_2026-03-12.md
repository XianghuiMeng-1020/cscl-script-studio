# CSCL Script Studio — 浏览器模拟测试 Bug 报告

**测试环境**: 内置浏览器，URL: https://web-production-591d6.up.railway.app/  
**测试日期**: 2026-03-12  
**测试内容**: 模拟真实教师/学生上传与操作流程

---

## 测试流程摘要

1. **教师端**
   - 使用 `teacher_demo` / `Demo@12345` 登录
   - 点击「Start Import」→ 在导入弹窗中粘贴大纲文本（Course: Introduction to CSCL, Topic: Scripted Collaboration, Objectives: …）
   - 点击「Continue」进入 Step 2
   - 进入「Course Documents」查看文档卡片

2. **学生端**
   - 使用 `student_demo` / `Demo@12345` 登录
   - 输入邀请码 `DEMO` 加入活动
   - 在活动内提交任务（Submit）

---

## 已发现 Bug

### Bug 1: 粘贴大纲后 Step 2 表单未根据粘贴内容填充（逻辑/产品）— **已修复**

**现象**: 在 Step 1 粘贴「Introduction to CSCL / Scripted Collaboration / Jigsaw」等文本并点击 Continue 后，Step 2 的教学计划表单显示的是「Introduction to Data Science / Algorithmic Fairness in Education」等与粘贴内容完全无关的默认/演示数据。

**原因分析**:
- Step 1 的 Continue 仅把粘贴文本当作「Teaching materials」上传到 `/courses/.../docs/upload`，并未调用「从文本提取教学计划」的接口。
- Step 2 的表单数据来自：页面默认值、或当前/已有 script 的 spec、或 sessionStorage 中的 demoSpec，而不是本次粘贴的内容。
- 用户预期：粘贴大纲后，系统应解析该文本并自动填充 Step 2 的表单（或至少给出“填充建议”），当前行为与预期不符。

**修复** (2026-03-12):
- 在 `wizardNext()` 中，Step 1 粘贴上传成功后读取响应中的 `doc_id`，对该文档调用 `GET /courses/:id/docs/:docId/prefill`，用返回的 suggestions 构建 spec 并调用 `fillSpecForm(spec)`，再进入 Step 2。这样 Step 2 表单会反映刚粘贴的大纲内容（规则提取的课程名、主题、目标等）。

---

### Bug 2: 教师端课程文档区域存在硬编码中文（已修复）

**现象**: 在语言为 English 时，课程文档卡片上仍显示中文：
- 按钮文案：「填充建议」
- 无预览时提示：「未提取到文本」
- 点击「填充建议」成功后的提示：「已填入建议，请确认或修改后再验证」

**修复**: 已为上述文案增加 i18n 键并改为使用 `t()`：
- `teacher.doc.prefill_btn` → 简体/繁体/英文
- `teacher.doc.no_text_extracted` → 简体/繁体/英文
- `teacher.doc.prefill_success` → 简体/繁体/英文  

修改文件：`static/js/i18n.js`、`static/js/teacher.js`。

---

## 已验证正常的行为

- 教师登录、学生登录（teacher_demo / student_demo, Demo@12345）正常。
- 教师端 Step 1：粘贴文本 + Continue 能上传材料并进入 Step 2。
- 学生端：输入邀请码 DEMO 可成功加入活动，活动标题与场景目标显示正确。
- 学生端提交任务（Submit）可点击，无控制台报错。
- Quick Demo 从首页可进入；Demo 页「Teacher Sign In」会跳转到教师登录页。

---

## 未在本次自动化中覆盖的部分

- 真实文件上传（Browse Files / 拖拽）：依赖本地文件选择，未在本次浏览器自动化中执行。
- 生成流水线（Run Pipeline）及发布流程：未完整跑通。
- 学生端「上传」类操作（若有）：未单独测试。

---

## 复现与回归建议

1. **Bug 1**:  
   - 教师登录 → Start Import → 粘贴一段与默认 demo 明显不同的课程大纲（如「Course: X, Topic: Y」）→ Continue。  
   - 检查 Step 2 表单中的 Course、Topic、Objectives 等是否来自该段粘贴内容（或至少来自其 prefill 结果），而不是固定的 Data Science / Algorithmic Fairness 示例。

2. **Bug 2**:  
   - 将界面语言切到 English，进入教师端 Course Documents，确认按钮与提示均为英文且无中文残留。
