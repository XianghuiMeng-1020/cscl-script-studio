# S2.3 i18n 覆盖

## 单一真相源

`static/js/i18n.js` — 所有用户可见文案由此管理。

## 支持属性

- `data-i18n` — 元素内容
- `data-i18n-placeholder` — placeholder
- `data-i18n-title` — title
- `data-i18n-aria-label` — aria-label

## 持久化

- `localStorage.app_locale` — 刷新后保持语言

## Key 与页面映射

### 首页 (/)

| Key | zh-CN | zh-TW | en |
|-----|-------|-------|-----|
| home.title | CSCL Script Studio | CSCL Script Studio | CSCL Script Studio |
| home.subtitle | Collaborative Learning... | ... | ... |
| home.hero.title | 将课程大纲转化为... | 將課程大綱轉化為... | Transform Course Syllabi... |
| home.teacher.card | 登录为教师 | 登入為教師 | Login as Teacher |
| home.student.card | 登录为学生 | 登入為學生 | Login as Student |
| home.demo | 快速体验 Demo | 快速體驗 Demo | Quick Demo |
| home.tech.details | 了解更多技术细节 | ... | Learn More Technical Details |
| home.demo.modal.title | Demo 课程大纲 | Demo 課程大綱 | Demo Syllabus |
| home.demo.modal.copy | 复制教学目标数据 | 複製教學目標數據 | Copy Teaching Plan Data |
| home.demo.modal.start | 以教师身份开始 | 以教師身份開始 | Start as Instructor |

### 教师页 (/teacher)

| Key | zh-CN | zh-TW | en |
|-----|-------|-------|-----|
| teacher.sidebar.dashboard | Dashboard | Dashboard | Dashboard |
| teacher.sidebar.scripts | 活动项目 | 活動項目 | Activity Projects |
| teacher.sidebar.spec | 教学目标设置 | 教學目標設定 | Teaching Plan Settings |
| teacher.sidebar.pipeline | 自动生成过程 | 自動生成過程 | Auto Generation Process |
| teacher.sidebar.documents | 课程文档 | 課程文檔 | Course Documents |
| teacher.sidebar.decisions | 教师调整记录 | 教師調整記錄 | Teacher Adjustment Records |
| teacher.sidebar.quality | 质量检查结果 | 質量檢查結果 | Quality Check Results |
| teacher.sidebar.publish | Publish & Export | Publish & Export | Publish & Export |
| teacher.sidebar.settings | Settings | Settings | Settings |
| teacher.spec.title | 教学目标设置 | 教學目標設定 | Teaching Plan Settings |
| teacher.spec.validate | 校验教学目标设置 | 驗證教學目標設定 | Validate Teaching Plan Settings |
| teacher.spec.ready | 教学目标已就绪... | 教學目標已就緒... | Teaching plan is complete... |
| teacher.wizard.step1 | 上传课程大纲 | 上傳課程大綱 | Upload Syllabus |
| teacher.wizard.step2 | 教学目标设置 | 教學目標設定 | Teaching Plan Settings |
| teacher.wizard.step3 | 运行生成流程 | 執行生成流程 | Run Pipeline |
| teacher.wizard.step4 | 审阅并发布 | 審閱並發布 | Finalize & Publish |
| teacher.doc.upload | 上传文档 | 上傳文檔 | Upload Document |
| teacher.doc.empty | 暂无课程文档 | 暫無課程文檔 | No Course Documents |
| teacher.doc.upload.first | 上传第一份文档 | 上傳第一份文檔 | Upload First Document |

### 学生页 (/student)

| Key | zh-CN | zh-TW | en |
|-----|-------|-------|-----|
| student.title | 学生工作台 | 學生工作台 | Student Dashboard |
| student.current.activity | 当前活动 | 當前活動 | Current Activity |
| student.current.task | 本次任务 | 本次任務 | Current Task |
| student.task.description | 你需要完成以下任务 | ... | You need to complete... |
| student.submit | 提交任务 | 提交任務 | Submit Task |
| student.continue | 继续任务 | 繼續任務 | Continue Task |
| student.scoring | 评分标准摘要 | 評分標準摘要 | Scoring Criteria Summary |
| student.history | 历史记录 | 歷史記錄 | History Record |
| student.collaboration | 协作建议 | 協作建議 | Collaboration Suggestions |

### 通用 (common)

| Key | 说明 |
|-----|------|
| common.loading | 加载中 |
| common.error | 错误 |
| common.success | 成功 |
| common.cancel | 取消 |
| common.close | 关闭 |
| common.no.data | 暂无数据 |
| common.error.network | 网络错误 |
| common.error.server | 服务器错误 |
| common.error.login | 请先登录 |
