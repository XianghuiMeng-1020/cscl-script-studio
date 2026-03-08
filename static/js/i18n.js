// i18n Language Dictionary and Switcher
const I18N = {
    'zh-CN': {
        // ===== Home page =====
        'home.title': 'CSCL Script Studio',
        'home.subtitle': '协作学习活动编排工具',
        'home.hero.title': '将课程大纲转化为<br>结构化协作学习活动',
        'home.hero.subtitle': '简单易用的活动编排工具，帮助教师快速创建协作学习方案',
        'home.teacher.card': '登录为教师',
        'home.teacher.subtitle': '创建活动、调整流程、发布给班级',
        'home.teacher.action': '进入教师端',
        'home.student.card': '登录为学生',
        'home.student.subtitle': '查看当前活动、完成协作任务、提交反思',
        'home.student.action': '进入学生端',
        'home.demo': '快速体验 Demo',
        'home.tech.details': '了解更多技术细节',
        'home.demo.modal.title': 'Demo 课程大纲',
        'home.demo.modal.copy': '复制教学目标数据',
        'home.demo.modal.start': '以教师身份开始',
        'home.feature.pipeline': '多阶段生成',
        'home.feature.pipeline_desc': '规划 → 材料 → 审查 → 优化',
        'home.feature.rag': '文档检索',
        'home.feature.rag_desc': '基于课程文档的智能检索与引用',
        'home.feature.decisions': '调整记录',
        'home.feature.decisions_desc': '完整记录教师决策与活动修订历史',
        'home.feature.quality': '质量检查',
        'home.feature.quality_desc': '多维度质量评估与证据链接',

        // ===== Login page =====
        'login.title': '登录',
        'login.role.teacher': '教师',
        'login.role.student': '学生',
        'login.username': '用户名',
        'login.password': '密码',
        'login.sign_in': '登录',
        'login.quick_demo': '快速体验 Demo',
        'login.error.invalid': '用户名或密码错误，请重试',
        'login.error.required': '请输入用户名和密码',
        'login.back_home': '返回首页',
        'login.welcome': '你好，我是你的协作学习活动生成小助手！可以用我把课程大纲变成结构化的协作学习活动哦～',

        // Demo page
        'demo.mode.title': 'Demo 模式',
        'demo.mode.desc': '仅可浏览活动列表，无法创建或编辑。如需完整功能，请使用上方登录。',

        // ===== Teacher page =====
        // Sidebar
        'teacher.sidebar.dashboard': '工作台',
        'teacher.sidebar.scripts': '活动项目',
        'teacher.sidebar.spec': '教学目标检查',
        'teacher.sidebar.pipeline': '自动生成过程',
        'teacher.sidebar.documents': '课程文档',
        'teacher.sidebar.decisions': '教师调整记录',
        'teacher.sidebar.quality': '质量检查结果',
        'teacher.sidebar.publish': '发布与导出',
        'teacher.sidebar.settings': '设置',
        'teacher.sidebar.logout': '退出登录',

        // Language option labels (for selector)
        'lang.zh-CN': '简体中文',
        'lang.zh-TW': '繁體中文',
        'lang.en': 'English',

        // Dashboard
        'teacher.dashboard.title': '教师工作台',
        'teacher.dashboard.step_indicator': '你现在在第 {step}/4 步',
        'teacher.dashboard.step_before': '你现在在第 ',
        'teacher.dashboard.step_after': '/4 步',
        'teacher.dashboard.new_activity': '新建活动',
        'teacher.dashboard.current_status': '当前状态：',
        'teacher.dashboard.ready': '准备开始',
        'teacher.tutorial.title': '👋 欢迎使用教师工作台',
        'teacher.tutorial.intro': '我是你的协作学习活动生成小助手。按下面 4 步即可把课程大纲变成可用的活动方案：',
        'teacher.tutorial.step1': '1. 导入课程大纲 — 上传或粘贴大纲，系统会提取课程信息',
        'teacher.tutorial.step2': '2. 确认教学目标 — 填写学习目标、任务类型与预期产出',
        'teacher.tutorial.step3': '3. 生成活动流程 — 点击「开始生成」，系统自动生成活动方案',
        'teacher.tutorial.step4': '4. 审阅并发布 — 检查无误后发布给学生',
        'teacher.tutorial.dismiss': '不再显示',
        'teacher.dashboard.view_tech': '查看技术详情',
        'teacher.dashboard.stat.projects': '活动项目',
        'teacher.dashboard.stat.pipelines': '自动生成过程',
        'teacher.dashboard.stat.publish': '待发布活动',
        'teacher.dashboard.stat.quality': '质量检查结果',

        // 4-Step Process Cards
        'teacher.step1.title': '导入课程大纲',
        'teacher.step1.what': '这一步做什么：上传或粘贴课程大纲内容',
        'teacher.step1.why': '为什么要做：系统需要了解课程内容才能生成合适的活动方案',
        'teacher.step1.result': '完成后会得到：提取的课程信息（课程名、主题、目标等）',
        'teacher.step1.action': '开始导入',
        'teacher.step2.title': '确认教学目标',
        'teacher.step2.what': '这一步做什么：确认或补充学习目标、任务类型、预期产出',
        'teacher.step2.why': '为什么要做：明确的教学目标确保生成的活动符合你的教学需求',
        'teacher.step2.result': '完成后会得到：完整的教学目标检查结果',
        'teacher.step2.action': '确认目标',
        'teacher.step3.title': '生成活动流程',
        'teacher.step3.what': '这一步做什么：系统自动生成协作学习活动方案',
        'teacher.step3.why': '为什么要做：基于课程内容和教学目标，生成结构化的活动流程',
        'teacher.step3.result': '完成后会得到：完整的活动方案，包括场景、角色、任务等',
        'teacher.step3.action': '开始生成',
        'teacher.step4.title': '审阅并发布',
        'teacher.step4.what': '这一步做什么：查看生成的活动方案，确认无误后发布给学生',
        'teacher.step4.why': '为什么要做：确保活动质量符合预期，再让学生开始使用',
        'teacher.step4.result': '完成后会得到：已发布的活动，学生可以开始参与',
        'teacher.step4.action': '审阅发布',

        // Spec/Teaching Plan
        'teacher.spec.title': '教学目标设置',
        'teacher.spec.subtitle': '教学目标已就绪，可进行生成。',
        'teacher.spec.validate': '校验教学目标设置',
        'teacher.spec.ready': '教学目标已就绪，可进行生成。',
        'teacher.spec.validated': '教学目标校验成功',

        // Wizard
        'teacher.wizard.step1': '上传课程大纲',
        'teacher.wizard.step2': '教学目标设置',
        'teacher.wizard.step3': '运行生成流程',
        'teacher.wizard.step4': '审阅并发布',
        'teacher.wizard.upload': '上传课程大纲',
        'teacher.wizard.define': '确认教学目标',
        'teacher.wizard.run': '开始生成',
        'teacher.wizard.finalize': '审阅发布',
        'teacher.wizard.spec_why': '教学目标定义学习目标、任务类型与预期产出，便于生成协作活动方案。',
        'teacher.wizard.step1.title': '第 1 步：上传课程大纲',
        'teacher.wizard.step1.subtitle': '上传课程材料以便系统检索',
        'teacher.wizard.step1.why': '课程文档用于检索增强生成，使活动方案贴合你的课程内容。',
        'teacher.wizard.step1.drag': '将课程大纲文件拖放到此处，或点击浏览',
        'teacher.wizard.step1.browse': '浏览文件',
        'teacher.wizard.step1.paste': '或粘贴大纲文本：',
        'teacher.wizard.step1.paste_placeholder': '在此粘贴课程大纲内容...',
        'teacher.wizard.step2.title': '第 2 步：教学目标设置',
        'teacher.wizard.step2.subtitle': '填写必要信息以生成 CSCL 活动方案',
        'teacher.wizard.step3.title': '第 3 步：运行生成流程',
        'teacher.wizard.step3.subtitle': '通过多阶段流程生成 CSCL 活动方案',
        'teacher.wizard.step3.why': '流程包含 4 个阶段：规划器（结构）、材料（内容）、审查器（审查）、优化器（润色）。',
        'teacher.wizard.step4.title': '第 4 步：审阅并发布',
        'teacher.wizard.step4.subtitle': '查看生成的活动方案并发布给学生',
        'teacher.wizard.step4.why': '审阅确保活动质量，确认后再对学生可见。',
        'teacher.wizard.cancel': '取消',
        'teacher.wizard.continue': '继续',
        'teacher.wizard.back': '上一步',
        'teacher.wizard.done': '完成',

        // Form Labels
        'teacher.form.course': '课程名称 *',
        'teacher.form.course_placeholder': '例如：CS101',
        'teacher.form.topic': '主题 *',
        'teacher.form.topic_placeholder': '例如：算法公平性',
        'teacher.form.duration': '时长（分钟）*',
        'teacher.form.mode': '模式 *',
        'teacher.form.mode_sync': '同步',
        'teacher.form.mode_async': '异步',
        'teacher.form.class_size': '班级人数 *',
        'teacher.form.course_context': '课程背景 *',
        'teacher.form.course_context_placeholder': '描述课程设置、学习者画像和教学情境。',
        'teacher.form.objectives': '学习目标 *（每行一个）',
        'teacher.form.objectives_placeholder': '解释基本公平性指标\n比较准确性与公平性之间的权衡',
        'teacher.form.task_type': '任务类型 *',
        'teacher.form.task_type_help': '从配置中选择协作论证任务类型。',
        'teacher.form.expected_output': '预期产出 *（每行一个）',
        'teacher.form.expected_output_placeholder': '小组论证地图\n300字联合反思',
        'teacher.form.collaboration_form': '协作形式 *',
        'teacher.form.collaboration_group': '小组',
        'teacher.form.collaboration_pair': '双人',
        'teacher.form.collaboration_individual': '个人分享',
        'teacher.form.collaboration_whole_class': '全班',
        'teacher.form.task_requirements': '任务要求 *',
        'teacher.form.task_requirements_placeholder': '指定具体的协作和证据要求。',

        // Demo
        'teacher.demo.fill': '填充示例数据',

        // Documents
        'teacher.doc.upload': '上传文档',
        'teacher.doc.empty': '暂无课程文档',
        'teacher.doc.upload.first': '上传第一份文档',
        'teacher.doc.subtitle': '管理课程材料用于检索增强',

        // Decisions
        'teacher.decisions.title': '调整时间线',
        'teacher.decisions.subtitle': '追踪教师决策与活动修订',
        'teacher.decisions.empty': '暂无调整记录',
        'teacher.decisions.empty_desc': '创建和修改活动项目后，调整时间线将出现在此处。',

        // Publish
        'teacher.publish.title': '发布与导出',
        'teacher.publish.subtitle': '完成并发布你的 CSCL 活动',
        'teacher.publish.empty': '暂无待发布活动',
        'teacher.publish.empty_desc': '完成一个活动项目后即可发布。',
        'teacher.publish.view_projects': '查看活动项目',

        // Scripts
        'teacher.scripts.title': '活动项目',
        'teacher.scripts.subtitle': '管理你的 CSCL 活动方案',
        'teacher.scripts.create': '创建新项目',

        // Pipeline
        'teacher.pipeline.title': '生成流程',
        'teacher.pipeline.subtitle': '追踪生成进度',
        'teacher.pipeline.spec_hash': '教学目标版本',
        'teacher.pipeline.spec_hash_title': '本次教学目标版本指纹',
        'teacher.pipeline.spec_validated': '教学目标已校验',
        'teacher.pipeline.start': '开始生成',
        'teacher.pipeline.provider': '提供商：',
        'teacher.pipeline.model': '模型：',
        'teacher.pipeline.config_fp': '配置指纹：',
        'teacher.pipeline.stage.planner': '规划器',
        'teacher.pipeline.stage.material': '材料',
        'teacher.pipeline.stage.critic': '审查器',
        'teacher.pipeline.stage.refiner': '优化器',
        'teacher.pipeline.stage.pending': '等待中',
        'teacher.pipeline.stage.running': '运行中',
        'teacher.pipeline.stage.completed': '已完成',
        'teacher.pipeline.stage.failed': '失败',
        'teacher.pipeline.stage.input': '输入：',
        'teacher.pipeline.stage.output': '输出：',
        'teacher.pipeline.stage.waiting': '等待中...',
        'teacher.pipeline.error': '流程错误',
        'teacher.pipeline.run_detail': '流程运行详情',
        'teacher.pipeline.run_detail_subtitle': '查看流程执行详情',
        'teacher.pipeline.back_to_runs': '返回流程列表',

        // Quality
        'teacher.quality.title': '质量报告',
        'teacher.quality.subtitle': '基于证据的质量评估',
        'teacher.quality.select': '选择一个活动项目以查看质量报告',
        'teacher.quality.detail_subtitle': '六维质量评估',
        'teacher.quality.back': '返回',

        // Settings
        'teacher.settings.title': '设置',
        'teacher.settings.subtitle': '配置你的偏好设置',
        'teacher.settings.system': '系统设置',
        'teacher.settings.coming_soon': '设置功能即将上线。',
        'teacher.publish.share_title': '分享给学生',
        'teacher.publish.share_hint': '将下方链接或邀请码发给学生，学生打开链接后登录即可参与活动。',
        'teacher.publish.share_code': '邀请码',
        'teacher.publish.copy_code': '复制邀请码',
        'teacher.publish.student_link': '学生链接',
        'teacher.publish.copy_link': '复制链接',

        // Wizard Step 4 actions
        'teacher.wizard.view_quality': '查看质量报告',
        'teacher.wizard.export': '导出方案',
        'teacher.wizard.finalize_script': '确认方案',
        'teacher.wizard.publish_activity': '发布活动',
        'teacher.wizard.loading_preview': '正在加载方案预览...',

        // PDF errors
        'teacher.pdf.parse_failed_binary': '文档解析失败：检测到二进制内容，请重新上传或更换 PDF',
        'teacher.pdf.parse_failed_empty': '提取失败：未能从文档中提取文本，请重试或更换文件',
        'teacher.pdf.parse_failed_short': '提取失败：文本过短，请使用内容更完整的文件',
        'teacher.pdf.parse_failed_generic': '提取失败，请重试或更换文件',

        // User info
        'teacher.user.role': '教师',

        // ===== Student page =====
        'student.title': '学生工作台',
        'student.user.role': '学生',
        'student.tutorial.title': '👋 欢迎来到学生工作台',
        'student.tutorial.intro': '在这里你可以：查看当前协作学习活动、完成分配的任务、提交反思。如有任务请按页面提示完成。',
        'student.tutorial.dismiss': '不再显示',
        'student.current.activity': '当前活动',
        'student.current.task': '本次任务',
        'student.task.description': '你需要完成以下任务',
        'student.submit': '提交任务',
        'student.continue': '继续任务',
        'student.scoring': '评分标准摘要',
        'student.history': '历史记录',
        'student.collaboration': '协作建议',
        'student.collaboration.tip1': '积极倾听同伴的想法',
        'student.collaboration.tip2': '在他人贡献的基础上继续',
        'student.collaboration.tip3': '需要时提出澄清问题',
        'student.empty.title': '当前没有活动',
        'student.empty.reason': '原因：URL中未提供活动ID，或教师尚未发布活动。',
        'student.empty.next_step': '下一步：请联系你的教师创建并发布活动，或使用有效的活动ID访问。',
        'student.empty.no_task': '暂无任务',
        'student.empty.no_history': '你还没有完成任何活动。',
        'student.error.login': '需要登录',
        'student.error.login_desc': '请先登录以查看活动。',
        'student.error.forbidden': '访问被拒绝',
        'student.error.forbidden_desc': '当前角色无权限查看此活动。',
        'student.error.not_found': '未找到活动',
        'student.error.not_found_desc': '资源不存在或尚未创建。',
        'student.error.load_failed': '加载失败',
        'student.error.retry': '重试',
        'student.context.viewing': '你正在查看：',
        'student.context.hint': '（通过 ?script_id=xxx 查看特定活动）',
        'student.deadline': '截止时间：',
        'student.days_left': '剩余 {n} 天',
        'student.activity.untitled': '未命名活动',
        'student.activity.join_title': '加入协作活动',
        'student.activity.join_hint': '输入老师分享的邀请码，或打开分享链接自动填入。',
        'student.activity.join': '加入',
        'student.activity.enter_code': '请输入邀请码',
        'student.chat.title': '小组讨论',
        'student.chat.empty': '加入活动后即可与同组同学聊天',
        'student.chat.placeholder': '输入消息...',
        'student.chat.send': '发送',
        'student.scene.progress': '场景',
        'student.scene.purpose': '本场景目标',
        'student.scene.your_role': '你的角色',
        'student.scene.task': '任务',
        'student.scene.prev': '上一场景',
        'student.scene.next': '下一场景',
        'student.submission.your_work': '你的作答',
        'student.submission.save_draft': '保存草稿',
        'student.submission.submit': '提交',
        'student.submission.submitted': '已提交',
        'student.submission.saved': '草稿已保存',
        'student.error.join_failed': '加入失败',

        // ===== Common =====
        'common.loading': '加载中...',
        'common.loading_text': '正在加载...',
        'common.error': '错误',
        'common.success': '成功',
        'common.warning': '警告',
        'common.info': '信息',
        'common.confirm': '确认',
        'common.cancel': '取消',
        'common.save': '保存',
        'common.delete': '删除',
        'common.edit': '编辑',
        'common.close': '关闭',
        'common.logout': '退出',
        'common.back': '返回',
        'common.next': '下一步',
        'common.previous': '上一步',
        'common.submit': '提交',
        'common.upload': '上传',
        'common.download': '下载',
        'common.search': '搜索',
        'common.filter': '筛选',
        'common.refresh': '刷新',
        'common.no.data': '暂无数据',
        'common.processing': '处理中...',
        'common.error.network': '网络错误，请检查连接',
        'common.error.server': '服务器错误，请稍后重试',
        'common.error.not.found': '资源不存在',
        'common.error.permission': '无权限访问',
        'common.error.login': '请先登录',
        'common.why': '为什么要做：',
        'common.loading_task_types': '加载中...'
    },
    'zh-TW': {
        // ===== Home page =====
        'home.title': 'CSCL Script Studio',
        'home.subtitle': '協作學習活動編排工具',
        'home.hero.title': '將課程大綱轉化為<br>結構化協作學習活動',
        'home.hero.subtitle': '簡單易用的活動編排工具，幫助教師快速創建協作學習方案',
        'home.teacher.card': '登入為教師',
        'home.teacher.subtitle': '創建活動、調整流程、發布給班級',
        'home.teacher.action': '進入教師端',
        'home.student.card': '登入為學生',
        'home.student.subtitle': '查看當前活動、完成協作任務、提交反思',
        'home.student.action': '進入學生端',
        'home.demo': '快速體驗 Demo',
        'home.tech.details': '了解更多技術細節',
        'home.demo.modal.title': 'Demo 課程大綱',
        'home.demo.modal.copy': '複製教學目標數據',
        'home.demo.modal.start': '以教師身份開始',
        'home.feature.pipeline': '多階段生成',
        'home.feature.pipeline_desc': '規劃 → 材料 → 審查 → 優化',
        'home.feature.rag': '文件檢索',
        'home.feature.rag_desc': '基於課程文件的智慧檢索與引用',
        'home.feature.decisions': '調整記錄',
        'home.feature.decisions_desc': '完整記錄教師決策與活動修訂歷史',
        'home.feature.quality': '品質檢查',
        'home.feature.quality_desc': '多維度品質評估與證據連結',

        // ===== Login page =====
        'login.title': '登入',
        'login.role.teacher': '教師',
        'login.role.student': '學生',
        'login.username': '使用者名稱',
        'login.password': '密碼',
        'login.sign_in': '登入',
        'login.quick_demo': '快速體驗 Demo',
        'login.error.invalid': '使用者名稱或密碼錯誤，請重試',
        'login.error.required': '請輸入使用者名稱與密碼',
        'login.back_home': '返回首頁',
        'login.welcome': '你好，我是你的協作學習活動生成小助手！可以用我把課程大綱變成結構化的協作學習活動哦～',

        'demo.mode.title': 'Demo 模式',
        'demo.mode.desc': '僅可瀏覽活動列表，無法建立或編輯。如需完整功能，請使用上方登入。',

        // ===== Teacher page =====
        // Sidebar
        'teacher.sidebar.dashboard': '工作台',
        'teacher.sidebar.scripts': '活動項目',
        'teacher.sidebar.spec': '教學目標檢查',
        'teacher.sidebar.pipeline': '自動生成過程',
        'teacher.sidebar.documents': '課程文檔',
        'teacher.sidebar.decisions': '教師調整記錄',
        'teacher.sidebar.quality': '品質檢查結果',
        'teacher.sidebar.publish': '發布與匯出',
        'teacher.sidebar.settings': '設定',
        'teacher.sidebar.logout': '登出',

        // Dashboard
        'lang.zh-CN': '簡體中文',
        'lang.zh-TW': '繁體中文',
        'lang.en': 'English',

        'teacher.dashboard.title': '教師工作台',
        'teacher.dashboard.step_indicator': '你現在在第 {step}/4 步',
        'teacher.dashboard.step_before': '你現在在第 ',
        'teacher.dashboard.step_after': '/4 步',
        'teacher.dashboard.new_activity': '新建活動',
        'teacher.dashboard.current_status': '目前狀態：',
        'teacher.dashboard.ready': '準備開始',
        'teacher.tutorial.title': '👋 歡迎使用教師工作台',
        'teacher.tutorial.intro': '我是你的協作學習活動生成小助手。按下面 4 步即可把課程大綱變成可用的活動方案：',
        'teacher.tutorial.step1': '1. 匯入課程大綱 — 上傳或貼上大綱，系統會提取課程資訊',
        'teacher.tutorial.step2': '2. 確認教學目標 — 填寫學習目標、任務類型與預期產出',
        'teacher.tutorial.step3': '3. 生成活動流程 — 點擊「開始生成」，系統自動生成活動方案',
        'teacher.tutorial.step4': '4. 審閱並發布 — 檢查無誤後發布給學生',
        'teacher.tutorial.dismiss': '不再顯示',
        'teacher.dashboard.view_tech': '查看技術詳情',
        'teacher.dashboard.stat.projects': '活動項目',
        'teacher.dashboard.stat.pipelines': '自動生成過程',
        'teacher.dashboard.stat.publish': '待發布活動',
        'teacher.dashboard.stat.quality': '品質檢查結果',

        // 4-Step Process Cards
        'teacher.step1.title': '匯入課程大綱',
        'teacher.step1.what': '這一步做什麼：上傳或貼上課程大綱內容',
        'teacher.step1.why': '為什麼要做：系統需要了解課程內容才能生成合適的活動方案',
        'teacher.step1.result': '完成後會得到：提取的課程資訊（課程名、主題、目標等）',
        'teacher.step1.action': '開始匯入',
        'teacher.step2.title': '確認教學目標',
        'teacher.step2.what': '這一步做什麼：確認或補充學習目標、任務類型、預期產出',
        'teacher.step2.why': '為什麼要做：明確的教學目標確保生成的活動符合你的教學需求',
        'teacher.step2.result': '完成後會得到：完整的教學目標檢查結果',
        'teacher.step2.action': '確認目標',
        'teacher.step3.title': '生成活動流程',
        'teacher.step3.what': '這一步做什麼：系統自動生成協作學習活動方案',
        'teacher.step3.why': '為什麼要做：基於課程內容和教學目標，生成結構化的活動流程',
        'teacher.step3.result': '完成後會得到：完整的活動方案，包括場景、角色、任務等',
        'teacher.step3.action': '開始生成',
        'teacher.step4.title': '審閱並發布',
        'teacher.step4.what': '這一步做什麼：查看生成的活動方案，確認無誤後發布給學生',
        'teacher.step4.why': '為什麼要做：確保活動品質符合預期，再讓學生開始使用',
        'teacher.step4.result': '完成後會得到：已發布的活動，學生可以開始參與',
        'teacher.step4.action': '審閱發布',

        // Spec/Teaching Plan
        'teacher.spec.title': '教學目標設定',
        'teacher.spec.subtitle': '教學目標已就緒，可進行生成。',
        'teacher.spec.validate': '驗證教學目標設定',
        'teacher.spec.ready': '教學目標已就緒，可進行生成。',
        'teacher.spec.validated': '教學目標校驗成功',

        // Wizard
        'teacher.wizard.step1': '上傳課程大綱',
        'teacher.wizard.step2': '教學目標設定',
        'teacher.wizard.step3': '執行生成流程',
        'teacher.wizard.step4': '審閱並發布',
        'teacher.wizard.upload': '上傳課程大綱',
        'teacher.wizard.define': '確認教學目標',
        'teacher.wizard.run': '開始生成',
        'teacher.wizard.finalize': '審閱發布',
        'teacher.wizard.spec_why': '教學目標定義學習目標、任務類型與預期產出，便於生成協作活動方案。',
        'teacher.wizard.step1.title': '第 1 步：上傳課程大綱',
        'teacher.wizard.step1.subtitle': '上傳課程材料以便系統檢索',
        'teacher.wizard.step1.why': '課程文件用於檢索增強生成，使活動方案貼合你的課程內容。',
        'teacher.wizard.step1.drag': '將課程大綱檔案拖放到此處，或點擊瀏覽',
        'teacher.wizard.step1.browse': '瀏覽檔案',
        'teacher.wizard.step1.paste': '或貼上大綱文字：',
        'teacher.wizard.step1.paste_placeholder': '在此貼上課程大綱內容...',
        'teacher.wizard.step2.title': '第 2 步：教學目標設定',
        'teacher.wizard.step2.subtitle': '填寫必要資訊以生成 CSCL 活動方案',
        'teacher.wizard.step3.title': '第 3 步：執行生成流程',
        'teacher.wizard.step3.subtitle': '通過多階段流程生成 CSCL 活動方案',
        'teacher.wizard.step3.why': '流程包含 4 個階段：規劃器（結構）、材料（內容）、審查器（審查）、優化器（潤色）。',
        'teacher.wizard.step4.title': '第 4 步：審閱並發布',
        'teacher.wizard.step4.subtitle': '查看生成的活動方案並發布給學生',
        'teacher.wizard.step4.why': '審閱確保活動品質，確認後再對學生可見。',
        'teacher.wizard.cancel': '取消',
        'teacher.wizard.continue': '繼續',
        'teacher.wizard.back': '上一步',
        'teacher.wizard.done': '完成',

        // Form Labels
        'teacher.form.course': '課程名稱 *',
        'teacher.form.course_placeholder': '例如：CS101',
        'teacher.form.topic': '主題 *',
        'teacher.form.topic_placeholder': '例如：演算法公平性',
        'teacher.form.duration': '時長（分鐘）*',
        'teacher.form.mode': '模式 *',
        'teacher.form.mode_sync': '同步',
        'teacher.form.mode_async': '非同步',
        'teacher.form.class_size': '班級人數 *',
        'teacher.form.course_context': '課程背景 *',
        'teacher.form.course_context_placeholder': '描述課程設置、學習者畫像和教學情境。',
        'teacher.form.objectives': '學習目標 *（每行一個）',
        'teacher.form.objectives_placeholder': '解釋基本公平性指標\n比較準確性與公平性之間的權衡',
        'teacher.form.task_type': '任務類型 *',
        'teacher.form.task_type_help': '從配置中選擇協作論證任務類型。',
        'teacher.form.expected_output': '預期產出 *（每行一個）',
        'teacher.form.expected_output_placeholder': '小組論證地圖\n300字聯合反思',
        'teacher.form.collaboration_form': '協作形式 *',
        'teacher.form.collaboration_group': '小組',
        'teacher.form.collaboration_pair': '雙人',
        'teacher.form.collaboration_individual': '個人分享',
        'teacher.form.collaboration_whole_class': '全班',
        'teacher.form.task_requirements': '任務要求 *',
        'teacher.form.task_requirements_placeholder': '指定具體的協作和證據要求。',

        // Demo
        'teacher.demo.fill': '填充示例數據',

        // Documents
        'teacher.doc.upload': '上傳文件',
        'teacher.doc.empty': '暫無課程文件',
        'teacher.doc.upload.first': '上傳第一份文件',
        'teacher.doc.subtitle': '管理課程材料用於檢索增強',

        // Decisions
        'teacher.decisions.title': '調整時間線',
        'teacher.decisions.subtitle': '追蹤教師決策與活動修訂',
        'teacher.decisions.empty': '暫無調整記錄',
        'teacher.decisions.empty_desc': '建立和修改活動項目後，調整時間線將出現在此處。',

        // Publish
        'teacher.publish.title': '發布與匯出',
        'teacher.publish.subtitle': '完成並發布你的 CSCL 活動',
        'teacher.publish.empty': '暫無待發布活動',
        'teacher.publish.empty_desc': '完成一個活動項目後即可發布。',
        'teacher.publish.view_projects': '查看活動項目',

        // Scripts
        'teacher.scripts.title': '活動項目',
        'teacher.scripts.subtitle': '管理你的 CSCL 活動方案',
        'teacher.scripts.create': '建立新項目',

        // Pipeline
        'teacher.pipeline.title': '生成流程',
        'teacher.pipeline.subtitle': '追蹤生成進度',
        'teacher.pipeline.spec_hash': '教學目標版本',
        'teacher.pipeline.spec_hash_title': '本次教學目標版本指紋',
        'teacher.pipeline.spec_validated': '教學目標已校驗',
        'teacher.pipeline.start': '開始生成',
        'teacher.pipeline.provider': '提供商：',
        'teacher.pipeline.model': '模型：',
        'teacher.pipeline.config_fp': '配置指紋：',
        'teacher.pipeline.stage.planner': '規劃器',
        'teacher.pipeline.stage.material': '材料',
        'teacher.pipeline.stage.critic': '審查器',
        'teacher.pipeline.stage.refiner': '優化器',
        'teacher.pipeline.stage.pending': '等待中',
        'teacher.pipeline.stage.running': '執行中',
        'teacher.pipeline.stage.completed': '已完成',
        'teacher.pipeline.stage.failed': '失敗',
        'teacher.pipeline.stage.input': '輸入：',
        'teacher.pipeline.stage.output': '輸出：',
        'teacher.pipeline.stage.waiting': '等待中...',
        'teacher.pipeline.error': '流程錯誤',
        'teacher.pipeline.run_detail': '流程執行詳情',
        'teacher.pipeline.run_detail_subtitle': '查看流程執行詳情',
        'teacher.pipeline.back_to_runs': '返回流程列表',

        // Quality
        'teacher.quality.title': '品質報告',
        'teacher.quality.subtitle': '基於證據的品質評估',
        'teacher.quality.select': '選擇一個活動項目以查看品質報告',
        'teacher.quality.detail_subtitle': '六維品質評估',
        'teacher.quality.back': '返回',

        // Settings
        'teacher.settings.title': '設定',
        'teacher.settings.subtitle': '配置你的偏好設定',
        'teacher.settings.system': '系統設定',
        'teacher.settings.coming_soon': '設定功能即將上線。',
        'teacher.publish.share_title': '分享給學生',
        'teacher.publish.share_hint': '將下方連結或邀請碼發給學生，學生打開連結後登入即可參與活動。',
        'teacher.publish.share_code': '邀請碼',
        'teacher.publish.copy_code': '複製邀請碼',
        'teacher.publish.student_link': '學生連結',
        'teacher.publish.copy_link': '複製連結',

        // Wizard Step 4 actions
        'teacher.wizard.view_quality': '查看品質報告',
        'teacher.wizard.export': '匯出方案',
        'teacher.wizard.finalize_script': '確認方案',
        'teacher.wizard.publish_activity': '發布活動',
        'teacher.wizard.loading_preview': '正在載入方案預覽...',

        // PDF errors
        'teacher.pdf.parse_failed_binary': '文件解析失敗：偵測到二進位內容，請重新上傳或更換 PDF',
        'teacher.pdf.parse_failed_empty': '提取失敗：未能從文件提取文字，請重試或更換文件',
        'teacher.pdf.parse_failed_short': '提取失敗：文字過短，請使用內容更完整的文件',
        'teacher.pdf.parse_failed_generic': '提取失敗，請重試或更換文件',

        // User info
        'teacher.user.role': '教師',

        // ===== Student page =====
        'student.title': '學生工作台',
        'student.user.role': '學生',
        'student.tutorial.title': '👋 歡迎來到學生工作台',
        'student.tutorial.intro': '在這裡你可以：查看當前協作學習活動、完成分配的任務、提交反思。如有任務請按頁面提示完成。',
        'student.tutorial.dismiss': '不再顯示',
        'student.current.activity': '當前活動',
        'student.current.task': '本次任務',
        'student.task.description': '你需要完成以下任務',
        'student.submit': '提交任務',
        'student.continue': '繼續任務',
        'student.scoring': '評分標準摘要',
        'student.history': '歷史記錄',
        'student.collaboration': '協作建議',
        'student.collaboration.tip1': '積極傾聽同伴的想法',
        'student.collaboration.tip2': '在他人貢獻的基礎上繼續',
        'student.collaboration.tip3': '需要時提出澄清問題',
        'student.empty.title': '目前沒有活動',
        'student.empty.reason': '原因：網址中未提供活動ID，或教師尚未發布活動。',
        'student.empty.next_step': '下一步：請聯繫你的教師創建並發布活動，或使用有效的活動ID存取。',
        'student.empty.no_task': '暫無任務',
        'student.empty.no_history': '你還沒有完成任何活動。',
        'student.error.login': '需要登入',
        'student.error.login_desc': '請先登入以查看活動。',
        'student.error.forbidden': '存取被拒絕',
        'student.error.forbidden_desc': '目前角色無權限查看此活動。',
        'student.error.not_found': '未找到活動',
        'student.error.not_found_desc': '資源不存在或尚未建立。',
        'student.error.load_failed': '載入失敗',
        'student.error.retry': '重試',
        'student.context.viewing': '你正在查看：',
        'student.context.hint': '（透過 ?script_id=xxx 查看特定活動）',
        'student.deadline': '截止時間：',
        'student.days_left': '剩餘 {n} 天',
        'student.activity.untitled': '未命名活動',
        'student.activity.join_title': '加入協作活動',
        'student.activity.join_hint': '輸入老師分享的邀請碼，或打開分享連結自動填入。',
        'student.activity.join': '加入',
        'student.activity.enter_code': '請輸入邀請碼',
        'student.chat.title': '小組討論',
        'student.chat.empty': '加入活動後即可與同組同學聊天',
        'student.chat.placeholder': '輸入訊息...',
        'student.chat.send': '發送',
        'student.scene.progress': '場景',
        'student.scene.purpose': '本場景目標',
        'student.scene.your_role': '你的角色',
        'student.scene.task': '任務',
        'student.scene.prev': '上一場景',
        'student.scene.next': '下一場景',
        'student.submission.your_work': '你的作答',
        'student.submission.save_draft': '儲存草稿',
        'student.submission.submit': '提交',
        'student.submission.submitted': '已提交',
        'student.submission.saved': '草稿已儲存',
        'student.error.join_failed': '加入失敗',

        // ===== Common =====
        'common.loading': '載入中...',
        'common.loading_text': '正在載入...',
        'common.error': '錯誤',
        'common.success': '成功',
        'common.warning': '警告',
        'common.info': '資訊',
        'common.confirm': '確認',
        'common.cancel': '取消',
        'common.save': '儲存',
        'common.delete': '刪除',
        'common.edit': '編輯',
        'common.close': '關閉',
        'common.logout': '登出',
        'common.back': '返回',
        'common.next': '下一步',
        'common.previous': '上一步',
        'common.submit': '提交',
        'common.upload': '上傳',
        'common.download': '下載',
        'common.search': '搜尋',
        'common.filter': '篩選',
        'common.refresh': '重新整理',
        'common.no.data': '暫無資料',
        'common.processing': '處理中...',
        'common.error.network': '網路錯誤，請檢查連線',
        'common.error.server': '伺服器錯誤，請稍後重試',
        'common.error.not.found': '資源不存在',
        'common.error.permission': '無權限存取',
        'common.error.login': '請先登入',
        'common.why': '為什麼要做：',
        'common.loading_task_types': '載入中...'
    },
    'en': {
        // ===== Home page =====
        'home.title': 'CSCL Script Studio',
        'home.subtitle': 'Collaborative Learning Activity Generator',
        'home.hero.title': 'Transform Course Syllabi<br>into Structured Collaborative Learning Activities',
        'home.hero.subtitle': 'An easy-to-use activity orchestration tool that helps teachers quickly create collaborative learning plans',
        'home.teacher.card': 'Login as Teacher',
        'home.teacher.subtitle': 'Create activities, adjust workflows, publish to class',
        'home.teacher.action': 'Enter Teacher Portal',
        'home.student.card': 'Login as Student',
        'home.student.subtitle': 'View current activities, complete collaborative tasks, submit reflections',
        'home.student.action': 'Enter Student Portal',
        'home.demo': 'Quick Demo',
        'home.tech.details': 'Learn More Technical Details',
        'home.demo.modal.title': 'Demo Syllabus',
        'home.demo.modal.copy': 'Copy Teaching Plan Data',
        'home.demo.modal.start': 'Start as Instructor',
        'home.feature.pipeline': 'Multi-stage Generation',
        'home.feature.pipeline_desc': 'Planner → Material → Critic → Refiner',
        'home.feature.rag': 'Document Retrieval',
        'home.feature.rag_desc': 'Intelligent retrieval based on course documents',
        'home.feature.decisions': 'Decision Tracking',
        'home.feature.decisions_desc': 'Complete record of teacher decisions and revisions',
        'home.feature.quality': 'Quality Check',
        'home.feature.quality_desc': 'Multi-dimensional quality assessment with evidence',

        // ===== Login page =====
        'login.title': 'Sign In',
        'login.role.teacher': 'Teacher',
        'login.role.student': 'Student',
        'login.username': 'Username',
        'login.password': 'Password',
        'login.sign_in': 'Sign In',
        'login.quick_demo': 'Quick Demo',
        'login.error.invalid': 'Invalid username or password. Please try again.',
        'login.error.required': 'Please enter username and password.',
        'login.back_home': 'Back to Home',
        'login.welcome': "Hi, I'm your group activity generation assistant! Use me to turn course syllabi into structured collaborative learning activities.",

        'demo.mode.title': 'Demo mode',
        'demo.mode.desc': 'You can only browse the activity list; creating or editing is disabled. Log in above for full features.',

        // ===== Teacher page =====
        // Sidebar
        'teacher.sidebar.dashboard': 'Dashboard',
        'teacher.sidebar.scripts': 'Activity Projects',
        'teacher.sidebar.spec': 'Teaching Plan Check',
        'teacher.sidebar.pipeline': 'Generation Pipeline',
        'teacher.sidebar.documents': 'Course Documents',
        'teacher.sidebar.decisions': 'Decision Records',
        'teacher.sidebar.quality': 'Quality Reports',
        'teacher.sidebar.publish': 'Publish & Export',
        'teacher.sidebar.settings': 'Settings',
        'teacher.sidebar.logout': 'Sign Out',

        // Dashboard
        'lang.zh-CN': 'Simplified Chinese',
        'lang.zh-TW': 'Traditional Chinese',
        'lang.en': 'English',

        'teacher.dashboard.title': 'Teacher Dashboard',
        'teacher.dashboard.step_indicator': 'You are on step {step}/4',
        'teacher.dashboard.step_before': 'You are on step ',
        'teacher.dashboard.step_after': '/4',
        'teacher.dashboard.new_activity': 'New Activity',
        'teacher.dashboard.current_status': 'Current Status:',
        'teacher.dashboard.ready': 'Ready to Start',
        'teacher.tutorial.title': '👋 Welcome to the Teacher Dashboard',
        'teacher.tutorial.intro': "I'm your collaborative learning activity assistant. Follow these 4 steps to turn your syllabus into a ready-to-use activity plan:",
        'teacher.tutorial.step1': '1. Import syllabus — Upload or paste your outline; we extract course info',
        'teacher.tutorial.step2': '2. Confirm objectives — Set learning goals, task type, and expected outputs',
        'teacher.tutorial.step3': '3. Generate activity — Click "Start generation" to create the plan',
        'teacher.tutorial.step4': '4. Review & publish — Check the plan and publish to students',
        'teacher.tutorial.dismiss': "Don't show again",
        'teacher.dashboard.view_tech': 'View Technical Details',
        'teacher.dashboard.stat.projects': 'Activity Projects',
        'teacher.dashboard.stat.pipelines': 'Pipeline Runs',
        'teacher.dashboard.stat.publish': 'Ready to Publish',
        'teacher.dashboard.stat.quality': 'Quality Reports',

        // 4-Step Process Cards
        'teacher.step1.title': 'Import Syllabus',
        'teacher.step1.what': 'What to do: Upload or paste your course syllabus',
        'teacher.step1.why': 'Why: The system needs course content to generate suitable activities',
        'teacher.step1.result': 'Result: Extracted course info (name, topic, objectives, etc.)',
        'teacher.step1.action': 'Start Import',
        'teacher.step2.title': 'Confirm Objectives',
        'teacher.step2.what': 'What to do: Confirm or supplement learning objectives, task types, expected outputs',
        'teacher.step2.why': 'Why: Clear objectives ensure generated activities match your teaching needs',
        'teacher.step2.result': 'Result: Complete teaching plan validation',
        'teacher.step2.action': 'Confirm Objectives',
        'teacher.step3.title': 'Generate Activity',
        'teacher.step3.what': 'What to do: System automatically generates collaborative learning activities',
        'teacher.step3.why': 'Why: Generate structured activity workflow based on content and objectives',
        'teacher.step3.result': 'Result: Complete activity plan with scenarios, roles, tasks, etc.',
        'teacher.step3.action': 'Start Generation',
        'teacher.step4.title': 'Review & Publish',
        'teacher.step4.what': 'What to do: Review the generated plan and publish to students',
        'teacher.step4.why': 'Why: Ensure activity quality meets expectations before student access',
        'teacher.step4.result': 'Result: Published activity, students can begin participating',
        'teacher.step4.action': 'Review & Publish',

        // Spec/Teaching Plan
        'teacher.spec.title': 'Teaching Plan Settings',
        'teacher.spec.subtitle': 'Teaching plan is complete and ready for generation.',
        'teacher.spec.validate': 'Validate Teaching Plan',
        'teacher.spec.ready': 'Teaching plan is complete and ready for pipeline generation.',
        'teacher.spec.validated': 'Teaching plan validated successfully',

        // Wizard
        'teacher.wizard.step1': 'Upload Syllabus',
        'teacher.wizard.step2': 'Teaching Plan Settings',
        'teacher.wizard.step3': 'Run Pipeline',
        'teacher.wizard.step4': 'Finalize & Publish',
        'teacher.wizard.upload': 'Upload Syllabus',
        'teacher.wizard.define': 'Confirm Objectives',
        'teacher.wizard.run': 'Start Generation',
        'teacher.wizard.finalize': 'Review & Publish',
        'teacher.wizard.spec_why': 'Teaching plan defines learning objectives, task type, and expected outcomes for the collaborative activity.',
        'teacher.wizard.step1.title': 'Step 1: Upload Course Syllabus',
        'teacher.wizard.step1.subtitle': 'Upload your course materials to enable RAG retrieval',
        'teacher.wizard.step1.why': 'Course documents are used for retrieval-augmented generation to ground script generation in your course content.',
        'teacher.wizard.step1.drag': 'Drag and drop your syllabus file here, or click to browse',
        'teacher.wizard.step1.browse': 'Browse Files',
        'teacher.wizard.step1.paste': 'Or paste syllabus text:',
        'teacher.wizard.step1.paste_placeholder': 'Paste your course syllabus content here...',
        'teacher.wizard.step2.title': 'Step 2: Teaching Plan Settings',
        'teacher.wizard.step2.subtitle': 'Fill in the required fields to generate your CSCL script',
        'teacher.wizard.step3.title': 'Step 3: Run Generation Pipeline',
        'teacher.wizard.step3.subtitle': 'Generate your CSCL activity script through multi-stage pipeline',
        'teacher.wizard.step3.why': 'The pipeline runs through 4 stages: Planner (structure), Material (content), Critic (review), and Refiner (polish).',
        'teacher.wizard.step4.title': 'Step 4: Review & Publish',
        'teacher.wizard.step4.subtitle': 'Review the generated script and publish it for students',
        'teacher.wizard.step4.why': 'Review ensures quality before making the activity visible to students.',
        'teacher.wizard.cancel': 'Cancel',
        'teacher.wizard.continue': 'Continue',
        'teacher.wizard.back': 'Back',
        'teacher.wizard.done': 'Done',

        // Form Labels
        'teacher.form.course': 'Course Name *',
        'teacher.form.course_placeholder': 'e.g., CS101',
        'teacher.form.topic': 'Topic *',
        'teacher.form.topic_placeholder': 'e.g., Algorithmic Fairness',
        'teacher.form.duration': 'Duration (minutes) *',
        'teacher.form.mode': 'Mode *',
        'teacher.form.mode_sync': 'Synchronous',
        'teacher.form.mode_async': 'Asynchronous',
        'teacher.form.class_size': 'Class Size *',
        'teacher.form.course_context': 'Course Context *',
        'teacher.form.course_context_placeholder': 'Describe course setting, learner profile, and instructional context.',
        'teacher.form.objectives': 'Learning Objectives * (one per line)',
        'teacher.form.objectives_placeholder': 'Explain basic fairness metrics\nCompare trade-offs between accuracy and fairness',
        'teacher.form.task_type': 'Task Type *',
        'teacher.form.task_type_help': 'Collaborative argumentation task types from config.',
        'teacher.form.expected_output': 'Expected Output * (one per line)',
        'teacher.form.expected_output_placeholder': 'Group argument map\n300-word joint reflection',
        'teacher.form.collaboration_form': 'Collaboration Form *',
        'teacher.form.collaboration_group': 'Group',
        'teacher.form.collaboration_pair': 'Pair',
        'teacher.form.collaboration_individual': 'Individual with sharing',
        'teacher.form.collaboration_whole_class': 'Whole class',
        'teacher.form.task_requirements': 'Task Requirements *',
        'teacher.form.task_requirements_placeholder': 'Specify concrete collaboration and evidence requirements.',

        // Demo
        'teacher.demo.fill': 'Fill Demo Data',

        // Documents
        'teacher.doc.upload': 'Upload Document',
        'teacher.doc.empty': 'No Course Documents',
        'teacher.doc.upload.first': 'Upload First Document',
        'teacher.doc.subtitle': 'Manage course materials for RAG retrieval',

        // Decisions
        'teacher.decisions.title': 'Decision Timeline',
        'teacher.decisions.subtitle': 'Track teacher decisions and script revisions',
        'teacher.decisions.empty': 'No Decisions Yet',
        'teacher.decisions.empty_desc': 'Decision timeline will appear here after you create and modify script projects.',

        // Publish
        'teacher.publish.title': 'Publish & Export',
        'teacher.publish.subtitle': 'Finalize and publish your CSCL activities',
        'teacher.publish.empty': 'No Scripts Ready to Publish',
        'teacher.publish.empty_desc': 'Finalize a script project to make it available for publishing.',
        'teacher.publish.view_projects': 'View Script Projects',

        // Scripts
        'teacher.scripts.title': 'Activity Projects',
        'teacher.scripts.subtitle': 'Manage your CSCL activity scripts',
        'teacher.scripts.create': 'Create New Project',

        // Pipeline
        'teacher.pipeline.title': 'Pipeline Runs',
        'teacher.pipeline.subtitle': 'Track generation progress',
        'teacher.pipeline.spec_hash': 'Teaching Plan Version',
        'teacher.pipeline.spec_hash_title': 'Teaching plan version fingerprint',
        'teacher.pipeline.spec_validated': 'Teaching plan validated',
        'teacher.pipeline.start': 'Start Generation',
        'teacher.pipeline.provider': 'Provider:',
        'teacher.pipeline.model': 'Model:',
        'teacher.pipeline.config_fp': 'Config Fingerprint:',
        'teacher.pipeline.stage.planner': 'Planner',
        'teacher.pipeline.stage.material': 'Material',
        'teacher.pipeline.stage.critic': 'Critic',
        'teacher.pipeline.stage.refiner': 'Refiner',
        'teacher.pipeline.stage.pending': 'Pending',
        'teacher.pipeline.stage.running': 'Running',
        'teacher.pipeline.stage.completed': 'Completed',
        'teacher.pipeline.stage.failed': 'Failed',
        'teacher.pipeline.stage.input': 'Input:',
        'teacher.pipeline.stage.output': 'Output:',
        'teacher.pipeline.stage.waiting': 'Waiting...',
        'teacher.pipeline.error': 'Pipeline error',
        'teacher.pipeline.run_detail': 'Pipeline Run Details',
        'teacher.pipeline.run_detail_subtitle': 'Detailed view of pipeline execution',
        'teacher.pipeline.back_to_runs': 'Back to Runs',

        // Quality
        'teacher.quality.title': 'Quality Report',
        'teacher.quality.subtitle': 'Evidence-grounded quality assessment',
        'teacher.quality.select': 'Select a script project to view quality report',
        'teacher.quality.detail_subtitle': 'Six-dimensional quality assessment',
        'teacher.quality.back': 'Back',

        // Settings
        'teacher.settings.title': 'Settings',
        'teacher.settings.subtitle': 'Configure your preferences',
        'teacher.settings.system': 'System Settings',
        'teacher.settings.coming_soon': 'Settings configuration coming soon.',
        'teacher.publish.share_title': 'Share with students',
        'teacher.publish.share_hint': 'Share the link or invite code below. Students can open the link and sign in to join the activity.',
        'teacher.publish.share_code': 'Invite code',
        'teacher.publish.copy_code': 'Copy code',
        'teacher.publish.student_link': 'Student link',
        'teacher.publish.copy_link': 'Copy link',

        // Wizard Step 4 actions
        'teacher.wizard.view_quality': 'View Quality Report',
        'teacher.wizard.export': 'Export Script',
        'teacher.wizard.finalize_script': 'Finalize Script',
        'teacher.wizard.publish_activity': 'Publish Activity',
        'teacher.wizard.loading_preview': 'Loading script preview...',

        // PDF errors
        'teacher.pdf.parse_failed_binary': 'Parsing failed: binary PDF content detected. Please re-upload or use another file.',
        'teacher.pdf.parse_failed_empty': 'Extraction failed: no text could be extracted. Please try again or use another file.',
        'teacher.pdf.parse_failed_short': 'Extraction failed: text too short. Please use a file with more content.',
        'teacher.pdf.parse_failed_generic': 'Extraction failed. Please try again or use another file.',

        // User info
        'teacher.user.role': 'Teacher',

        // ===== Student page =====
        'student.title': 'Student Dashboard',
        'student.user.role': 'Student',
        'student.tutorial.title': '👋 Welcome to the Student Dashboard',
        'student.tutorial.intro': 'Here you can: view the current collaborative learning activity, complete assigned tasks, and submit reflections. Follow the on-screen prompts for any tasks.',
        'student.tutorial.dismiss': "Don't show again",
        'student.current.activity': 'Current Activity',
        'student.current.task': 'Current Task',
        'student.task.description': 'You need to complete the following tasks',
        'student.submit': 'Submit Task',
        'student.continue': 'Continue Task',
        'student.scoring': 'Scoring Criteria Summary',
        'student.history': 'History Record',
        'student.collaboration': 'Collaboration Suggestions',
        'student.collaboration.tip1': 'Actively listen to your peers\' ideas',
        'student.collaboration.tip2': 'Build on others\' contributions',
        'student.collaboration.tip3': 'Ask clarifying questions when needed',
        'student.empty.title': 'No current activity',
        'student.empty.reason': 'No activity ID was provided in the URL, or your instructor has not published an activity yet.',
        'student.empty.next_step': 'Next step: Ask your instructor to create and publish an activity, or use a valid activity link.',
        'student.empty.no_task': 'No tasks yet',
        'student.empty.no_history': 'You have not completed any activities yet.',
        'student.error.login': 'Login required',
        'student.error.login_desc': 'Please log in to view activities.',
        'student.error.forbidden': 'Access denied',
        'student.error.forbidden_desc': 'Your role does not have permission to view this activity.',
        'student.error.not_found': 'Activity not found',
        'student.error.not_found_desc': 'The resource does not exist or has not been created yet.',
        'student.error.load_failed': 'Failed to load',
        'student.error.retry': 'Retry',
        'student.context.viewing': 'You are viewing:',
        'student.context.hint': '(Access with ?script_id=xxx to view specific activity)',
        'student.deadline': 'Deadline:',
        'student.days_left': '{n} days left',
        'student.activity.untitled': 'Untitled activity',
        'student.activity.join_title': 'Join collaborative activity',
        'student.activity.join_hint': 'Enter the invite code shared by your teacher, or open the share link to auto-fill.',
        'student.activity.join': 'Join',
        'student.activity.enter_code': 'Enter invite code',
        'student.chat.title': 'Group chat',
        'student.chat.empty': 'Join an activity to chat with your group',
        'student.chat.placeholder': 'Type a message...',
        'student.chat.send': 'Send',
        'student.scene.progress': 'Scene',
        'student.scene.purpose': 'Scene goal',
        'student.scene.your_role': 'Your role',
        'student.scene.task': 'Task',
        'student.scene.prev': 'Previous scene',
        'student.scene.next': 'Next scene',
        'student.submission.your_work': 'Your response',
        'student.submission.save_draft': 'Save draft',
        'student.submission.submit': 'Submit',
        'student.submission.submitted': 'Submitted',
        'student.submission.saved': 'Draft saved',
        'student.error.join_failed': 'Join failed',

        // ===== Common =====
        'common.loading': 'Loading...',
        'common.loading_text': 'Loading...',
        'common.error': 'Error',
        'common.success': 'Success',
        'common.warning': 'Warning',
        'common.info': 'Info',
        'common.confirm': 'Confirm',
        'common.cancel': 'Cancel',
        'common.save': 'Save',
        'common.delete': 'Delete',
        'common.edit': 'Edit',
        'common.close': 'Close',
        'common.logout': 'Logout',
        'common.back': 'Back',
        'common.next': 'Next',
        'common.previous': 'Previous',
        'common.submit': 'Submit',
        'common.upload': 'Upload',
        'common.download': 'Download',
        'common.search': 'Search',
        'common.filter': 'Filter',
        'common.refresh': 'Refresh',
        'common.no.data': 'No Data',
        'common.processing': 'Processing...',
        'common.error.network': 'Network error, please check connection',
        'common.error.server': 'Server error, please try again later',
        'common.error.not.found': 'Resource not found',
        'common.error.permission': 'No permission to access',
        'common.error.login': 'Please login first',
        'common.why': 'Why:',
        'common.loading_task_types': 'Loading...'
    }
};

