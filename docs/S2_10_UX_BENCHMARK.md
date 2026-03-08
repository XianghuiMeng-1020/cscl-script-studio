# S2.10 UX Benchmark（上线门槛验收）

以以下标准作为**上线门槛**（非参考）：Nielsen 10 条、Material/Ant Design 信息层级与状态反馈、WCAG 2.1 AA。

| 标准 | 对应页面/元素 | 检查结果 | 证据 |
|------|----------------|----------|------|
| 可见系统状态 | 教师/学生 dashboard、loading/成功/失败提示 | PASS/FAIL | 有 common.loading、common.error、student.error.* i18n；按钮与状态反馈存在 |
| 一致性 | 三语 i18n、按钮用词（创建/生成/发布） | PASS/FAIL | i18n.js 三语 key 一致；s2_10_ux_gate.sh 术语检查 |
| 防错 | 上传文档类型/大小、教学目标校验 | PASS/FAIL | document_service 允许类型与 PDF 防护；spec/validate 接口 |
| 识别优于回忆 | 首页双入口（教师/学生）、9 菜单明确标签 | PASS/FAIL | index 双卡片；teacher 9 data-view |
| 灵活与效率 | 向导步骤、Demo 填充 | PASS/FAIL | wizard step1–4；fillDemoSpec |
| 美学与最小化 | 主按钮、留白、层级 | PASS/FAIL | btn-primary；CSS 层级 |
| 错误识别与恢复 | 401/403/404 用户可读、重试/下一步 | PASS/FAIL | student.error.*、common.error.* |
| 帮助与文档 | 空状态“为什么+下一步” | PASS/FAIL | student.empty.reason、student.empty.next_step |
| WCAG 2.1 AA 对比度 | 主文本 4.5:1、主按钮可辨 | PASS/FAIL | teacher/student CSS 主按钮与焦点 |
| WCAG 焦点与键盘 | :focus、tab 可达 | PASS/FAIL | style/teacher/student.css 含 focus |

**判定**：全部 PASS 且 `scripts/s2_10_ux_gate.sh` 与 `scripts/s2_10_task_walkthrough.sh` 通过，方可产品级上线；任一 FAIL 即 GO_LIVE_BLOCKED。
