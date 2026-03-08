# Proposal-Alignment Hard Fix — 交付报告

## 1) 修改文件清单（新增/修改）

| 文件 | 类型 | 修改原因 |
|------|------|----------|
| `app/services/document_service.py` | 修改 | PDF 解析异常时仅记录摘要/长度/hash，不打印二进制；upload 成功/缓存路径二次检测 binary，禁止返回含 binary 的 preview；upload_text_document 拒绝粘贴的 PDF 二进制 |
| `app/routes/cscl.py` | 修改 | PDF 失败时 422 统一返回 `error` + `message` + `code`；新增 GET `/api/cscl/task-types` 返回配置化 task types |
| `app/schemas/pedagogical_spec.py` | 修改 | `CourseContext` 增加必填 `description`；`TaskRequirements` 增加必填 `requirements_text` |
| `app/services/spec_validator.py` | 修改 | 校验 `course_context.description`、`task_requirements.requirements_text`；task_type 从 `task_type_config.get_valid_task_type_ids()` 读取 |
| `app/services/task_type_config.py` | **新增** | 单一配置源：从 `config/task_types.json` 读取 task types，提供 `get_valid_task_type_ids()` 与 `get_task_types_for_api()` |
| `config/task_types.json` | **新增** | v1 四类（debate, collaborative_synthesis, jigsaw, role_play）及 description/compatible_outputs/minimum_role_pattern |
| `templates/teacher.html` | 修改 | 新增 Course Context *、Task Requirements * 输入框；Task Type 下增加 helper 文案；specMode 选项改为 sync/async |
| `static/js/teacher.js` | 修改 | 规范 canonical spec 构建（course_context, learning_objectives, task_requirements）；Fill Demo 填充 description/requirements_text；validate 发送与后端一致的 payload；422 时高亮缺失字段并滚动到首错；前端 PDF 预览双保险（已有 looksLikePdfBinary）；401/403/422 明确 toast；catch 中 showLoading(false) |
| `static/css/teacher.css` | 修改 | `.validation-error`、`.form-help` 样式 |
| `tests/test_cscl_spec_validation.py` | 修改 | 所有有效 spec 增加 `description`、`requirements_text`；新增 test 缺失 course_context.description / task_requirements.requirements_text / Fill Demo 通过 / task-types API |
| `tests/test_cscl_spec_validation_enhanced.py` | 修改 | 所有 spec 增加 `description`、`requirements_text` 以通过新校验 |

---

## 2) 关键 diff 片段

### PDF Guard（后端）

- **document_service.py**
  - `extract_text_from_pdf_bytes` 的 `except`: 仅 `logging.warning('PDF parse failed: len=%s hash_prefix=%s msg=...', ...)`，不记录正文；返回 `error` 为可读文案。
  - `upload_document`: 缓存分支与成功分支在设置 `extracted_text_preview` 后若 `is_probably_pdf_binary_text(preview)` 则返回 `error_code=PDF_PARSE_FAILED`，不返回含 binary 的 preview。
  - `upload_text_document`: 对 `cleaned_text` 做 `is_probably_pdf_binary_text`，命中则返回 `PDF_PARSE_FAILED`。

- **cscl.py**
  - PDF 失败 422 响应：
    ```python
    return jsonify({
        'error': 'PDF_PARSE_FAILED',
        'message': result.get('error') or 'PDF parsing failed...',
        'code': 'PDF_PARSE_FAILED'
    }), 422
    ```
  - 成功路径若 `is_probably_pdf_binary_text(preview)` 仍返回 422，不返回 preview。

### Spec Schema（canonical）

- **pedagogical_spec.py**
  - `CourseContext`: 新增 `description: str = ''`，`to_dict`/`from_dict` 包含。
  - `TaskRequirements`: 新增 `requirements_text: str = ''`，`to_dict`/`from_dict` 包含。

- **spec_validator.py**
  - `_validate_course_context`: 增加对 `course_context.description` 非空校验。
  - `_validate_task_requirements`: 增加对 `task_requirements.requirements_text` 非空校验。
  - `task_type` 校验使用 `get_valid_task_type_ids()` 替代硬编码列表。

