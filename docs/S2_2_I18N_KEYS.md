# S2.2 i18n 语言键值列表

**版本**: 1.0.0  
**更新日期**: 2026-02-05

---

## 支持的语言

- `zh-CN`: 简体中文（默认）
- `zh-TW`: 繁體中文
- `en`: English

---

## 语言键值映射表

### 首页 (Home Page)

| Key | zh-CN | zh-TW | en |
|-----|-------|-------|-----|
| `home.title` | CSCL Script Studio | CSCL Script Studio | CSCL Script Studio |
| `home.subtitle` | Collaborative Learning Activity Generator | Collaborative Learning Activity Generator | Collaborative Learning Activity Generator |
| `home.hero.title` | 将课程大纲转化为<br>结构化协作学习活动 | 將課程大綱轉化為<br>結構化協作學習活動 | Transform Course Syllabi<br>into Structured Collaborative Learning Activities |
| `home.hero.subtitle` | 简单易用的活动编排工具，帮助教师快速创建协作学习方案 | 簡單易用的活動編排工具，幫助教師快速創建協作學習方案 | An easy-to-use activity orchestration tool that helps teachers quickly create collaborative learning plans |
| `home.teacher.card` | 登录为教师 | 登入為教師 | Login as Teacher |
| `home.teacher.subtitle` | 创建活动、调整流程、发布给班级 | 創建活動、調整流程、發布給班級 | Create activities, adjust workflows, publish to class |
| `home.teacher.action` | 进入教师端 | 進入教師端 | Enter Teacher Portal |
| `home.student.card` | 登录为学生 | 登入為學生 | Login as Student |
| `home.student.subtitle` | 查看当前活动、完成协作任务、提交反思 | 查看當前活動、完成協作任務、提交反思 | View current activities, complete collaborative tasks, submit reflections |
| `home.student.action` | 进入学生端 | 進入學生端 | Enter Student Portal |
| `home.demo` | 快速体验 Demo | 快速體驗 Demo | Quick Demo |
| `home.tech.details` | 了解更多技术细节 | 了解更多技術細節 | Learn More Technical Details |

### 教师端侧边栏 (Teacher Sidebar)

| Key | zh-CN | zh-TW | en |
|-----|-------|-------|-----|
| `teacher.sidebar.dashboard` | Dashboard | Dashboard | Dashboard |
| `teacher.sidebar.scripts` | 活动项目 | 活動項目 | Activity Projects |
| `teacher.sidebar.spec` | 教学目标检查 | 教學目標檢查 | Learning Objectives Check |
| `teacher.sidebar.pipeline` | 自动生成过程 | 自動生成過程 | Auto Generation Process |
| `teacher.sidebar.documents` | 课程文档 | 課程文檔 | Course Documents |
| `teacher.sidebar.decisions` | 教师调整记录 | 教師調整記錄 | Teacher Adjustment Records |
| `teacher.sidebar.quality` | 质量检查结果 | 質量檢查結果 | Quality Check Results |
| `teacher.sidebar.publish` | Publish & Export | Publish & Export | Publish & Export |
| `teacher.sidebar.settings` | Settings | Settings | Settings |

### 学生端 (Student Page)

| Key | zh-CN | zh-TW | en |
|-----|-------|-------|-----|
| `student.title` | 学生工作台 | 學生工作台 | Student Dashboard |
| `student.current.activity` | 当前活动 | 當前活動 | Current Activity |
| `student.current.task` | 本次任务 | 本次任務 | Current Task |
| `student.task.description` | 你需要完成以下任务 | 你需要完成以下任務 | You need to complete the following tasks |
| `student.submit` | 提交任务 | 提交任務 | Submit Task |
| `student.continue` | 继续任务 | 繼續任務 | Continue Task |
| `student.scoring` | 评分标准摘要 | 評分標準摘要 | Scoring Criteria Summary |
| `student.history` | 历史记录 | 歷史記錄 | History Record |
| `student.collaboration` | 协作建议 | 協作建議 | Collaboration Suggestions |

### 通用 (Common)

| Key | zh-CN | zh-TW | en |
|-----|-------|-------|-----|
| `common.loading` | 加载中... | 載入中... | Loading... |
| `common.error` | 错误 | 錯誤 | Error |
| `common.success` | 成功 | 成功 | Success |
| `common.warning` | 警告 | 警告 | Warning |
| `common.info` | 信息 | 資訊 | Info |
| `common.confirm` | 确认 | 確認 | Confirm |
| `common.cancel` | 取消 | 取消 | Cancel |
| `common.save` | 保存 | 儲存 | Save |
| `common.delete` | 删除 | 刪除 | Delete |
| `common.edit` | 编辑 | 編輯 | Edit |
| `common.close` | 关闭 | 關閉 | Close |
| `common.back` | 返回 | 返回 | Back |
| `common.next` | 下一步 | 下一步 | Next |
| `common.previous` | 上一步 | 上一步 | Previous |
| `common.submit` | 提交 | 提交 | Submit |
| `common.upload` | 上传 | 上傳 | Upload |
| `common.download` | 下载 | 下載 | Download |
| `common.search` | 搜索 | 搜尋 | Search |
| `common.filter` | 筛选 | 篩選 | Filter |
| `common.refresh` | 刷新 | 重新整理 | Refresh |
| `common.no.data` | 暂无数据 | 暫無資料 | No Data |
| `common.error.network` | 网络错误，请检查连接 | 網路錯誤，請檢查連線 | Network error, please check connection |
| `common.error.server` | 服务器错误，请稍后重试 | 伺服器錯誤，請稍後重試 | Server error, please try again later |
| `common.error.not.found` | 资源不存在 | 資源不存在 | Resource not found |
| `common.error.permission` | 无权限访问 | 無權限存取 | No permission to access |
| `common.error.login` | 请先登录 | 請先登入 | Please login first |

---

## 使用方法

### JavaScript

```javascript
// 获取翻译
const text = t('home.title'); // 返回当前语言的翻译

// 切换语言
setLocale('zh-CN'); // 切换到简体中文
setLocale('zh-TW'); // 切换到繁體中文
setLocale('en');    // 切换到English

// 应用翻译到页面
applyTranslations(); // 更新所有带有 data-i18n 属性的元素
```

### HTML

```html
<!-- 使用 data-i18n 属性 -->
<h1 data-i18n="home.title">CSCL Script Studio</h1>
<span data-i18n="common.loading">加载中...</span>
```

---

## 持久化

语言选择保存在 `localStorage` 中，键名为 `app_locale`。

首次访问时，系统会根据浏览器语言自动选择：
- `zh-TW` 或 `zh-HK` → `zh-TW`
- `zh-CN` 或其他中文变体 → `zh-CN`
- `en` 或其他 → `en`
- 默认 → `zh-CN`