// Get current locale from localStorage or browser
function getCurrentLocale() {
    const saved = localStorage.getItem('app_locale');
    if (saved && I18N[saved]) {
        return saved;
    }
    
    const browserLang = navigator.language || navigator.userLanguage;
    if (browserLang.startsWith('zh')) {
        return browserLang.includes('TW') || browserLang.includes('HK') ? 'zh-TW' : 'zh-CN';
    }
    if (browserLang.startsWith('en')) {
        return 'en';
    }
    
    return 'zh-CN';
}

// Set locale and persist
function setLocale(locale) {
    if (!I18N[locale]) {
        console.warn(`Locale ${locale} not supported, using zh-CN`);
        locale = 'zh-CN';
    }
    localStorage.setItem('app_locale', locale);
    currentLocale = locale;
    updatePageLanguage();
    applyLocaleToPage();
}

// Apply current locale to all data-i18n* nodes
function applyLocaleToPage() {
    if (typeof document === 'undefined') return;
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = t(key);
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            el.placeholder = val;
        } else {
            el.innerHTML = val;
        }
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        el.title = t(el.getAttribute('data-i18n-title'));
    });
    document.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
        el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria-label')));
    });
    // Sync language selector value and update option labels so no residual language
    document.querySelectorAll('#languageSelect, [data-language-select]').forEach(sel => {
        sel.value = currentLocale;
        [].slice.call(sel.options || []).forEach(function(opt) {
            var labelKey = 'lang.' + opt.value;
            if (I18N[currentLocale] && I18N[currentLocale][labelKey] !== undefined) {
                opt.textContent = I18N[currentLocale][labelKey];
            }
        });
    });
    document.dispatchEvent(new CustomEvent('localeChange'));
}

// Current locale
let currentLocale = getCurrentLocale();

// Translation function
function t(key, defaultValue = '') {
    const translation = I18N[currentLocale]?.[key];
    if (translation !== undefined) {
        return translation;
    }
    const fallback = I18N['zh-CN']?.[key];
    return fallback !== undefined ? fallback : defaultValue || key;
}

// Update page language attribute
function updatePageLanguage() {
    document.documentElement.lang = currentLocale;
}

// Initialize on load
if (typeof document !== 'undefined') {
    updatePageLanguage();
    document.addEventListener('DOMContentLoaded', function() {
        applyLocaleToPage();
    });
}