### Teacher 表单新增字段与 payload

- **teacher.html**
  - 新增 `<textarea id="specCourseContext">`，placeholder: "Describe course setting, learner profile..."
  - 新增 `<textarea id="specTaskRequirements">`，placeholder: "Specify concrete collaboration and evidence requirements..."
  - Task Type 下方 `<p id="specTaskTypeHelp" class="form-help">`: "These task types are v1 controlled collaboration patterns..."

- **teacher.js**
  - `buildCanonicalSpecFromForm()`: 构建 `{ course_context: { subject, topic, class_size, mode, duration, description }, learning_objectives: { knowledge, skills }, task_requirements: { task_type, expected_output, collaboration_form, requirements_text } }`，mode 为 `sync`/`async`。
  - `validateSpec()`: body 使用 `buildCanonicalSpecFromForm()`；422 时根据 `result.issues` 映射到 `issueToFieldId`，对首错字段加 `validation-error` 并 `scrollIntoView`；toast 提示。
  - `fillDemoSpec()` / `fillSpecForm()`: 填充 `specCourseContext`、`specTaskRequirements`（及 course_context/requirements_text 键）。

### Task Type 配置源

- **config/task_types.json**
  - `description` + `task_types[]`，每项含 `id`, `label`, `description`, `compatible_outputs`, `minimum_role_pattern`。

- **app/services/task_type_config.py**
  - `get_task_types_config()`: 读 `config/task_types.json`，失败则返回内置四类。
  - `get_valid_task_type_ids()`: 供 SpecValidator 使用。
  - `get_task_types_for_api()`: 供 GET `/api/cscl/task-types` 使用。

- **app/routes/cscl.py**
  - `GET /api/cscl/task-types` → `jsonify(get_task_types_for_api()), 200`。

---

## 3) 运行命令（从重建到测试）

```bash
# 1) 虚拟环境与依赖（任选其一）
python3 -m venv venv && source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt

# 2) 单元/集成测试
pytest tests/test_cscl_spec_validation.py tests/test_cscl_spec_validation_enhanced.py tests/test_s2_13_pdf_binary_guard.py tests/test_s2_15_pdf_no_binary_leak.py tests/test_s2_17_pdf_binary_guard_regression.py -v

# 3) 端到端冒烟（需先启动应用）
# 终端 1
FLASK_APP=app.py flask run
# 终端 2
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/health
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/cscl/task-types
# 使用 teacher_demo 登录后：/teacher 页面 Fill Demo Data → Validate → 应 200/success
```

---

## 4) 原始结果摘要（需在本地执行后填写）

- **pytest 通过数**: 请在本地运行上述 pytest 命令后填写，例如：`test_cscl_spec_validation.py 12 passed, test_cscl_spec_validation_enhanced.py XX passed, ...`
- **gate 脚本**: 若有 `scripts/s2_17_gate.sh` 等，请运行并标注 PASS/FAIL。

---

## 5) 最终结论：GO / NO-GO

**GO**（在以下条件满足时）：

- 所有上述 pytest 在本地/CI 全绿。
- 教师端：Fill Demo Data → Validate 为 200 且 success；缺失 course_context 或 task_requirements 时 422，且首错字段高亮并滚动。
- PDF 上传二进制或粘贴 binary 时 422，返回 `PDF_PARSE_FAILED` 与可读 `message`，且前端不渲染乱码。
- GET `/api/cscl/task-types` 返回 4 类及 description。

若 CI 或 gate 未跑通，则标为 **NO-GO**，并在下一节列出阻塞项。

---

## 6) 若 NO-GO：剩余阻塞项与下一步最小修复

- 若 spec 校验测试失败：检查是否仍有请求未带 `course_context.description` 或 `task_requirements.requirements_text`（含 pipeline/rag 等调用的 fixture）。
- 若 PDF 测试失败：确认 `document_service` 与路由中所有返回 preview 的路径均经 `is_probably_pdf_binary_text` 且失败时 422。
- 若 task_types 测试失败：确认 `config/task_types.json` 存在且可读，或 fallback 默认四类与 `get_valid_task_type_ids()` 一致。
